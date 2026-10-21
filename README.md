# Xak III: The Eternal Recurrence — PC Engine CD English Subtitles

Research project to add timed **English subtitles** to the original Japanese-voiced PC Engine CD cutscenes of *Xak III*. **Subtitling, not dubbing:** preserve Japanese voice acting, CD audio, animation and gameplay.

## Current status (October 21, 2026)

**Disc reconstruction, physical Track 28 audio timing and a disc-native cutscene hook are verified. No working on-screen subtitle yet.** The NightWolve English Track 02 has been independently reconstructed and verified against the original PPF3 patches. The King Wavis royal-audience scene plays physical CD Track 28; a real Geargrafx save confirms v0.2's `$8EE5 -> $9C00` hook executes and the injected subtitle sprites enter the native SAT path. However the tester does **not** see `SUB TEST`: two font patterns were overwritten in a later 14.43-second checkpoint and the remaining sprite visibility is unresolved.

A **source-only v0.3 visibility diagnostic** has been built and passed five synthetic/offline checks, but it has **not** been run successfully in Geargrafx. It refreshes glyph graphics each scene-loop call and tests visibility inside the active picture. This is a reversible experiment, not synchronized subtitle support.

See [v0.3 visibility probe](docs/pilot-01-v03-visibility-probe.md), [v0.2 runtime checkpoint](docs/pilot-01-v02-first-runtime-checkpoint.md), [Disc research](docs/disc-foundation.md), [Subtitle research plan](docs/subtitle-plan.md), and the [rebuild tool](tools/rebuild_english_track02.py).

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
