#!/usr/bin/env python3
"""Locate a Geargrafx v44 CD-card RAM overlay in the user's own raw game-data BIN.

Read-only: emits offsets/hashes only. An exact disc match does not prove that
all bytes are executable code or that patching them is safe.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

SECTOR = 2352
SECTOR_USER_DATA = 2048
PREGAP = 225
HEADER_SIZE = 200
MAGIC = 0x82190619


def sha(data):
    return hashlib.sha256(data).hexdigest()


def extract_card_ram(state):
    tail = len(state) - HEADER_SIZE
    if tail < 0 or struct.unpack_from('<III', state, tail) != (MAGIC, 44, len(state)):
        raise ValueError('Expected Geargrafx v44 native save state')
    p = 13 + 8 + 0x8000  # saved CD enabled/CRC/clock; MPRs; 32K WRAM
    cd_size = struct.unpack_from('<I', state, p)[0]
    if cd_size not in (0x10000, 0x40000):
        raise ValueError('Unexpected serialized CD RAM size')
    p += 4 + cd_size
    card_size = struct.unpack_from('<I', state, p)[0]
    if not (0 < card_size <= 0x200000):
        raise ValueError('Invalid card RAM size')
    p += 4
    if p + card_size > tail:
        raise ValueError('Truncated state')
    return state[p:p + card_size]


def track_as_iso(raw, pregap=PREGAP):
    if len(raw) % SECTOR:
        raise ValueError('Raw data track length not multiple of 2352')
    count = len(raw) // SECTOR
    if not (0 <= pregap < count):
        raise ValueError('Invalid pregap')
    first = raw[pregap * SECTOR:(pregap + 1) * SECTOR]
    if first[:12] != bytes([0] + [255] * 10 + [0]) or first[15] != 1:
        raise ValueError('Indexed track does not begin with raw MODE1')
    return b''.join(raw[i * SECTOR + 16:i * SECTOR + 16 + SECTOR_USER_DATA]
                    for i in range(pregap, count))


def locate(card, iso, pregap=PREGAP):
    if len(card) < 128:
        raise ValueError('Card region too small')
    offset = -1
    matches = []
    while (offset := iso.find(card[:128], offset + 1)) != -1:
        possible = min(len(card), len(iso) - offset)
        # Identify first modified byte, if any, without dumping copied game data.
        matching = next((i for i in range(possible) if card[i] != iso[offset + i]), possible)
        sector = offset // SECTOR_USER_DATA
        record = {
            'indexed_user_data_offset': offset,
            'indexed_sector': sector,
            'raw_track_sector': pregap + sector,
            'raw_track_byte_offset': (pregap + sector) * SECTOR + 16
                + offset % SECTOR_USER_DATA,
            'matching_prefix_bytes': matching,
            'full_card_ram_match': matching == len(card)
        }
        if record['full_card_ram_match']:
            record['matched_region_sha256'] = sha(iso[offset:offset + len(card)])
        matches.append(record)
    return sorted(matches, key=lambda r: r['matching_prefix_bytes'], reverse=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-track', type=Path, required=True)
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--pregap', type=int, default=PREGAP)
    p.add_argument('--out', type=Path, help='JSON output in ignored local directory')
    a = p.parse_args()
    raw = a.data_track.read_bytes()
    state = a.state.read_bytes()
    card = extract_card_ram(state)
    report = {
        'track_sha256': sha(raw),
        'state_sha256': sha(state),
        'card_ram_bytes': len(card),
        'card_ram_sha256': sha(card),
        'disc_matches': locate(card, track_as_iso(raw, a.pregap), a.pregap)[:20],
        'notice': 'Matching source bytes do not identify a safe executable hook.'
    }
    text = json.dumps(report, indent=2) + '\n'
    if a.out:
        if a.out.exists() or a.out in (a.state, a.data_track):
            raise ValueError('Refusing to overwrite an input or an existing file')
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
