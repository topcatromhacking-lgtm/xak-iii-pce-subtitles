# Pilot 01: Track 28 waveform aligned to real gameplay recording

**2026-10-20 — verification of audio/timebase only, not a subtitle engine.**

The user-supplied Japanese disc `Track 28` is raw CD-DA, 44.1 kHz, signed 16-bit stereo. It contains **14,364 sectors × 2,352 bytes = 33,784,128 bytes**, exactly **191.520 seconds**. SHA-256: `66adab4f9504d6cb14aad462bf49115d234c14c84b5f5fced74fcd9c5c6e9959`.

We correlated that audio with the user's original Geargrafx 216.2-second screen recording of King Wavis's scene, converting both audio streams to mono at 8 kHz and comparing overlapping five-second windows.

**36 of 37** sampled windows met the minimum local-correlation threshold.

- **Screen recording time = 13.064345 + 1.00875018 × CD Track 28 time** (seconds).
- Linear fit R² **0.999999713**.
- Mean absolute residual **0.0242 seconds**, max **0.0564 seconds**.
- Recording playback is approximately **0.875% slower** than nominal CD time.
- Track audio 00:00 maps to recording **00:13.064**.
- Track audio 03:11.520 maps to recording **03:26.260**.

This establishes that the actual uploaded audio is present throughout the gameplay recording, independently of the previously identified CD track number in Geargrafx save states.

### First visual landmark conversions (not spoken-line boundaries)

| Visual scene element | Approximate CDDA time |
| --- | --- |
| Wide throne-room shot | 00:00.9–00:07.9 |
| King Wavis close-up | 00:21.7–00:31.7 |
| Pixie appears | 00:31.7–00:40.6 |
| General Beluga | 00:49.5–00:59.4 |
| Magician close-up | 01:21.2–01:37.0 |
| Final Pixie scene | around 02:59–03:04 |

These are **approximate picture landmarks**, not voice onsets, and cannot be inserted as final subtitle timestamps. The existing fan-translated dialogue for this scene is discussed at [Ys Utopia](https://www.ysutopia.net/forums/index.php?topic=205.0); its text should be carefully reviewed and not wholesale copied into this public repository without permission.

Use `tools/align_cdda_capture.py` with your own original Track 28 BIN and recording:

```sh
python -m pip install numpy scipy
python tools/align_cdda_capture.py --cdda "/private/Track28.bin" --capture "/private/cutscene.mp4" --out "/private/alignment.json"
python -m unittest discover -s tests -p "test_align_cdda_capture.py" -v
```

**Next engineering gate:** identify safe cutscene code execution/rendering hook in the 192-KiB overlay and time one independently reviewed English line to the **CD track clock**, keeping Japanese voices unchanged. Neither the recording nor CD audio, screenshots, copied dialogue, states or proprietary disc sectors belong in this public repo.
