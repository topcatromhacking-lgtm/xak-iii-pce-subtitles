#!/usr/bin/env python3
"""Match a raw 44.1-kHz stereo CD-DA track against a gameplay video.

Read only; ffmpeg + numpy + scipy required. Timing anchors do not identify
individual voiced lines. Never publish extracted game audio or source videos.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from scipy import signal, stats


def decode_mono_8k(path, raw_cdda):
    args = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error"]
    if raw_cdda:
        args += ["-f", "s16le", "-ar", "44100", "-ac", "2"]
    args += ["-i", str(path), "-vn", "-f", "s16le", "-ac", "1", "-ar", "8000", "-"]
    data = subprocess.run(args, check=True, capture_output=True).stdout
    return np.frombuffer(data, dtype="<i2").astype(np.float32) / 32768


def fit_alignment(track, captured, *, start_guess=13.0, rate_guess=1.009,
                  rate=8000, step_seconds=5, window_seconds=5, search_seconds=2.0):
    if not len(track) or not len(captured):
        raise ValueError("Empty audio input")
    if rate < 1000:
        raise ValueError("Sampling rate too low")
    sos = signal.butter(3, [250, min(2400, 0.45 * rate)],
                        btype="bandpass", fs=rate, output="sos")
    stride = max(1, rate // 2000)
    a = signal.sosfilt(sos, track)[::stride]
    b = signal.sosfilt(sos, captured)[::stride]
    fps = rate / stride
    window_size = round(window_seconds * fps)
    anchors = []
    for t in np.arange(step_seconds, len(a) / fps - window_seconds, step_seconds):
        start = round(t * fps)
        reference = a[start:start + window_size]
        predicted = start_guess + rate_guess * t
        lo = max(0, round((predicted - search_seconds) * fps))
        hi = min(len(b), round((predicted + window_seconds + search_seconds) * fps))
        region = b[lo:hi]
        if len(reference) != window_size or len(region) < window_size:
            continue
        scores = signal.fftconvolve(region, reference[::-1], mode="valid")
        peak = int(np.argmax(np.abs(scores))) + lo
        observed = b[peak:peak + window_size]
        if np.std(reference) < 1e-9 or np.std(observed) < 1e-9:
            continue
        anchors.append({"track_seconds": float(t), "capture_seconds": peak / fps,
                        "correlation": float(np.corrcoef(reference, observed)[0, 1])})
    accepted = [x for x in anchors if abs(x["correlation"]) >= 0.09 and
                abs(x["capture_seconds"] -
                    (start_guess + rate_guess * x["track_seconds"])) <= search_seconds]
    if len(accepted) < 6:
        raise RuntimeError("Not enough reliable audio matches to fit an alignment")
    fit = stats.linregress([x["track_seconds"] for x in accepted],
                           [x["capture_seconds"] for x in accepted])
    errors = [abs(x["capture_seconds"] -
                  (fit.intercept + fit.slope * x["track_seconds"])) for x in accepted]
    return {
        "intercept_seconds": float(fit.intercept),
        "capture_seconds_per_track_second": float(fit.slope),
        "r_squared": float(fit.rvalue ** 2),
        "mean_absolute_residual_seconds": float(np.mean(errors)),
        "max_absolute_residual_seconds": float(max(errors)),
        "accepted_anchors": accepted,
        "matched_windows": len(accepted),
        "total_windows": len(anchors),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cdda", type=Path, required=True)
    p.add_argument("--capture", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--guess-offset", type=float, default=13.0)
    p.add_argument("--guess-speed", type=float, default=1.009)
    a = p.parse_args()
    if a.out.exists() or a.out.resolve() in (a.cdda.resolve(), a.capture.resolve()):
        p.error("Refusing to overwrite an existing file or input")
    track = decode_mono_8k(a.cdda, True)
    video = decode_mono_8k(a.capture, False)
    report = fit_alignment(track, video, start_guess=a.guess_offset,
                           rate_guess=a.guess_speed)
    report.update(
        cdda_seconds=len(track) / 8000,
        capture_seconds=len(video) / 8000,
        cdda_sha256=hashlib.sha256(a.cdda.read_bytes()).hexdigest(),
        capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest(),
        formula="capture_seconds = intercept_seconds + capture_seconds_per_track_second * cdda_seconds",
        warning="Acoustic anchors, not spoken-line start/end times",
    )
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "accepted_anchors"}, indent=2))


if __name__ == "__main__":
    main()
