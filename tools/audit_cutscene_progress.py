#!/usr/bin/env python3
"""Summarize Xak III scene readiness from public subtitle TSV, without game data."""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

def audit(tsv: Path) -> dict:
    with tsv.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    if not rows or not {'cue_id', 'scene_id', 'cd_track', 'en_subtitle', 'start', 'end', 'status'}.issubset(rows[0]):
        raise ValueError('Not a Xak III subtitle script TSV')
    groups = defaultdict(list)
    for r in rows:
        if not r['scene_id'] or not r['cue_id']:
            raise ValueError('Cue lacks a scene or ID')
        groups[r['scene_id']].append(r)
    result = {}
    for scene, cues in sorted(groups.items()):
        playable = [r for r in cues if not r['status'].startswith('SKIP')]
        completed = [r for r in playable if r['start'].strip() and r['end'].strip()]
        incomplete = [r['cue_id'] for r in playable if not (r['start'].strip() and r['end'].strip())]
        placeholders = [r['cue_id'] for r in playable if r['en_subtitle'].strip() in ('???', '...', 'TBD', 'TODO', '')]
        draft = [r['cue_id'] for r in playable if r['status'].strip().upper().startswith('DRAFT')]
        start_end = [(float(r['start']), float(r['end']), r['cue_id']) for r in completed]
        if any(e <= s for s, e, _ in start_end):
            raise ValueError(f'Scene {scene} contains an inverted cue interval')
        result[scene] = {
            'cd_tracks': sorted({r['cd_track'] for r in cues}),
            'records': len(cues),
            'playable_cues': len(playable),
            'timed_cues': len(completed),
            'untimed_cue_ids': incomplete,
            'placeholder_cue_ids': placeholders,
            'draft_cue_ids': draft,
            'end_seconds_max': max((e for _, e, _ in start_end), default=None),
            'ready_for_release_review': bool(playable) and not incomplete and not placeholders and not draft,
        }
    return {'scenes': result, 'total_records': len(rows),
            'total_timed_cues': sum(v['timed_cues'] for v in result.values()),
            'ready_scenes': [s for s, v in result.items() if v['ready_for_release_review']]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('tsv', type=Path)
    p.add_argument('--report', type=Path)
    p.add_argument('--strict', action='store_true', help='fail if any scene has draft or missing subtitles')
    args = p.parse_args()
    data = audit(args.tsv)
    if args.report:
        if args.report.exists():
            raise FileExistsError('Refusing to overwrite audit report')
        args.report.write_text(json.dumps(data, indent=2) + '\n', encoding='utf8')
    print(json.dumps(data, indent=2))
    if args.strict and len(data['ready_scenes']) != len(data['scenes']):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
