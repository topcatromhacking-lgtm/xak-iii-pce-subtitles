#!/usr/bin/env python3
"""Self-test for the timing tools without game audio: builds a synthetic
'cinema track' (music bed + speech-like bursts at known times) as a Redump-style
BIN/CUE, runs extract_audio_tracks.py and vad_cues.py, and checks the boundaries
are within 0.25 s. Usage: python3 tools/timing/selftest_synth.py"""
import os, subprocess, sys, tempfile
import numpy as np
from scipy.signal import butter, sosfilt
HERE = os.path.dirname(os.path.abspath(__file__))
SR = 44100
TRUTH = [(1.5, 3.2), (4.0, 6.6), (7.3, 8.1), (9.4, 12.5), (13.4, 15.0), (16.2, 18.9)]
rng = np.random.default_rng(1)
dur = 21.0; t = np.arange(int(dur * SR)) / SR
music = sum(0.08 * np.sin(2 * np.pi * f * t) for f in (110, 165, 220, 277, 330))
music *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * t)
kick = (np.exp(-((t % 0.5) * 30)) * np.sin(2 * np.pi * 60 * t)) * 0.25
music = music + kick + 0.02 * sosfilt(butter(4, 2000, "low", fs=SR, output="sos"), rng.standard_normal(t.size))
voice = np.zeros_like(t)
for a, b in TRUTH:
    m = (t >= a) & (t < b); tt = t[m] - a
    f0 = 180 + 40 * np.sin(2 * np.pi * 0.7 * tt)
    ph = 2 * np.pi * np.cumsum(f0) / SR
    harm = sum(np.sin(k * ph) / k for k in range(1, 18))
    noise = rng.standard_normal(tt.size) * 0.3
    s = sosfilt(butter(4, [300, 3400], "band", fs=SR, output="sos"), harm + noise)
    env = (0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 2.3 * tt))) * np.minimum(1, np.minimum(tt, b - a - tt) / 0.03)
    voice[m] = 0.25 * s * env
x = music + voice
pcm = np.clip(np.stack([x, x], 1) * 32767, -32768, 32767).astype("<i2")
d = tempfile.mkdtemp()
data = os.path.join(d, "fake (Track 01).bin"); aud = os.path.join(d, "fake (Track 02).bin")
open(data, "wb").write(b"\0" * 2352 * 10)
raw = pcm.tobytes(); raw += b"\0" * (-len(raw) % 2352)
open(aud, "wb").write(b"\0" * 2352 * 150 + raw)       # 2 s pregap (INDEX 00)
open(os.path.join(d, "fake.cue"), "w").write(
    'FILE "fake (Track 01).bin" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\n'
    'FILE "fake (Track 02).bin" BINARY\n  TRACK 02 AUDIO\n    INDEX 00 00:00:00\n    INDEX 01 00:02:00\n')
py = sys.executable
subprocess.run([py, os.path.join(HERE, "extract_audio_tracks.py"), os.path.join(d, "fake.cue"), "-o", d, "--mono16k"], check=True)
out = subprocess.run([py, os.path.join(HERE, "vad_cues.py"), os.path.join(d, "track02_16k.wav"), "--no-fit"],
                     check=True, capture_output=True, text=True).stdout
print(out)
segs = [tuple(map(float, l.split()[1:3])) for l in out.splitlines() if l.startswith("  ")]
assert len(segs) == len(TRUTH), f"found {len(segs)} segments, want {len(TRUTH)}"
err = max(max(abs(a - c), abs(b - e)) for (a, b), (c, e) in zip(segs, TRUTH))
print(f"max boundary error {err:.3f} s"); assert err < 0.25
print("TIMING SELFTEST OK")
