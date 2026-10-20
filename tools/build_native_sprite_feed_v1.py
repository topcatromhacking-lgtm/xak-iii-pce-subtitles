#!/usr/bin/env python3
"""Reproducible Geargrafx v44 slot-5 native sprite-queue feed test.

Original state input required. Changes only working RAM; never modifies a disc,
audio, the original save, VDC graphics or the saved screenshot.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

EXPECTED_INPUT_SHA = "4cf4f8064b78de6059f5e8f58f6dcc1304e90ab26d4695918e318750a6783a1b"
EXPECTED_OUTPUT_SHA = "6ed046b184df5f32ce4371ee81086cf09b3902ac99224db98ba10f4dab418bda"
WRAM_FILE = 21
CDRAM_FILE = 13 + 8 + 0x8000 + 4
VRAM_FILE = 0x48C67
SAT_FILE = VRAM_FILE + 0x10000 + 4 + 40
PATTERNS = (504, 505, 506, 507, 30, 31, 43, 56)
COUNT_ADDR = 0x3444
SELECTOR_ADDR = 0x2EA4
BYTE_FIELDS = (0x3264, 0x32C4, 0x3324, 0x3384,
               0x30E4, 0x3144, 0x33E4, 0x3204)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def wram_address(address):
    if not 0x2000 <= address < 0x4000:
        raise ValueError("Not a CPU working-RAM address")
    return WRAM_FILE + address - 0x2000


def sprite_entries():
    for i, pattern in enumerate(PATTERNS):
        yield 271, 96 + i * 16, pattern * 2, 0x008F


def expected_sat():
    return b"".join(struct.pack("<4H", *entry) for entry in sprite_entries())


def simulate_sat_copy(state):
    """The effect of Xak III's $8539-$8592 SAT table writer and zero-fill."""
    sat = bytearray(512)
    count = min(64, state[wram_address(COUNT_ADDR)])
    for x in range(count):
        y = state[wram_address(SELECTOR_ADDR + x)]
        sat[8*x:8*x+8] = bytes(state[wram_address(base + y)] for base in BYTE_FIELDS)
    return bytes(sat)


def build(base):
    if sha(base) != EXPECTED_INPUT_SHA:
        raise ValueError("The original slot-4 SHA-256 does not match")
    h = len(base) - 200
    if struct.unpack_from("<III", base, h) != (0x82190619, 44, len(base)):
        raise ValueError("Expected native Geargrafx v44 save state")
    if base[wram_address(COUNT_ADDR)] != 0:
        raise ValueError("Initial active-sprite count is not zero")
    if base[wram_address(0x233F):wram_address(0x2340)+1] != b"\x00\x0c":
        raise ValueError("Game sprite output address is not $0C00")
    if base[CDRAM_FILE+0x4516:CDRAM_FILE+0x451A] != bytes.fromhex("a9 00 85 f7"):
        raise ValueError("The loaded updater code differs")
    if base[CDRAM_FILE+0x4574:CDRAM_FILE+0x457C] != bytes.fromhex("e0 40 b0 1b 9c 02 00 9c"):
        raise ValueError("The native SAT zero-fill code differs")
    regs = struct.unpack_from("<20H", base, VRAM_FILE + 65536 + 4)
    if (regs[5], regs[15], regs[19]) != (0x00CC, 0x0010, 0x0C00):
        raise ValueError("Video/sprite control registers differ")
    if any(base[VRAM_FILE+0x0C00*2:VRAM_FILE+0x0C00*2+512]):
        raise ValueError("The SAT DMA source is not blank")
    for pattern in PATTERNS:
        if not any(base[VRAM_FILE+pattern*128:VRAM_FILE+(pattern+1)*128]):
            raise ValueError("Missing a previously loaded subtitle sprite pattern")
    allowed = {wram_address(COUNT_ADDR)}
    for i in range(8):
        allowed.add(wram_address(SELECTOR_ADDR + i))
        allowed.update(wram_address(base_addr + i) for base_addr in BYTE_FIELDS)
    if any(base[index] != 0 for index in allowed):
        raise ValueError("Sprite tables already contain records; refusing overwrite")
    result = bytearray(base)
    result[wram_address(COUNT_ADDR)] = 8
    for i, entry in enumerate(sprite_entries()):
        result[wram_address(SELECTOR_ADDR+i)] = i
        for field, value in zip(BYTE_FIELDS, struct.pack("<4H", *entry)):
            result[wram_address(field+i)] = value
    if simulate_sat_copy(result) != expected_sat() + bytes(512-64):
        raise AssertionError("Native SAT copy simulation mismatch")
    if result[WRAM_FILE+0x8000:] != base[WRAM_FILE+0x8000:]:
        raise AssertionError("Some non-WRAM data was changed")
    differences = [i for i, (old, new) in enumerate(zip(base, result)) if old != new]
    if len(differences) != 52 or any(i not in allowed for i in differences):
        raise AssertionError("Unexpected changes outside sprite queue")
    if sha(result) != EXPECTED_OUTPUT_SHA:
        raise AssertionError("Output regression SHA-256 mismatch")
    return bytes(result), dict(input_sha256=sha(base), output_sha256=sha(result),
                               changed_bytes=52, affected_memory="CPU WRAM only",
                               predicted_sat_match=True,
                               runtime_status="not yet tested")


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--state", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--report", type=Path, required=True)
    ns = a.parse_args()
    if ns.out.exists() or ns.report.exists() or ns.out.resolve() == ns.state.resolve():
        a.error("Refusing to overwrite existing files or the source state")
    binary, report = build(ns.state.read_bytes())
    ns.out.parent.mkdir(parents=True, exist_ok=True)
    ns.report.parent.mkdir(parents=True, exist_ok=True)
    ns.out.write_bytes(binary)
    ns.report.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
