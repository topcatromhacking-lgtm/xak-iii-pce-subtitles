#!/usr/bin/env python3
"""Xak III Geargrafx v44 subtitle sprite save-state proof of concept.

Experimental save-state modification only: not a disc patch or working
subtitle engine. Requires the user's original, hash-verified King Wavis
checkpoint. Game BIN/audio/save assets are not included in this repository.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

ORIGINAL_SHA256 = "d91527353864d7ac1d5aa3b51239582a68ee642fd9b65a5cc58817075a8dbc6b"
EXPECTED_OUTPUT_SHA256 = "db13e5018f591526322ce36990bd498a46ebd0c4c9ff551fbb1b2dc3fe7156e6"
MAGIC = 0x82190619
VRAM = 0x48C67
SAT = VRAM + 0x10000 + 2 + 2 + 40
VCE_PALETTE = 0x4884F
PATTERNS = list(range(48, 52)) + list(range(56, 60)) + list(range(504, 508))
TEXT = "ENGLISH SUBTITLE TEST"
FONT = {
    " ": ("00000",)*7,
    "A": ("01110","10001","10001","11111","10001","10001","10001"),
    "B": ("11110","10001","10001","11110","10001","10001","11110"),
    "E": ("11111","10000","10000","11110","10000","10000","11111"),
    "G": ("01111","10000","10000","10111","10001","10001","01110"),
    "H": ("10001","10001","10001","11111","10001","10001","10001"),
    "I": ("11111","00100","00100","00100","00100","00100","11111"),
    "L": ("10000","10000","10000","10000","10000","10000","11111"),
    "N": ("10001","11001","10101","10101","10011","10001","10001"),
    "S": ("01111","10000","10000","01110","00001","00001","11110"),
    "T": ("11111","00100","00100","00100","00100","00100","00100"),
    "U": ("10001","10001","10001","10001","10001","10001","01110"),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode_two_chars(pair):
    """Emit 16x16 HuC6270 sprite in four 16-row bitplanes, color index 15."""
    words = [0] * 64
    for row in range(7):
        pixels = [0] * 16
        for ci, ch in enumerate(pair):
            for column, bit in enumerate(FONT[ch][row]):
                if bit == "1":
                    pixels[ci*8 + column + 1] = 1
        mask = sum((1 << (15-x)) for x, filled in enumerate(pixels) if filled)
        for plane in range(4):
            words[16*plane + row + 4] = mask
    return struct.pack("<64H", *words)


def make_probe(original):
    if sha(original) != ORIGINAL_SHA256:
        raise ValueError("State SHA-256 mismatch: do not modify an unknown save")
    end = len(original) - 200
    if struct.unpack_from("<III", original, end) != (MAGIC, 44, len(original)):
        raise ValueError("Expected native Geargrafx v44 state")
    if struct.unpack_from("<I", original, end + 156)[0] != 256*240*4:
        raise ValueError("Expected 256x240 RGBA state screenshot")
    if struct.unpack_from("<HH", original, end + 160) != (256,240):
        raise ValueError("Unexpected native display size")
    screenshot = original[end - 256*240*4:end]
    for y in range(200, 225):
        for x in range(25, 230):
            px = (y*256+x)*4
            if screenshot[px:px+3] != b"\x00\x00\x00":
                raise ValueError("Subtitle lower margin is not black")
    if struct.unpack_from("<H", original, VCE_PALETTE+511*2)[0] != 0x1ff:
        raise ValueError("Sprite palette 15/15 is not white")
    cr = struct.unpack_from("<H", original, VRAM+0x10000+4+5*2)[0]
    mwr = struct.unpack_from("<H", original, VRAM+0x10000+4+9*2)[0]
    if not cr & 0x40 or (mwr >> 2) & 3 == 1:
        raise ValueError("Incompatible VDC sprite mode")
    if any(original[SAT:SAT+512]):
        raise ValueError("Original cutscene sprite table is not empty")

    pairs = [TEXT.ljust((len(TEXT)+1)&~1)[i:i+2]
             for i in range(0, (len(TEXT)+1)&~1, 2)]
    if len(pairs) > len(PATTERNS):
        raise ValueError("Insufficient unused VRAM patterns")
    result = bytearray(original)
    for index, pair in enumerate(pairs):
        pattern = PATTERNS[index]
        destination = VRAM + pattern*64*2
        if any(original[destination:destination+128]):
            raise ValueError(f"VRAM sprite pattern {pattern} is not empty")
        result[destination:destination+128] = encode_two_chars(pair)
        # PCE SAT coordinates = screen X+32 and screen Y+64.
        struct.pack_into("<4H", result, SAT+index*8,
                         207+64, 40+index*16+32, pattern << 1, 0x000F)
    if result[end:] != original[end:] or result[end-256*240*4:end] != screenshot:
        raise AssertionError("Geargrafx header or thumbnail mutated")
    allowed = set(range(VRAM, VRAM+65536)) | set(range(SAT, SAT+512))
    changed = [i for i, (a,b) in enumerate(zip(original,result)) if a!=b]
    if len(changed) != 590 or any(i not in allowed for i in changed):
        raise AssertionError("Unexpected changes outside first VDC VRAM/SAT")
    if sha(result) != EXPECTED_OUTPUT_SHA256:
        raise AssertionError("Output differs from independently checked pilot")
    return bytes(result), {
        "original_sha256": ORIGINAL_SHA256,
        "output_sha256": EXPECTED_OUTPUT_SHA256,
        "changed_bytes": len(changed),
        "message": TEXT,
        "sprite_count": len(pairs),
        "status": "experimental snapshot only; no emulator runtime QA"
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    a=ap.parse_args()
    if a.out.exists() or a.report.exists() or a.out.resolve()==a.state.resolve():
        ap.error("Refusing to overwrite an existing file or original state")
    output, report = make_probe(a.state.read_bytes())
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_bytes(output)
    a.report.write_text(json.dumps(report,indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
