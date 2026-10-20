#!/usr/bin/env python3
"""Read-only Geargrafx v44 CD-DA-state/CUE track identification.

For Xak III, two independent saves establish a +375 sector offset between
absolute INDEX 01 CUE timecodes and saved CD audio LBA positions. This bias
must not be assumed for other discs. Original game and state files are never
modified or bundled with the tool.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

HEADER_SIZE = 200
MAGIC = 0x82190619
VERSION = 44
CDDA_TO_SCREEN_DIST = 65536 + 111


def frames(tc):
    minute, second, frame = map(int, tc.split(':'))
    if not (0 <= second < 60 and 0 <= frame < 75):
        raise ValueError("Invalid CD timecode")
    return (minute * 60 + second) * 75 + frame


def cue_tracks(path):
    content = path.read_text(encoding='utf-8-sig')
    chunks = re.split(r'(?=^\s*TRACK\s+\d+\s+)', content, flags=re.M | re.I)[1:]
    result = []
    for chunk in chunks:
        match = re.search(r'^\s*TRACK\s+(\d+)\s+(AUDIO|MODE1/2352)', chunk, re.M | re.I)
        index = re.search(r'^\s*INDEX\s+01\s+(\d+:\d{2}:\d{2})', chunk, re.M | re.I)
        if not (match and index):
            raise ValueError("Each track must have a TRACK and INDEX 01 declaration")
        result.append({
            'track': int(match.group(1)),
            'type': match.group(2),
            'cue_index': frames(index.group(1))
        })
    index_values = [x['cue_index'] for x in result]
    if len(index_values) < 2 or sorted(set(index_values)) != index_values:
        raise ValueError("Provide a single-BIN absolute-time CUE, not a split-track CUE")
    return result


def read_audio_state(path):
    data = path.read_bytes()
    tail = len(data) - HEADER_SIZE
    if tail < 0 or struct.unpack_from('<III', data, tail) != (MAGIC, VERSION, len(data)):
        raise ValueError("Expected a native Geargrafx v44 state")
    picture_size = struct.unpack_from('<I', data, tail + 156)[0]
    width, height = struct.unpack_from('<HH', data, tail + 160)
    if picture_size <= 0 or picture_size != width * height * 4:
        raise ValueError("Expected a native RGBA save-state screenshot")
    offset = tail - picture_size - CDDA_TO_SCREEN_DIST
    if offset < 0:
        raise ValueError("Inconsistent CD-DA data position")
    record = struct.unpack_from('<10Ihh', data, offset)
    _, state, first, last, now, seek, sample, stop_event, seekcycles, delay, left, right = record
    if state not in range(4) or stop_event not in range(3):
        raise ValueError("Unexpected CD-DA status")
    if not (0 <= sample < 588 and first <= now <= last):
        raise ValueError("Inconsistent CD audio position")
    return {
        'state_sha256': hashlib.sha256(data).hexdigest(),
        'playback_state': ('playing', 'idle', 'paused', 'stopped')[state],
        'start_lba': first,
        'current_lba': now,
        'stop_lba': last,
        'stop_mode': ('stop', 'loop', 'interrupt')[stop_event],
        'elapsed_seconds': round((now - first + sample / 588) / 75, 4),
    }


def match_state_to_cue(audio, tracks, bias):
    cue_start = audio['start_lba'] - bias
    found = [(i, track) for i, track in enumerate(tracks) if track['cue_index'] == cue_start]
    if len(found) != 1:
        raise ValueError("Audio start does not match a known track after applying bias")
    pos, track = found[0]
    result = dict(audio)
    result.update(track_number=track['track'], cue_start_index=cue_start, cue_lba_bias=bias)
    if pos + 1 < len(tracks):
        next_start = tracks[pos + 1]['cue_index']
        result['track_duration_seconds'] = round((next_start - cue_start) / 75, 4)
        result['stop_lba_matches_next_track'] = audio['stop_lba'] - bias == next_start
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cue', type=Path, required=True,
                        help="Single-BIN English CUE, with absolute INDEX 01 positions")
    parser.add_argument('--state', type=Path, action='append', required=True,
                        help="Geargrafx v44 .stateN file (repeat to compare)")
    parser.add_argument('--bias', type=int, default=375,
                        help="CUE-LBA sector offset (Xak III v1.0 measured +375)")
    parser.add_argument('--out', type=Path, help="Optional ignored local JSON output")
    args = parser.parse_args()
    tracks = cue_tracks(args.cue)
    output = {
        'disc_cue': args.cue.name,
        'assumed_cue_lba_bias': args.bias,
        'states': [
            dict(filename=path.name,
                 **match_state_to_cue(read_audio_state(path), tracks, args.bias))
            for path in args.state
        ],
        'warning': "A save state confirms CD audio position, not executed CPU code."
    }
    result = json.dumps(output, indent=2) + '\n'
    if args.out:
        if args.out.exists() or args.out in [args.cue, *args.state]:
            raise ValueError("Refusing to overwrite source or existing output")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(result, encoding='utf-8')
    print(result, end='')


if __name__ == '__main__':
    main()
