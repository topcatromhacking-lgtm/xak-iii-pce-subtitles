# Xak III: The Eternal Recurrence — PC Engine CD English Subtitles

Research project to add timed **English subtitles** to the original Japanese-voiced PC Engine CD cutscenes of *Xak III*. **Subtitling, not dubbing:** preserve Japanese voice acting, CD audio, animation and gameplay.

## Current status (October 24, 2026)

**The King Wavis subtitle renderer now works from the beginning of his first spoken dialogue in Geargrafx's v0.9 save-state experiment.** We retain the original Japanese CD-DA Track 28 and the existing NightWolve English gameplay translation. The on-screen `SUB TEST` is a rendering diagnostic, **not yet a synchronized English dialogue subtitle**.

- **v0.5: real emulator success.** Moving `SU` to VRAM sprite pattern 59 fixed the permanent glyph corruption; the other three glyphs survived throughout sampled late-scene checkpoints.
- **v0.6–v0.7: negative experiments.** Four test heights and a background-tile overlay did not make early King subtitles visible. These experiments identified raster display control as the correct target.
- **v0.8: real emulator success.** A one-byte saved-code experiment showed that the game's native raster routine deliberately disables sprites in the King's early background-only bands.
- **v0.9: real emulator success, user reports “All good.”** A same-bank 10-byte helper enables sprites only where the native background raster band is enabled, retaining clean black borders and normal animation/audio.
- **v0.10: source-only disc-native builder ready, real clean-boot test pending.** The guarded builder maps the v0.9 code to raw Track02 sectors **738 and 740**, regenerates both MODE1 EDC/ECC sets, checks exact 15-byte executable edits and confirms an IPS round-trip. **Twelve synthetic tests pass.** It uses the user-owned exact v0.5 data BIN and produces a new v0.10 BIN/CUE/IPS/report and optional verified camp Slot 1. No game data or audio is distributed.

**Next gate:** the user builds v0.10 locally and loads the clean camp save, then watches the complete royal-audience sequence. If the new disc patch survives the scene, begin implementing timed English spoken-line captions on the verified rendering pipeline.

Technical details: [v0.10 sector mapping and test](docs/pilot-01-v10-disc-selective-raster-build.md), [v0.9 selective raster probe](docs/pilot-01-v09-selective-raster-probe.md), [v0.8 root cause](docs/pilot-01-v08-king-raster-sprite-enable-root-cause.md), [v0.5 runtime result](docs/pilot-01-v05-verified-early-speech-gap.md). Current repository source: [v0.10 builder](tools/build_xak_iii_v10_disc_raster.py), [MODE1/IPS utility module](tools/xak_iii_disc_utils.py), [regression tests](tests/test_xak_iii_v10_disc_raster.py).

The separate [Xak I & II reference translation](https://github.com/randomprojectsfactory/xak-i-ii-pce-english) demonstrates completed subtitling on related hardware, but the current Xak III fix was found **independently in native Xak III raster code**. No external comments or outreach will be made without the user's prior approval.

## Reproduce the English Track 02 reconstruction

Use your own original Japanese 35-track disc image and an authorized copy of the English translation patch containing Xak3BINB.ppf and Xak3ISOB.ppf. None of those game or patch files is included in this repository.

    python tools/rebuild_english_track02.py \
      --japanese-track "/private/Xak III - The Eternal Recurrence (Japan) (Track 02).bin" \
      --bin-ppf "/private/Xak3BINB.ppf" \
      --iso-ppf "/private/Xak3ISOB.ppf" \
      --out "/private/Xak_III_English_Track02_Reconstructed.bin" \
      --report "/private/verification.json"

This reconstruction checks pinned input and patch SHA-256 values, output SHA-256, original pregap, raw sector headers and data agreement between the two independent PPF formats. It does not modify the original Japanese track. Its output is **not a complete playable disc** without the other 34 tracks.

To generate a corresponding split-track CUE that reuses the original Japanese audio tracks:

    python tools/make_split_cue.py \
      --japanese-cue "/private/Xak III - The Eternal Recurrence (Japan).cue" \
      --out "/private/Xak_III_English_Split_Track.cue"

Put the replacement Track 02 and the original other tracks together in the same directory when testing in an emulator.

## Research direction

Map actual cutscene/voice triggers, locate existing English text rendering, hook a single cutscene to display one subtitle, validate synchronized playback, then build out the remaining dialogue. Study [Galaxy Fraulein Yuna tools](https://github.com/suppertails66/yunatools), [Yuna 2 tools](https://github.com/suppertails66/yuna2tools) and [Emerald Dragon tools](https://github.com/suppertails66/emdrtools) as references, not ready-made drop-in Xak III patches.

## Public repository safety

This repository is **public**. Its [.gitignore](.gitignore) excludes BIN/CUE/ISO/CHD disc images, music and voices, third-party PPFs and archives, save states, local workspaces and generated output. **Gitignore does not hide anything already committed.** Never force-add copyrighted source media, the translated BIN or somebody else's patch payloads; use your ignored /private or /work directories. Only original tools, research notes and legally distributable patches belong here.

The existing English translation package credits NightWolve, Paul England and Akimaru. No ownership, permission to redistribute their patches, or rights to the Japanese game are asserted here.
