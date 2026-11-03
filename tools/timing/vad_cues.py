#!/usr/bin/env python3
"""Propose subtitle cue start/end times for one cutscene track by voice-activity detection.

Voice in Xak III cinemas is mixed with music on the same CD-DA track, so plain
energy VAD fails. This detector uses, per 20 ms frame:
  * speech-band energy (300-3400 Hz) in dB above a rolling 8 s 15th-percentile
    floor (the music bed), plus half the gain in speech-band share of total energy, and
  * spectral flux in the 1-4 kHz band (syllable onsets).
A frame is voiced when the score passes a hysteresis threshold (--hi/--lo dB).
Segments shorter than --min-seg are dropped, gaps < --merge-gap merged, and
--pad added. Then the segments are fitted to the scene's N script cues in order:
merge the closest neighbours while there are too many, split the longest while
there are too few. The output is a proposal for a human to check (Audacity labels
are written for that), not a final timing.

  python3 tools/timing/vad_cues.py build/audio/track28.wav --scene VS1 \\
      --tsv script/xak3_cutscenes.tsv --labels build/timing/VS1_labels.txt [--write]
  # after fixing the labels in Audacity:
  python3 tools/timing/vad_cues.py --from-labels build/timing/VS1_labels.txt --scene VS1 --write

Times are seconds from track INDEX 01 (what the game's CD play command starts at).
Convert to a runtime key with the scene's measured play-start offset (docs/timing.md).
"""
import argparse, csv, os, sys, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TSV = os.path.join(ROOT, "script/xak3_cutscenes.tsv")
HOP = 0.02

