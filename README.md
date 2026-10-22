# Xak III: The Eternal Recurrence — PC Engine CD English Subtitles

Research project to add timed **English subtitles** to the original Japanese-voiced PC Engine CD cutscenes of *Xak III*. **Subtitling, not dubbing:** preserve Japanese voice acting, CD audio, animation and gameplay.

## Current status (October 21, 2026)

**Actual, readable `SUB TEST` has been rendered during the King Wavis cinematic in Geargrafx; synchronized English dialogue is not yet implemented.** The NightWolve English Track 02 has been reconstructed and independently verified against the original PPF3 patches. The first King Wavis scene plays physical CD Track 28. The disc-native `$8EE5 -> $9C00` cutscene hook runs and inserts subtitle sprites into the game's native SAT path without modifying Japanese CD audio.

**v0.4.1 runtime breakthrough:** Five authentic Geargrafx v44 states and a 230-second video establish that all four glyphs appear correctly at 14.46 seconds into Track 28. At 32.33 seconds, the first `SU` glyph (VRAM pattern 43) has been overwritten while the other three survive unchanged; the damage persists at 72.58 seconds. Separately, the scene's VDC HDR switches from `$0C0F` (128px picture) to `$041F` (256px picture), shifting the apparent subtitle position.

**v0.5 source-only glyph-stability experiment prepared:** Move just the damaged `SU` glyph to pattern 59, observed empty in all three captured cinematic checkpoints. Eleven synthetic/offline tests pass; **v0.5 has not yet been validated in Geargrafx**. A later revision will address the changing video width and real timed spoken-line subtitles.

See [v0.5 glyph-lifetime analysis](docs/pilot-01-v05-glyph-lifetime.md), [v0.4.1 centered/mask probe](docs/pilot-01-v041-centered-mask-probe.md), [v0.3 first visible sprite probe](docs/pilot-01-v03-visibility-probe.md), [v0.2 runtime checkpoint](docs/pilot-01-v02-first-runtime-checkpoint.md), [Disc research](docs/disc-foundation.md), [Subtitle research plan](docs/subtitle-plan.md), and the [rebuild tool](tools/rebuild_english_track02.py).

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
