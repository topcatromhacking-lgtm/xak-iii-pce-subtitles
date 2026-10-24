# Xak III: The Eternal Recurrence — PC Engine CD English Subtitles

Research project to add timed **English subtitles** to the original Japanese-voiced PC Engine CD cutscenes of *Xak III*. **Subtitling, not dubbing:** preserve Japanese voice acting, CD audio, animation and gameplay.

## Current status (October 24, 2026)

**v0.5 has achieved stable, visible `SUB TEST` glyphs in actual Geargrafx gameplay, while the first King Wavis spoken line remains visually unsubtitled.** The existing disc-native scene hook preserves NightWolve's English game translation and original Japanese voiced physical CD Track 28. A verified native v0.5 checkpoint at 74.30 and 130.00 seconds confirms glyph pattern 59 survives after the previous pattern-43 overwrite; patterns 56–58 remain intact.

**New early-voice evidence changes our diagnosis.** A native v0.5 state taken **exactly as the King begins speaking, 5.2873 seconds into Track 28**, proves that the **existing hook has already run**: first-use flag `$9C99=$00`, all four subtitle SAT entries in live and DMA shadow, all four glyph patterns intact, and white sprite palette `$01FF`. Nevertheless the captured screenshot has **no visible subtitle**. Therefore installing another early hook is **not presently justified**. The first-speech failure is in actual rendering/display or scene composition; a VBlank VDC control-register snapshot cannot establish behavior at subtitle scanlines.

**v0.6 source-only vertical-band diagnostic prepared (12 offline tests pass; no real emulator test yet):** move the same four glyph fragments to screen Ys 64, 88, 112 and 136 without changing v0.5's stable font, original sprite writer, Japanese audio or any other source data sector. Different visible/hidden fragments would identify whether the first King's scene masks selected raster bands or disables sprite output more broadly. A unique v0.6 CUE retains its own five Geargrafx save slots.

See [v0.6 early King and raster-band investigation](docs/pilot-01-v06-early-king-raster-band.md), [v0.5 verified runtime checkpoints](docs/pilot-01-v05-verified-early-speech-gap.md), [v0.5 glyph-lifetime design](docs/pilot-01-v05-glyph-lifetime.md), [Xak I & II comparative techniques](docs/xak-i-ii-subtitle-technique-comparison.md), [Disc research](docs/disc-foundation.md), and [Subtitle research plan](docs/subtitle-plan.md).

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
