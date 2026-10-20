#!/usr/bin/env python3
"""Read-only Geargrafx v44/Xak III snapshot audit for sprite-counter overflow.

Analyzes two user-owned save states without modifying or publishing either.
Addresses are specific to the verified King Wavis scene overlay.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

CD_RAM_OFFSET = 13 + 8 + 0x8000 + 4
WRAM_OFFSET = 21
CPU_OFFSET = 0x6A2C9
VDC_OFFSET = 0x48C67
LIVE_SAT_OFFSET = VDC_OFFSET + 0x10000 + 4 + 40
SPRITE_COUNT = 0x3444
SELECTOR_START = 0x2EA4
SELECTOR_CAPACITY = 96
SLOT6_SHA = "65cd995a37490f80208a52bcdee1c381927e3066aded4534ff4a32e395087c76"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def wram(b, addr):
    if not 0x2000 <= addr < 0x4000:
        raise ValueError("Outside CPU WRAM address range")
    return b[WRAM_OFFSET + addr - 0x2000]


def inspect(b):
    h = len(b) - 200
    if h < 0 or struct.unpack_from("<III", b, h) != (0x82190619, 44, len(b)):
        raise ValueError("Expected a native Geargrafx v44 state")
    if b[0] != 1 or b[13:21] != bytes.fromhex("FF F8 80 81 82 83 84 00"):
        raise ValueError("Incompatible CD-ROM or memory bank state")
    pc, A, X, Y, S, P = struct.unpack_from("<H5B", b, CPU_OFFSET)
    bank = b[13 + pc // 0x2000]
    if not 0x80 <= bank <= 0x87:
        raise ValueError("CPU PC outside mapped CD RAM")
    code = b[CD_RAM_OFFSET:CD_RAM_OFFSET + 65536]
    if code[0x44F0:0x44FB] != bytes.fromhex("AD 44 34 42 99 A4 2E 42 EE 44 34"):
        raise ValueError("Sprite accumulator instructions at CPU $84F0 differ")
    if code[0x4EE5:0x4EE8] != bytes.fromhex("20 16 85"):
        raise ValueError("Normal scene loop call at CPU $8EE5 differs")
    count = wram(b, SPRITE_COUNT)
    cdda_offset = h - (256 * 240 * 4) - 65647
    cdda = struct.unpack_from("<10Ihh", b, cdda_offset)
    if not (cdda[1] in range(4) and cdda[6] < 588
            and cdda[2] <= cdda[4] <= cdda[3]):
        raise ValueError("Unexpected CD audio layout")
    live = b[LIVE_SAT_OFFSET:LIVE_SAT_OFFSET + 512]
    shadow = b[VDC_OFFSET + 0x1800:VDC_OFFSET + 0x1800 + 512]
    return {
        "sha256": sha(b),
        "pc": f"${pc:04X}",
        "cpu_bank": f"${bank:02X}",
        "registers": dict(A=A, X=X, Y=Y, SP=S, P=P),
        "count_address": "$3444",
        "sprite_count": count,
        "selector_base": "$2EA4",
        "selector_initialized_entries": SELECTOR_CAPACITY,
        "selector_overrun_entries": max(0, count - SELECTOR_CAPACITY),
        "next_selector_write": f"${SELECTOR_START + count:04X}",
        "native_count_clear_instruction": code[0x4593:0x4596].hex(" ").upper(),
        "sprite_accumulation_opcode": "LDA $3444; SAY; STA $2EA4,Y; SAY; INC $3444",
        "native_sprite_writer_call": "$8EE5: JSR $8516",
        "normal_counter_cleanup_enabled": (
            code[0x4593:0x4596] == bytes.fromhex("9C 44 34")),
        "cdda_track28_seconds": round(
            (cdda[4] - cdda[2] + cdda[6] / 588) / 75, 3),
        "cdda_playback": ("playing", "idle", "paused", "stopped")[cdda[1]],
        "nonzero_live_SAT_bytes": sum(x != 0 for x in live),
        "nonzero_shadow_SAT_bytes": sum(x != 0 for x in shadow),
        "live_shadow_match": live == shadow,
    }


def compare(baseline, recovered):
    a, b = inspect(baseline), inspect(recovered)
    if a["sha256"] != SLOT6_SHA:
        raise ValueError("Expected the original slot 6 diagnostic input")
    if a["normal_counter_cleanup_enabled"] or b["normal_counter_cleanup_enabled"]:
        raise ValueError("Clean count instruction expected to be NOPed")
    count = b["sprite_count"]
    if count >= SELECTOR_CAPACITY:
        affected = {
            "overrun_start": f"${SELECTOR_START + SELECTOR_CAPACITY:04X}",
            "overrun_last_completed": f"${SELECTOR_START + count - 1:04X}",
            "normal_next_data_table": "$2F04 (selector table ends at $2F03)",
            "sprite_position_table": "$2F64 (overrun reaches it at count >=192)",
        }
    else:
        affected = None
    return {
        "baseline": a,
        "after": b,
        "WRAM_changed_bytes": sum(x != y for x, y in zip(
            baseline[WRAM_OFFSET:WRAM_OFFSET + 32768],
            recovered[WRAM_OFFSET:WRAM_OFFSET + 32768])),
        "CD_RAM_changed_bytes": sum(x != y for x, y in zip(
            baseline[CD_RAM_OFFSET:CD_RAM_OFFSET + 65536],
            recovered[CD_RAM_OFFSET:CD_RAM_OFFSET + 65536])),
        "counter_overflow_region": affected,
        "conclusion": ("Native sprite count reset was disabled; accumulation reached "
                       f"{count}, exceeding the 96-entry selector region and "
                       "overwriting adjacent game WRAM. Do not resume or patch "
                       "this state for normal gameplay."),
        "limitations": ("Save states show current state and modified instructions, "
                        "not a full execution trace or exact freeze instant."),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slot6", type=Path, required=True)
    ap.add_argument("--slot7", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if (args.out.exists() or args.out.resolve() in
            (args.slot6.resolve(), args.slot7.resolve())):
        ap.error("Refusing to overwrite input or existing report")
    result = compare(args.slot6.read_bytes(), args.slot7.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "baseline_PC": result["baseline"]["pc"],
        "after_PC": result["after"]["pc"],
        "sprite_count_before": result["baseline"]["sprite_count"],
        "sprite_count_after": result["after"]["sprite_count"],
        "conclusion": result["conclusion"],
    }, indent=2))


if __name__ == "__main__":
    main()
