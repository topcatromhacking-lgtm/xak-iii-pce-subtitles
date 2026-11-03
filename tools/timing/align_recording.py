#!/usr/bin/env python3
"""Find where a CD-DA track plays inside an emulator/console recording and fit
recording_time = offset + rate * cd_time by cross-correlating several windows.

  python3 tools/timing/align_recording.py capture.mov build/audio/track28_16k.wav
Prints the per-window match (normalised cross-correlation) and the linear fit.
Mednafen 1.32 headless (-qtrecord) gives rate 1.000000 for Track 28; Paul's
capture card earlier gave 1.00875 (docs/timing.md).
"""
import argparse, subprocess, tempfile, wave
import numpy as np
from scipy.signal import fftconvolve, resample_poly

SR = 4000


def load(path):
    if not path.endswith('.wav') or True:
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', path, '-vn', '-ac', '1', '-ar', '16000', tmp], check=True)
        path = tmp
    w = wave.open(path)
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    return resample_poly(x, SR, w.getframerate())


def best(hay, seg):
    c = fftconvolve(hay, seg[::-1], 'valid'); i = int(np.argmax(c))
    n = np.sqrt(np.sum(hay[i:i + len(seg)] ** 2) * np.sum(seg ** 2)) or 1
    return i, float(c[i] / n)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('recording'); ap.add_argument('track_wav')
    ap.add_argument('--probe', type=float, default=2.0, help='track time of the coarse probe window (s)')
    ap.add_argument('--win', type=float, default=10.0)
    ap.add_argument('--step', type=float, default=30.0)
    a = ap.parse_args()
    rec, trk = load(a.recording), load(a.track_wav)
    W = int(a.win * SR)
    i, r = best(rec, trk[int(a.probe * SR):int(a.probe * SR) + W])
    off0 = i / SR - a.probe
    print(f'coarse: track starts at recording {off0:.3f} s (ncc {r:.3f})')
    pts = []
    for t in np.arange(a.probe, len(trk) / SR - a.win, a.step):
        lo = max(0, int((off0 + t - 5) * SR)); hay = rec[lo:lo + W + 10 * SR]
        if len(hay) < W: break
        j, r = best(hay, trk[int(t * SR):int(t * SR) + W])
        print(f'  cd {t:7.2f} -> rec {(lo + j) / SR:9.3f}  ncc {r:.3f}')
        if r > 0.5: pts.append((t, (lo + j) / SR))
    if len(pts) >= 2:
        p = np.polyfit(*np.array(pts).T, 1)
        print(f'fit: recording = {p[1]:.4f} + {p[0]:.6f} * cd_time  ({len(pts)} windows)')


if __name__ == '__main__':
    main()
