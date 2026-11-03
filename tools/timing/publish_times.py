#!/usr/bin/env python3
"""Copy reviewed times (and English/status/notes) from the private script TSV into the
public one, never Japanese: ja_text and en_reference stay empty, and any non-ASCII
character in notes is rejected (fix the private note first) unless --strip is given.

  publish_times.py PRIVATE.tsv script/xak3_cutscenes.tsv [--strip]
"""
import argparse, csv, re, sys
ap = argparse.ArgumentParser(); ap.add_argument('private'); ap.add_argument('public')
ap.add_argument('--strip', action='store_true'); ns = ap.parse_args()
priv = {r['cue_id']: r for r in csv.DictReader(open(ns.private, encoding='utf-8'), delimiter='\t')}
rows = list(csv.DictReader(open(ns.public, encoding='utf-8'), delimiter='\t')); F = list(rows[0].keys())
bad = 0
for r in rows:
    p = priv.get(r['cue_id'])
    if not p: continue
    for k in ('speaker', 'en_subtitle', 'start', 'end', 'status', 'cd_track', 'notes', 'ja_source'):
        v = p[k]
        if re.search(r'[^\x00-\x7f]', v):
            if not ns.strip:
                print(f"non-ASCII in {r['cue_id']}.{k}: fix it or use --strip", file=sys.stderr); bad += 1; continue
            v = re.sub(r'\s*[^\x00-\x7f]+\s*', ' ', v).strip()
        r[k] = v
    r['ja_text'] = ''; r['en_reference'] = ''
if bad: sys.exit(1)
with open(ns.public, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, F, delimiter='\t', lineterminator='\n'); w.writeheader(); w.writerows(rows)
print('published', sum(1 for r in rows if r['start']), 'timed cues')
