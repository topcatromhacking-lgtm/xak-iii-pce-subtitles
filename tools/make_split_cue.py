#!/usr/bin/env python3
"""Create a split-track English CUE by replacing only Japanese Track 02's filename.

No game/audio BIN content is read or modified by this script.
"""
import argparse
import re
from pathlib import Path


def convert(cue: str, english_filename: str) -> str:
    if '"' in english_filename or '\n' in english_filename or '\r' in english_filename:
        raise ValueError('Invalid quoted BIN filename')
    lines = cue.splitlines(keepends=True)
    tracks = [int(x) for x in re.findall(r'^\s*TRACK\s+(\d+)\s+', cue, re.M | re.I)]
    if tracks != list(range(1, 36)):
        raise ValueError('Expected exactly 35 ordered tracks')
    index = None
    for i, line in enumerate(lines):
        if re.match(r'^FILE\s+".*\(Track 02\)\.bin"\s+BINARY\s*$', line.strip(), re.I):
            if index is not None:
                raise ValueError('Ambiguous Track 02 file')
            index = i
    if index is None:
        raise ValueError('Cannot locate Japanese split Track 02 FILE entry')
    ending = '\r\n' if lines[index].endswith('\r\n') else '\n'
    lines[index] = f'FILE "{english_filename}" BINARY{ending}'
    return ''.join(lines)


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--japanese-cue', type=Path, required=True)
    a.add_argument('--english-bin-name', default='Xak_III_English_Track02_Reconstructed.bin')
    a.add_argument('--out', type=Path, required=True)
    ns = a.parse_args()
    if ns.out.exists() or ns.out.resolve() == ns.japanese_cue.resolve():
        a.error('Refusing to overwrite input or existing output')
    source = ns.japanese_cue.read_bytes().decode('utf-8-sig')
    result = convert(source, ns.english_bin_name)
    ns.out.parent.mkdir(parents=True, exist_ok=True)
    ns.out.write_bytes(result.encode('utf-8'))
    print(f'Wrote split-track CUE to {ns.out} (35 tracks; Track 02 replaced only)')


if __name__ == '__main__':
    main()