def read_wav(path):
    with wave.open(path) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32) / 32768
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    if sr != 16000:
        from scipy.signal import resample_poly
        from math import gcd
        g = gcd(sr, 16000); x = resample_poly(x, 16000 // g, sr // g); sr = 16000
    return x, sr

def features(x, sr):
    from scipy.signal import stft
    from scipy.ndimage import median_filter
    nper = int(0.04 * sr); hop = int(HOP * sr)
    f, t, Z = stft(x, sr, nperseg=nper, noverlap=nper - hop, boundary=None, padded=False)
    P = np.abs(Z) ** 2 + 1e-12
    sb = (f >= 300) & (f <= 3400); fb = (f >= 1000) & (f <= 4000)
    e = 10 * np.log10(P[sb].sum(axis=0))
    tot = 10 * np.log10(P.sum(axis=0))
    ratio = e - tot                                   # speech-band share
    L = np.log(P[fb]); flux = np.maximum(np.diff(L, axis=1), 0).mean(axis=0); flux = np.r_[0, flux]
    from scipy.ndimage import percentile_filter
    win = max(3, int(8.0 / HOP) | 1)
    # music-bed floor = 15th percentile of speech-band energy over 8 s
    base = percentile_filter(e, 15, size=win, mode="nearest")
    rbase = percentile_filter(ratio, 15, size=win, mode="nearest")
    fl = median_filter(flux, size=5); fl = fl / (np.percentile(fl, 50) + 1e-9)
    # score in dB above floor (+ half the speech-band-share gain, + onset flux bonus)
    score = (e - base) + 0.5 * (ratio - rbase) + np.clip(fl - 1, 0, 3)
    return t, median_filter(score, size=5)

def segments(t, score, hi, lo, min_seg, merge_gap, pad, dur):
    segs, on, s0 = [], False, 0
    for i, v in enumerate(score):
        if not on and v > hi: on, s0 = True, t[i]
        elif on and v < lo: on = False; segs.append([s0, t[i]])
    if on: segs.append([s0, t[-1]])
    merged = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < merge_gap: merged[-1][1] = s[1]
        else: merged.append(s)
    out = [[max(0, a - pad), min(dur, b + pad)] for a, b in merged if b - a >= min_seg]
    for i in range(1, len(out)):                      # no overlap after padding
        if out[i][0] < out[i - 1][1]:
            mid = (out[i][0] + out[i - 1][1]) / 2; out[i - 1][1] = mid; out[i][0] = mid
    return out

def fit(segs, n):
    segs = [list(s) for s in segs]
    if n <= 0: return segs
    while len(segs) > n:
        gaps = [segs[i + 1][0] - segs[i][1] for i in range(len(segs) - 1)]
        i = int(np.argmin(gaps)); segs[i][1] = segs[i + 1][1]; del segs[i + 1]
    while len(segs) < n and segs:
        i = int(np.argmax([b - a for a, b in segs])); a, b = segs[i]; m = (a + b) / 2
        segs[i:i + 1] = [[a, m - 0.05], [m + 0.05, b]]
    return segs

def load_rows(tsv):
    with open(tsv, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        return r.fieldnames, list(r)

def save_rows(tsv, fields, rows):
    with open(tsv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, quotechar=None)
        w.writeheader(); w.writerows(rows)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("wav", nargs="?")
    ap.add_argument("--scene"); ap.add_argument("--tsv", default=TSV)
    ap.add_argument("--hi", type=float, default=6.0, help="dB over floor to start a segment"); ap.add_argument("--lo", type=float, default=3.0)
    ap.add_argument("--min-seg", type=float, default=0.30); ap.add_argument("--merge-gap", type=float, default=0.35)
    ap.add_argument("--pad", type=float, default=0.12)
    ap.add_argument("--no-fit", action="store_true", help="don't force segment count to the cue count")
    ap.add_argument("--labels", help="write Audacity label file")
    ap.add_argument("--from-labels", help="read (corrected) Audacity labels instead of running VAD")
    ap.add_argument("--write", action="store_true", help="write start/end into the TSV (only empty cells unless --overwrite)")
    ap.add_argument("--overwrite", action="store_true")
    a = ap.parse_args()
    fields, rows = load_rows(a.tsv)
    cues = [r for r in rows if r["scene_id"] == a.scene and r["status"] != "SKIP-system-text"] if a.scene else []
    if a.from_labels:
        segs = [[float(l.split("\t")[0]), float(l.split("\t")[1])] for l in open(a.from_labels) if l.strip()]
    else:
        if not a.wav: ap.error("wav required")
        x, sr = read_wav(a.wav)
        t, sc = features(x, sr)
        raw = segments(t, sc, a.hi, a.lo, a.min_seg, a.merge_gap, a.pad, len(x) / sr)
        segs = raw if a.no_fit or not cues else fit(raw, len(cues))
        print(f"{a.wav}: {len(x)/sr:.2f} s, {len(raw)} voiced segments -> {len(segs)} cues (script has {len(cues)})")
    for i, (s0, s1) in enumerate(segs):
        cid = cues[i]["cue_id"] if i < len(cues) else f"extra{i+1}"
        txt = cues[i]["en_subtitle"] if i < len(cues) else ""
        print(f"  {cid:9s} {s0:8.2f} {s1:8.2f}  {txt}")
    if a.labels:
        os.makedirs(os.path.dirname(os.path.abspath(a.labels)), exist_ok=True)
        with open(a.labels, "w") as o:
            for i, (s0, s1) in enumerate(segs):
                o.write(f"{s0:.3f}\t{s1:.3f}\t{cues[i]['cue_id'] + ' ' + cues[i]['en_subtitle'] if i < len(cues) else 'extra'}\n")
        print("labels:", a.labels)
    if a.write:
        if not cues: ap.error("--write needs --scene")
        n = 0
        for r, (s0, s1) in zip(cues, segs):
            if a.overwrite or not r["start"].strip():
                r["start"], r["end"] = f"{s0:.2f}", f"{s1:.2f}"; n += 1
        save_rows(a.tsv, fields, rows); print(f"wrote {n} timings to {a.tsv}")

if __name__ == "__main__":
    main()
