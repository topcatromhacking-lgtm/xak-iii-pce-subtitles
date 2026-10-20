#!/usr/bin/env python3
"""Geargrafx 1.8.4 save-only sprite test v2, correcting VBlank SAT-DMA overwrite.

Private source game data and state files are required as input. This makes an
experimental slot-3 state, NOT a disc patch or a complete subtitle engine.
"""
import argparse
import json
import struct
from pathlib import Path

from make_subtitle_savestate_probe import (
    VRAM_OFFSET, SAT_OFFSET, PALETTE_OFFSET, SOURCE_SHA256,
    sprite_planes, sha, MAGIC,
)

TEXT = "ENGLISH SUBTITLE"
PATTERNS = (504, 505, 506, 507, 30, 31, 43, 56)
EXPECTED_SHA256 = "0abf78b8bbc7f338b29f51e47d4cfc769d2465a985fc9e7953af9f4ef9defc05"
REGISTERS = VRAM_OFFSET + 65536 + 4


def create(source):
    if sha(source) != SOURCE_SHA256:
        raise ValueError("Unknown input checkpoint; refusing to patch")
    tail = len(source) - 200
    if struct.unpack_from("<III", source, tail) != (MAGIC, 44, len(source)):
        raise ValueError("Not a Geargrafx v44 state")
    if struct.unpack_from("<IHH", source, tail+156) != (256*240*4, 256, 240):
        raise ValueError("Unexpected display geometry")
    regs = struct.unpack_from("<20H", source, REGISTERS)
    if (regs[5], regs[9], regs[8], regs[15], regs[19]) != (
        0x00CC, 0x0050, 0x01FF, 0x0010, 0x0C00
    ):
        raise ValueError("VDC registers disagree with expected original")
    if struct.unpack_from("<H", source, PALETTE_OFFSET+511*2)[0] != 0x1FF:
        raise ValueError("Expected white sprite color missing")
    shadow = VRAM_OFFSET + regs[19]*2
    if any(source[SAT_OFFSET:SAT_OFFSET+512]) or any(source[shadow:shadow+512]):
        raise ValueError("Original live or DMA-source SAT is not empty")
    visible_rows = (63, *range(30))  # BYR=511, 240-pixel screen
    bat = struct.unpack_from("<4096H", source, VRAM_OFFSET)
    visible_tiles = {bat[y*64+x] & 0x7FF for y in visible_rows for x in range(33)}
    for p in PATTERNS:
        pos = VRAM_OFFSET+p*128
        if any(source[pos:pos+128]):
            raise ValueError("Sprite pattern already contains graphics")
        if any(tile in visible_tiles for tile in range(p*4, p*4+4)):
            raise ValueError("Sprite pattern used by visible background")
        if not (pos+128 <= shadow or pos >= shadow+512):
            raise ValueError("Sprite pattern overlaps SAT-DMA source")
    screenshot = source[tail-256*240*4:tail]
    for y in range(207, 222):
        for x in range(60, 196):
            at = (y*256+x)*4
            if screenshot[at:at+3] != b"\0\0\0":
                raise ValueError("Expected black subtitle margin is occupied")
    output = bytearray(source)
    for i, p in enumerate(PATTERNS):
        pos = VRAM_OFFSET+p*128
        output[pos:pos+128] = sprite_planes(TEXT[2*i:2*i+2])
        # SAT coordinates are screen +32 (X), +64 (Y). 0x0080=foreground.
        struct.pack_into("<4H", output, SAT_OFFSET+i*8,
                         207+64, 64+i*16+32, p*2, 0x008F)
    output[shadow:shadow+512] = output[SAT_OFFSET:SAT_OFFSET+512]
    if struct.unpack_from("<20H", output, REGISTERS) != regs:
        raise AssertionError("Changed VDC control register")
    if output[tail-256*240*4:] != source[tail-256*240*4:]:
        raise AssertionError("Changed embedded screenshot or state header")
    changes = [i for i,(a,b) in enumerate(zip(source,output)) if a != b]
    if len(changes) != 508 or any(
        not (VRAM_OFFSET <= i < VRAM_OFFSET+65536 or
             SAT_OFFSET <= i < SAT_OFFSET+512) for i in changes
    ):
        raise AssertionError("Unexpected binary changes")
    if sha(output) != EXPECTED_SHA256:
        raise AssertionError("Regression mismatch against verified slot-3 state")
    return bytes(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.resolve() == args.state.resolve():
        parser.error("Refusing to overwrite source or existing output")
    output = create(args.state.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(output)
    print(json.dumps(dict(output_sha256=sha(output),
                          status="static QA passed; Geargrafx gameplay untested"), indent=2))


if __name__ == "__main__":
    main()
