# Xak III: The Eternal Recurrence — PC Engine CD English Subtitles

Research project to add timed **English subtitles** to the original Japanese-voiced PC Engine CD cutscenes of *Xak III*. **Subtitling, not dubbing:** preserve Japanese voice acting, CD audio, animation and gameplay.

## Current status (October 24, 2026)

**The King Wavis subtitle renderer now works from the beginning of his first spoken dialogue in Geargrafx's v0.9 save-state experiment.** We retain the original Japanese CD-DA Track 28 and the existing NightWolve English gameplay translation. The on-screen `SUB TEST` is a rendering diagnostic, **not yet a synchronized English dialogue subtitle**.

- **v0.5: real emulator success.** Moving `SU` to VRAM sprite pattern 59 fixed the permanent glyph corruption; the other three glyphs survived throughout sampled late-scene checkpoints.
- **v0.6–v0.7: negative experiments.** Four test heights and a background-tile overlay did not make early King subtitles visible. These experiments identified raster display control as the correct target.
- **v0.8: real emulator success.** A one-byte saved-code experiment showed that the game's native raster routine deliberately disables sprites in the King's early background-only bands.
- **v0.9: real emulator success, user reports “All good.”** A same-bank 10-byte helper enables sprites only where the native background raster band is enabled, retaining clean black borders and normal animation/audio.
- **v0.10: real clean-scene Geargrafx success.** The user confirmed the marker appears from the start of the cinematic, before the King's speech, and that previous black-square occlusion has been eliminated. Disc-native selective raster code was limited to sectors 738 and 740; MODE1 EDC/ECC and an IPS round-trip passed.
- **v0.11: prebuilt separate black-band save-state diagnostic, Geargrafx result pending.** This reuses the existing v0.10 game disc and briefly enables sprites in background-blanked bands, moving the eight-letter marker into two lines at native Y184 and Y204. Nine tests passed; unsafe as a general solution until native-sprite bleeding is ruled out. [Details and first historical Track28 caption plan](docs/pilot-01-v11-black-band-first-caption-plan.md).

**v0.11 is the preferred black-band presentation and remains the visual baseline.** Ten real Geargrafx frames confirmed readable two-line subtitles around native Y184/Y204 in most widescreen shots. Three narrower scenes shift the text horizontally by **+64 pixels** (measured left edge X113 → X177); three scenes reveal native hero/pixie/mouth sprites when v0.11 disables lower-band sprite masking. Its global sprite-enable is experimental, not a final release.

**v0.12 failed in real emulator testing.** Turning on the native background instead uncovered duplicate picture art and coloured graphics in the black band. The untested v0.13 raster-background phase experiments are set aside; neither replaces the user's preferred v0.11 design.

**v0.14 now ready for real Geargrafx centering test.** Private standalone ZIP \`Xak_III_v14_v11_Letterbox_Centering_AB_Ready_To_Test.zip\` contains the original v0.11 two-line sprite renderer in an isolated v0.14 CUE and four saved states: Slot2 original X, Slot3 X−48, **Slot4 X−64**, Slot5 X−80. All share the v0.10 data BIN and unchanged 34 Japanese audio tracks. Exactly four saved CD-RAM coordinate bytes differ in each shifted variant; no font, Y-coordinate, raster, native SAT, game-disc or audio changes. **15 synthetic tests passed and authentic pinned state was transformed and validated; actual v0.14 emulator outcome is pending.** [Findings](docs/pilot-01-v14-v11-letterbox-geometry-ab.md), [source builder](tools/build_xak_iii_v14_letterbox_geometry.py), [read-only wide/narrow comparator](tools/analyze_xak_iii_v14_two_scenes.py), [regression tests](tests/test_xak_iii_v14_letterbox_geometry.py).

**v0.14 Slot 4 — user-confirmed success (25 October):** The user explicitly confirmed that the six new screenshots are all from **v0.14 Slot 4** (X−64), and that subtitles are correctly placed even in narrower 4:3 scenes. No new graphical glitches were reported. The six remaining exceptions are **original native sprite pixels escaping the letterbox**: pixie's body/lower body, hero legs, a stray upper-right mouth, and a walking NPC's lower half. The four-column text/X experiment is finished; **do not alter the successful Slot 4 layout again.** See [v0.14 confirmation and v0.15 plan](docs/pilot-01-v14-slot4-confirmed-v15-native-sat-plan.md).

**v0.15 SAT clipping research (source-only, actual glitch save needed):** We have a [fail-closed saved-state SAT isolation builder](tools/build_xak_iii_v15_native_sat_isolation.py) and [12 synthetic regression tests](tests/test_xak_iii_v15_native_sat_isolation.py), plus a private downloadable source ZIP. From one actual glitch-frame v0.14 Slot 4 checkpoint, it creates reference and three native-only suppression modes, without touching program code, subtitle SAT entries, v0.10 BIN or Japanese audio. This is strictly a short-duration root-cause test; SAT redraws may erase the change. The user should preserve Slots 2–5 and capture an actual glitch in **v0.14 Slot 1** for analysis.

**Next engineering gate:** identify a reliable *runtime* indicator of the narrower scene from paired Geargrafx states, so the 64px correction is applied only when needed, then identify and selectively suppress the native sprites exposed below the picture. Preserve v0.10 as the verified disc-level rollback. Only afterward begin timed King Wavis dialogue.

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
