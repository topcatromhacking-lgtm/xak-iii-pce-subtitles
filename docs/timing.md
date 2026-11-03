# Cue timing workflow

Tools live in `tools/timing/`. They need Paul's own disc dump. Nothing is downloaded.

1. Extract the cinema tracks (VS1=28, VS4=29, VS7=30|35?, VS2=31, VS3=32, VS5=33, VS6=34):

       python3 tools/timing/extract_audio_tracks.py "/path/Xak III (Japan).cue" \
           -o build/audio --tracks 28-35 --mono16k

   Each track's audio starts at INDEX 01 (pregap skipped), which is what
   the game's CD play command seeks to. Output is a 44.1 kHz stereo WAV plus a 16 kHz mono WAV for VAD.
2. Propose timings for one scene and write Audacity labels for review:

       python3 tools/timing/vad_cues.py build/audio/track28_16k.wav --scene VS1 \
           --labels build/timing/VS1_labels.txt

   The detector scores dB in the speech band (300–3400 Hz) above a rolling
   8 s music floor, plus speech-band share and onset flux. It applies hysteresis, a minimum length,
   gap merging and padding, then fits the segments to the scene's cue count
   (merge the nearest gaps, or split the longest segment).
3. Open the track WAV in Audacity, import the labels, and fix boundaries/order.
   Export the labels, then:

       python3 tools/timing/vad_cues.py --from-labels VS1_fixed.txt --scene VS1 --write

4. `python3 tools/lint_script.py` checks overlaps, durations and reading speed (≤ 17 cps).
5. Runtime key = round((t − play_latency) × 59.826) frames. Measure play_latency
   per scene on hardware (`align_cdda_capture.py`).

Self-test without game audio: `python3 tools/timing/selftest_synth.py` builds
a synthetic BIN/CUE (music bed + 6 speech-like bursts), extracts it, runs VAD,
and checks every boundary is within 0.25 s. Current result: 0.12 s max error, which is the padding.
Real Xak III audio has music under the voice, so expect to tune `--hi/--lo`.
