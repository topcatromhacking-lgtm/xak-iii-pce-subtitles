#!/usr/bin/env python3
"""Apply reviewed cue times to the private script TSV.

  apply_times.py --tsv PRIVATE.tsv TIMES.tsv [--hold 0.6 --min 1.2 --gap 0.05]

TIMES.tsv rows: cue_id, speech_start, speech_end, conf, note (seconds from the cue's CD
track INDEX 01). Display end = speech_end + hold, at least start + min, cut to the next
cue's start - gap. Writes start/end and 'timing:<conf> <note>' into notes.
"""
import argparse, csv, re
ap = argparse.ArgumentParser(); ap.add_argument('--tsv', required=True); ap.add_argument('times')
ap.add_argument('--hold', type=float, default=0.6); ap.add_argument('--min', type=float, default=1.2)
ap.add_argument('--gap', type=float, default=0.05); ns = ap.parse_args()
T = [l.rstrip('\n').split('\t') for l in open(ns.times, encoding='utf-8') if l.strip() and not l.startswith('#')]
T.sort(key=lambda t: float(t[1]))
out = {}
for i, t in enumerate(T):
    s, e = float(t[1]), float(t[2])
    nxt = float(T[i + 1][1]) if i + 1 < len(T) else 1e9
    out[t[0]] = (s, max(s + 0.3, min(max(e + ns.hold, s + ns.min), nxt - ns.gap)), t[3], t[4] if len(t) > 4 else '')
rows = list(csv.DictReader(open(ns.tsv, encoding='utf-8'), delimiter='\t')); fields = list(rows[0].keys())
for r in rows:
    if r['cue_id'] in out:
        s, e, c, n = out[r['cue_id']]
        r['start'], r['end'] = f'{s:.2f}', f'{e:.2f}'
        note = re.sub(r'\s*timing:\S+[^;]*;?', '', r['notes']).strip()
        r['notes'] = (note + f' timing:{c} {n};').strip()
with open(ns.tsv, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fields, delimiter='\t', lineterminator='\n'); w.writeheader(); w.writerows(rows)
print('applied', len(out))
