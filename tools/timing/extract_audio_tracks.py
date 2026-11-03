#!/usr/bin/env python3
"""Extract CD-DA tracks from Paul's disc image to WAV.

Accepts a .cue (Redump-style, one FILE per track or one big BIN with INDEX
offsets) or raw track .bin files. Redump audio is 44.1 kHz s16le stereo, 2352
bytes/sector. Writes trackNN.wav (full quality) and, with --mono16k, trackNN_16k.wav
for VAD. Only AUDIO tracks are written; INDEX 00 pregap is skipped (INDEX 01 = t0,
which is what the game's CD play command seeks to). Nothing is downloaded; you
must supply your own dump.

  python3 tools/timing/extract_audio_tracks.py "Xak III (Japan).cue" -o build/audio --tracks 28-35 --mono16k
  python3 tools/timing/extract_audio_tracks.py --bin "Track 28.bin" -o build/audio
"""
import argparse, os, re, sys, wave
import numpy as np

SECTOR = 2352

def msf(s):
    m, sec, f = (int(x) for x in s.split(":"))
    return (m * 60 + sec) * 75 + f

def parse_cue(path):
    base = os.path.dirname(os.path.abspath(path))
    tracks, cur_file = [], None
    for line in open(path, encoding="utf-8", errors="replace"):
        t = line.strip()
        m = re.match(r'FILE\s+"(.+)"\s+\w+', t) or re.match(r"FILE\s+(\S+)\s+\w+", t)
        if m:
            cur_file = os.path.join(base, m.group(1)); continue
        m = re.match(r"TRACK\s+(\d+)\s+(\S+)", t)
        if m:
            tracks.append(dict(num=int(m.group(1)), mode=m.group(2), file=cur_file, idx={})); continue
        m = re.match(r"INDEX\s+(\d+)\s+(\d+:\d+:\d+)", t)
        if m and tracks:
            tracks[-1]["idx"][int(m.group(1))] = msf(m.group(2))
    # compute byte ranges (start at INDEX 01, end at next track's INDEX 00/01 in same file, else EOF)
    for i, tr in enumerate(tracks):
        start = tr["idx"].get(1, tr["idx"].get(0, 0))
        end = None
        for nx in tracks[i + 1:]:
            if nx["file"] == tr["file"]:
                end = nx["idx"].get(0, nx["idx"].get(1)); break
        size = os.path.getsize(tr["file"]) if os.path.exists(tr["file"]) else None
        tr["byte_start"] = start * SECTOR
        tr["byte_end"] = end * SECTOR if end is not None else size
    return tracks

def write_wav(path, pcm, rate, ch):
    with wave.open(path, "wb") as w:
        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm.tobytes())

def to_mono16k(st):
    from scipy.signal import resample_poly
    mono = st.reshape(-1, 2).astype(np.float32).mean(axis=1)
    out = resample_poly(mono, 160, 441)
    return np.clip(out, -32768, 32767).astype("<i2")

def parse_range(s):
    out = set()
    for part in s.split(","):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cue", nargs="?")
    ap.add_argument("--bin", action="append", default=[], help="raw audio track .bin (repeatable)")
    ap.add_argument("-o", "--outdir", default="build/audio")
    ap.add_argument("--tracks", help="e.g. 28-35 (cue mode)")
    ap.add_argument("--mono16k", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    jobs = []
    if a.cue:
        want = parse_range(a.tracks) if a.tracks else None
        for tr in parse_cue(a.cue):
            if tr["mode"] != "AUDIO" or (want and tr["num"] not in want):
                continue
            jobs.append((f"track{tr['num']:02d}", tr["file"], tr["byte_start"], tr["byte_end"]))
    for b in a.bin:
        m = re.search(r"(\d+)\D*$", os.path.basename(b).rsplit(".", 1)[0])
        name = f"track{int(m.group(1)):02d}" if m else os.path.splitext(os.path.basename(b))[0]
        jobs.append((name, b, 0, os.path.getsize(b)))
    if not jobs:
        ap.error("no audio tracks selected")
    for name, f, s, e in jobs:
        with open(f, "rb") as fh:
            fh.seek(s); raw = fh.read(e - s)
        raw = raw[: len(raw) // 4 * 4]
        pcm = np.frombuffer(raw, dtype="<i2")
        p = os.path.join(a.outdir, name + ".wav")
        write_wav(p, pcm, 44100, 2)
        msg = f"{p}: {len(pcm)//2/44100:.3f} s ({(e-s)//SECTOR} sectors)"
        if a.mono16k:
            q = os.path.join(a.outdir, name + "_16k.wav")
            write_wav(q, to_mono16k(pcm), 16000, 1); msg += f", {q}"
        print(msg)

if __name__ == "__main__":
    main()
