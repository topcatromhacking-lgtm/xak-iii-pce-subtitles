#!/usr/bin/env python3
"""Time script cues from a Japanese ASR transcript with word timestamps.

Input: the scene's rows in script/xak3_cutscenes.tsv (ja_text must be present, so
use the PRIVATE TSV) and an ASR JSON list of segments with "words":[{s,e,w,p}]
(faster-whisper word_timestamps=True on a vocal stem, see docs/timing.md).
Each cue's ja_text is matched, in order, against the ASR character stream with a
local fuzzy alignment (difflib), giving start = time of the first matched char
and end = time of the last. Cues that match poorly are reported, not guessed.

  python3 tools/timing/asr_align.py --tsv PRIVATE.tsv --scene VS1 --asr asr/T28.json [--write]
Writes start/end (seconds from track INDEX 01) only with --write, and only into
empty cells unless --overwrite. Prints a confidence (matched-char ratio) per cue.
"""
import argparse, csv, json, re, sys, unicodedata
from difflib import SequenceMatcher

KEEP = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff\uff66-\uff9fA-Za-z0-9]')


def norm(s):
    s = unicodedata.normalize('NFKC', s)
    s = ''.join(ch for ch in s if KEEP.match(ch))
    # katakana -> hiragana so ASR kana/kanji variants line up a bit better
    return ''.join(chr(ord(c) - 0x60) if '\u30a1' <= c <= '\u30f6' else c for c in s)


def char_stream(segs):
    chars, times = [], []
    for sg in segs:
        for w in sg.get('words', []):
            t = norm(w['w'])
            if not t or w.get('p', 1) < 0.05:
                continue
            n = len(t)
            for i, c in enumerate(t):
                chars.append(c); times.append(w['s'] + (w['e'] - w['s']) * (i + 0.5) / n)
    return ''.join(chars), times


def align(cues, stream, times, look=400):
    pos, out = 0, []
    for cue in cues:
        q = norm(cue['ja_text'])
        if not q:
            out.append((cue, None, None, 0.0)); continue
        hay = stream[pos:pos + look]
        sm = SequenceMatcher(None, q, hay, autojunk=False)
        blocks = [b for b in sm.get_matching_blocks() if b.size]
        # keep blocks that form a compact window
        if not blocks:
            out.append((cue, None, None, 0.0)); continue
        best, bscore = None, 0
        for i in range(len(blocks)):
            j0 = blocks[i].b; m = 0; last = None
            for b in blocks[i:]:
                if b.b - j0 > 2.5 * len(q) + 6: break
                m += b.size; last = b
            if m > bscore: bscore, best = m, (j0, last.b + last.size)
        conf = bscore / len(q)
        if conf < 0.3:
            out.append((cue, None, None, conf)); continue
        a, b = pos + best[0], pos + best[1] - 1
        out.append((cue, times[a] - 0.15, times[b] + 0.35, conf))
        pos = b + 1
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tsv', required=True); ap.add_argument('--scene', required=True)
    ap.add_argument('--asr', required=True); ap.add_argument('--write', action='store_true')
    ap.add_argument('--overwrite', action='store_true'); ap.add_argument('--min-conf', type=float, default=0.45)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.tsv, encoding='utf-8'), delimiter='\t'))
    fields = list(rows[0].keys())
    cues = [r for r in rows if r['scene_id'] == a.scene and r['status'] != 'SKIP']
    if not any(c['ja_text'] for c in cues):
        sys.exit('no ja_text in this TSV (public copy?); use the private TSV')
    stream, times = char_stream(json.load(open(a.asr, encoding='utf-8')))
    res = align(cues, stream, times)
    n = 0
    for cue, s, e, conf in res:
        flag = '' if s is not None and conf >= a.min_conf else '  <-- check by ear'
        ts = f'{s:7.2f} {e:7.2f}' if s is not None else '      -       -'
        print(f"{cue['cue_id']:9s} {ts}  conf {conf:4.2f}  {cue['en_subtitle'][:40]}{flag}")
        if a.write and s is not None and conf >= a.min_conf and (a.overwrite or not cue['start']):
            cue['start'], cue['end'] = f'{max(0, s):.2f}', f'{e:.2f}'; n += 1
    # fix overlaps: an end may not run past the next start
    if a.write:
        timed = [c for c in cues if c['start']]
        for c1, c2 in zip(timed, timed[1:]):
            if float(c1['end']) > float(c2['start']) - 0.05:
                c1['end'] = f"{float(c2['start']) - 0.05:.2f}"
        with open(a.tsv, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n'); w.writeheader(); w.writerows(rows)
        print(f'wrote {n} cue times to {a.tsv}')


if __name__ == '__main__':
    main()
