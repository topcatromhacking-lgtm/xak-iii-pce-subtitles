#!/usr/bin/env python3
"""Align per-utterance ASR chunks to a scene's script cues and propose start/end times.

  chunk_align.py --tsv PRIVATE.tsv --scene VS1 --chunks C28.json [--write]

Chunks: JSON list of {start, end, text} in track seconds (one per detected utterance, e.g.
from a VAD + faster-whisper pass on the vocal stem). Cues keep their script order; a
monotonic DP gives each cue a run of 0..4 consecutive chunks, maximising the reading
similarity (hiragana bigram Dice via pykakasi) between the cue's Japanese line and the
chunks' ASR text, with a small cost for skipped chunks (noise, grunts). Cues that get no
chunk are interpolated between neighbours and marked low confidence.

Output: a table (cue_id, start, end, conf, n_chunks) on stdout; with --write, fills the
TSV's start/end (seconds, 2 decimals) and appends 'timing:asr conf=..' to notes. The TSV is
the private one (Japanese text): never commit it; publish times with make_script_tsv.py.
"""
import argparse, csv, json, re, sys
try:
    import pykakasi
    _K = pykakasi.kakasi()
    def reading(s): return ''.join(x['hira'] for x in _K.convert(s))
except ImportError:          # degrade to raw characters
    def reading(s): return s
PUNCT = re.compile(r'[\s\u3001\u3002\uff01\uff1f!?\u2026\u30fb\u300c\u300d\u300e\u300f\uff08\uff09()\-\u30fc\u301c~.,:;"\'|\[\]]+')
def norm(s): return PUNCT.sub('', reading(PUNCT.sub('', s)))
def grams(s): return {s[i:i + 2] for i in range(len(s) - 1)} | set(s)
def sim(a, b):
    A, B = grams(a), grams(b)
    return 2 * len(A & B) / (len(A) + len(B)) if A and B else 0.0

def align(cues, chunks, maxk=4, skip=0.05, ns_none=0.15):
    n, m = len(cues), len(chunks)
    cn = [norm(c) for c in cues]; hn = [norm(h['text']) for h in chunks]
    NEG = -1e9
    dp = [[NEG] * (m + 1) for _ in range(n + 1)]; bk = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for j in range(1, m + 1):                       # leading noise chunks
        dp[0][j] = dp[0][j - 1] - skip; bk[0][j] = ('skip', j - 1)
    for i in range(1, n + 1):
        for j in range(0, m + 1):
            best, arg = dp[i - 1][j] - ns_none, ('none', j)   # cue with no chunk
            if j and dp[i][j - 1] - skip > best:              # skip chunk j-1 (after cue i)
                best, arg = dp[i][j - 1] - skip, ('skip', j - 1)
            for k in range(1, maxk + 1):
                if j - k < 0: break
                s = sim(cn[i - 1], ''.join(hn[j - k:j]))
                # length agreement: reading length vs speech duration (~8 morae/s)
                dur = chunks[j - 1]['end'] - chunks[j - k]['start']
                v = dp[i - 1][j - k] + s - 0.04 * abs(dur - len(cn[i - 1]) / 8.0)
                if v > best: best, arg = v, ('take', j - k, s)
            dp[i][j], bk[i][j] = best, arg
    out = [None] * n; i, j = n, m
    while i > 0 or j > 0:
        a = bk[i][j]
        if a[0] == 'skip': j = a[1]
        elif a[0] == 'none': out[i - 1] = None; i -= 1
        else: out[i - 1] = (a[1], j, a[2]); j = a[1]; i -= 1
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tsv', required=True); ap.add_argument('--scene', required=True)
    ap.add_argument('--chunks', required=True); ap.add_argument('--write', action='store_true')
    ap.add_argument('--min-dur', type=float, default=1.2); ap.add_argument('--hold', type=float, default=0.4)
    ns = ap.parse_args()
    rows = list(csv.DictReader(open(ns.tsv, encoding='utf-8'), delimiter='\t'))
    fields = list(rows[0].keys())
    idx = [i for i, r in enumerate(rows) if r['scene_id'] == ns.scene]
    chunks = [c for c in json.load(open(ns.chunks)) if c['end'] > c['start']]
    al = align([rows[i]['ja_text'] for i in idx], chunks)
    # an empty cue next to a multi-chunk cue takes that cue's outer chunk
    for i, a in enumerate(al):
        if a: continue
        for nb, side in ((i - 1, 'tail'), (i + 1, 'head')):
            if 0 <= nb < len(al) and al[nb] and al[nb][1] - al[nb][0] >= 2:
                k0, k1, s0 = al[nb]
                if side == 'tail': al[nb] = (k0, k1 - 1, s0); al[i] = (k1 - 1, k1, 0.0)
                else: al[nb] = (k0 + 1, k1, s0); al[i] = (k0, k0 + 1, 0.0)
                break
    res = []
    for q, a in zip(idx, al):
        if a:
            k0, k1, s = a
            res.append([rows[q]['cue_id'], chunks[k0]['start'], chunks[k1 - 1]['end'], s, k1 - k0])
        else:
            res.append([rows[q]['cue_id'], None, None, 0.0, 0])
    # interpolate missing, then pad/hold and remove overlaps
    for i, r in enumerate(res):
        if r[1] is None:
            prev = next((res[k][2] for k in range(i - 1, -1, -1) if res[k][2] is not None), 0.0)
            nxt = next((res[k][1] for k in range(i + 1, len(res)) if res[k][1] is not None), prev + 2.0)
            r[1], r[2] = prev + 0.1, max(prev + 0.2, nxt - 0.1)
    for i, r in enumerate(res):
        nxt = res[i + 1][1] if i + 1 < len(res) else 1e9
        r[2] = max(r[1] + 0.3, min(max(r[2] + ns.hold, r[1] + ns.min_dur), nxt - 0.05))
    for r in res:
        conf = 'high' if r[3] >= 0.45 else 'med' if r[3] >= 0.25 else 'low'
        r.append(conf)
        print(f'{r[0]}\t{r[1]:.2f}\t{r[2]:.2f}\t{r[3]:.2f}\t{r[4]}\t{conf}')
    print('summary', {c: sum(1 for r in res if r[5] == c) for c in ('high', 'med', 'low')}, file=sys.stderr)
    if ns.write:
        by = {r[0]: r for r in res}
        for r in rows:
            if r['cue_id'] in by:
                b = by[r['cue_id']]
                r['start'], r['end'] = f'{b[1]:.2f}', f'{b[2]:.2f}'
                note = re.sub(r'\s*timing:asr conf=\w+ sim=[\d.]+', '', r.get('notes', ''))
                r['notes'] = (note + f' timing:asr conf={b[5]} sim={b[3]:.2f}').strip()
        with open(ns.tsv, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fields, delimiter='\t', lineterminator='\n'); w.writeheader(); w.writerows(rows)

if __name__ == '__main__':
    main()
