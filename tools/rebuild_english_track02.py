#!/usr/bin/env python3
"""Reconstruct English raw Track 02 from the user's private Japanese Track 02.

Requires the original unmodified NightWolve BIN/ISO PPF3 files. No executable
from the historical patch archive is run. Originals are read-only.
"""
import argparse
import hashlib
import json
from pathlib import Path

SECTOR = 2352
DATA_OFFSET = 16
DATA_LEN = 2048
JAPAN_PREGAP_SECTORS = 225
COMBINED_INDEX01_SECTOR = 3365
COMBINED_START = COMBINED_INDEX01_SECTOR * SECTOR
LOCAL_START = JAPAN_PREGAP_SECTORS * SECTOR
DIFFERENCE = COMBINED_START - LOCAL_START
EXPECTED_SECTORS = 23288
EXPECTED_JAPANESE_SHA256 = 'af04551ce4bf60d50397e99a6467c9e081b3091caa4eb95c67e7984578021733'
EXPECTED_BIN_PPF_SHA256 = '45c6938e87d7baf334b2715b55ab1e9521343d43f8075ea239ed1b290e571fac'
EXPECTED_ISO_PPF_SHA256 = '4be6f96ae9a5fd1588ef308e5cfe732da83f5fbf77ae14da43242f2a2f7e0ee6'
EXPECTED_ENGLISH_SHA256 = 'c3aef214616309a6a87f9836bdc8062e57b3e2d5b492b089f72fd52848cd9b72'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def records(path):
    data = path.read_bytes()
    if data[:5] != b'PPF30' or data[5] != 2:
        raise ValueError('Expected PPF3 revision 2 header')
    cur = 60
    out = []
    while cur < len(data):
        if cur + 9 > len(data):
            raise ValueError('Truncated PPF record')
        pos = int.from_bytes(data[cur:cur + 8], 'little')
        n = data[cur + 8]
        if n <= 0 or cur + 9 + n > len(data):
            raise ValueError('Invalid PPF record')
        out.append((pos, data[cur + 9:cur + 9 + n]))
        cur += 9 + n
    return out


def apply_on_bin(jp, ppf):
    edited = set()
    for pos, b in ppf:
        local = pos - DIFFERENCE
        if not (LOCAL_START <= local and local + len(b) <= len(jp)):
            raise ValueError('BIN patch edits outside Track 02 user data')
        for i in range(len(b)):
            if local + i in edited:
                raise ValueError('Overlapping BIN PPF edits')
            edited.add(local + i)
        jp[local:local + len(b)] = b
    return len(edited)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--japanese-track', type=Path, required=True)
    p.add_argument('--bin-ppf', type=Path, required=True)
    p.add_argument('--iso-ppf', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists() or a.out.resolve() == a.japanese_track.resolve():
        raise ValueError('Refusing to overwrite a source or existing output')
    if a.report.exists() or a.report.resolve() == a.japanese_track.resolve():
        raise ValueError('Refusing to overwrite an existing report or source')
    jp = a.japanese_track.read_bytes()
    if sha(jp) != EXPECTED_JAPANESE_SHA256:
        raise ValueError('Japanese Track 02 SHA-256 mismatch')
    if sha(a.bin_ppf.read_bytes()) != EXPECTED_BIN_PPF_SHA256:
        raise ValueError('Incorrect BIN PPF version')
    if sha(a.iso_ppf.read_bytes()) != EXPECTED_ISO_PPF_SHA256:
        raise ValueError('Incorrect ISO PPF version')
    if len(jp) != SECTOR * EXPECTED_SECTORS:
        raise ValueError('Incorrect Track 02 size')
    if jp[LOCAL_START:LOCAL_START + 12] != bytes([0] + [255] * 10 + [0]) or jp[LOCAL_START + 15] != 1:
        raise ValueError('Track 02 MODE1/2352 sync/header mismatch')
    rows = records(a.bin_ppf)
    rows_iso = records(a.iso_ppf)
    iso = bytearray()
    for i in range(JAPAN_PREGAP_SECTORS, EXPECTED_SECTORS):
        o = i * SECTOR
        iso.extend(jp[o + DATA_OFFSET:o + DATA_OFFSET + DATA_LEN])
    changes_iso = set()
    for pos, b in rows_iso:
        if not (0 <= pos and pos + len(b) <= len(iso)):
            raise ValueError('ISO patch edits outside Track 02')
        for i in range(len(b)):
            if pos + i in changes_iso:
                raise ValueError('Overlapping ISO PPF edits')
            changes_iso.add(pos + i)
        iso[pos:pos + len(b)] = b
    translated = bytearray(jp)
    changed_positions = apply_on_bin(translated, rows)
    for i in range(EXPECTED_SECTORS - JAPAN_PREGAP_SECTORS):
        start = (i + JAPAN_PREGAP_SECTORS) * SECTOR
        if translated[start + DATA_OFFSET:start + DATA_OFFSET + DATA_LEN] != iso[i * DATA_LEN:(i + 1) * DATA_LEN]:
            raise ValueError(f'BIN and ISO patches disagree at data sector {i}')
    if translated[:LOCAL_START] != jp[:LOCAL_START]:
        raise ValueError('Pregap unexpectedly changed')
    for i in range(JAPAN_PREGAP_SECTORS, EXPECTED_SECTORS):
        if translated[i * SECTOR:i * SECTOR + 16] != jp[i * SECTOR:i * SECTOR + 16]:
            raise ValueError(f'Raw sector header changed at sector {i}')
    if sha(translated) != EXPECTED_ENGLISH_SHA256:
        raise ValueError('Reconstructed Track 02 SHA-256 mismatch')
    changed = sum(x != y for x, y in zip(jp, translated))
    report = {
        'source_sha256': sha(jp),
        'english_sha256': sha(translated),
        'raw_sector_bytes': len(jp),
        'cd_sectors': EXPECTED_SECTORS,
        'pregap_sectors': JAPAN_PREGAP_SECTORS,
        'indexed_sectors': EXPECTED_SECTORS - JAPAN_PREGAP_SECTORS,
        'bin_ppf_records': len(rows),
        'iso_ppf_records': len(rows_iso),
        'bin_patched_positions': changed_positions,
        'iso_patched_positions': len(changes_iso),
        'actual_changed_bytes': changed,
        'full_disc_to_split_bin_offset': DIFFERENCE,
        'bin_iso_user_data_agreement': True,
        'raw_sector_headers_and_pregap_preserved': True,
        'notes': 'Track 02 only; Japanese CD audio tracks remain untouched.'
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(translated)
    a.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
