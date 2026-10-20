#!/usr/bin/env python3
"""Read-only PCE CD-ROM System Card call-signature scanner.

A byte match is not proof of executed code: graphics/compression/data can
produce JSR-looking patterns. Locate actual call sites with a debugger.
"""
import argparse
import hashlib
import json
from pathlib import Path

SECTOR = 2352
USER_START = 16
USER_LENGTH = 2048
PREGAP = 225
CALLS = {
    "CD_READ": bytes.fromhex("20 09 E0"),
    "CD_PLAY": bytes.fromhex("20 12 E0"),
    "AD_TRANS": bytes.fromhex("20 33 E0"),
    "AD_PLAY": bytes.fromhex("20 39 E0"),
}


def user_data(raw, pregap=PREGAP):
    if len(raw) % SECTOR:
        raise ValueError("Input is not a raw 2352-byte-sector track")
    count = len(raw) // SECTOR
    if not 0 <= pregap < count:
        raise ValueError("Invalid pregap")
    first = raw[pregap * SECTOR:(pregap + 1) * SECTOR]
    if first[:12] != bytes([0] + [255] * 10 + [0]) or first[15] != 1:
        raise ValueError("Indexed data track does not start with a MODE1 sector")
    return b"".join(
        raw[i * SECTOR + USER_START:i * SECTOR + USER_START + USER_LENGTH]
        for i in range(pregap, count)
    )


def find_calls(data, pregap=PREGAP):
    hits = {}
    for name, needle in CALLS.items():
        found = []
        offset = 0
        while True:
            offset = data.find(needle, offset)
            if offset < 0:
                break
            sector = pregap + offset // USER_LENGTH
            inside = offset % USER_LENGTH
            found.append({
                "user_data_offset": offset,
                "physical_track02_sector": sector,
                "user_data_sector_offset": inside,
                "raw_track_offset": sector * SECTOR + USER_START + inside,
            })
            offset += 1
        hits[name] = found
    return hits


def scan(path, pregap=PREGAP):
    raw = path.read_bytes()
    matches = find_calls(user_data(raw, pregap), pregap)
    return {
        "filename": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "counts": {key: len(value) for key, value in matches.items()},
        "candidates": matches,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("track", type=Path, help="Original split raw Track 02 BIN")
    p.add_argument("--compare", type=Path, help="Optional reconstructed English track")
    p.add_argument("--out", type=Path, help="Write JSON to an ignored local path")
    p.add_argument("--pregap", type=int, default=PREGAP)
    args = p.parse_args()
    result = scan(args.track, args.pregap)
    result["caution"] = "Signature matches only; execution unverified."
    if args.compare:
        other = scan(args.compare, args.pregap)
        result["comparison"] = {
            "filename": other["filename"],
            "sha256": other["sha256"],
            "counts": other["counts"],
            "identical_candidate_locations": all(
                [x["user_data_offset"] for x in result["candidates"][key]]
                == [x["user_data_offset"] for x in other["candidates"][key]]
                for key in CALLS
            ),
        }
    output = json.dumps(result, indent=2) + "\n"
    if args.out:
        if args.out.resolve() == args.track.resolve() or (
            args.compare and args.out.resolve() == args.compare.resolve()
        ):
            raise ValueError("Will not overwrite game data")
        if args.out.exists():
            raise ValueError("Will not overwrite an existing report")
        args.out.write_text(output, encoding="utf-8")
        print(f"Saved scan: {args.out}")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
