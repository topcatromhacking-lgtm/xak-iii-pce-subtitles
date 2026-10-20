# Xak III: The Eternal Recurrence — PC Engine CD English Subtitles

Research project to add timed **English subtitles** to the original Japanese-voiced PC Engine CD cutscenes of *Xak III*. **Subtitling, not dubbing:** preserve Japanese voice acting, CD audio, animation and gameplay.

## Current status (October 2026)

**Verified disc-analysis foundation; no working subtitle patch yet.** The Japanese Track 02 and the NightWolve English translation's original PPF3 patches were compared. We reconstructed a split-track English data track and independently validated every indexed user-data sector against the ISO patch. No cutscene hook, voice-to-track mapping, subtitle display routine or runtime/emulator test has yet been validated.

See [Disc research](docs/disc-foundation.md), [Subtitle research plan](docs/subtitle-plan.md), and the [rebuild tool](tools/rebuild_english_track02.py).

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
