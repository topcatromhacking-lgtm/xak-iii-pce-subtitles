# Xak III: The Eternal Recurrence — PC Engine CD English Subtitles

Research project to add timed **English subtitles** to the original Japanese-voiced PC Engine CD cutscenes of *Xak III*. **Subtitling, not dubbing:** preserve Japanese voice acting, CD audio, animation and gameplay.

## Current status (October 24, 2026)

**v0.5 has achieved stable, visible `SUB TEST` glyphs in actual Geargrafx gameplay, while the first King Wavis spoken line remains visually unsubtitled.** The existing disc-native scene hook preserves NightWolve's English game translation and original Japanese voiced physical CD Track 28. A verified native v0.5 checkpoint at 74.30 and 130.00 seconds confirms glyph pattern 59 survives after the previous pattern-43 overwrite; patterns 56–58 remain intact.

**New early-voice evidence changes our diagnosis.** A native v0.5 state taken **exactly as the King begins speaking, 5.2873 seconds into Track 28**, proves that the **existing hook has already run**: first-use flag `$9C99=$00`, all four subtitle SAT entries in live and DMA shadow, all four glyph patterns intact, and white sprite palette `$01FF`. Nevertheless the captured screenshot has **no visible subtitle**. Therefore installing another early hook is **not presently justified**. The first-speech failure is in actual rendering/display or scene composition; a VBlank VDC control-register snapshot cannot establish behavior at subtitle scanlines.

**v0.6 real emulator test: negative.** The user reported that all four separately positioned glyph fragments at screen Ys 64, 88, 112 and 136 remained invisible during the King's opening and appeared only after the hero's first line. This argues against a simple fixed-Y crop, but the **exact scanline-time cause is not yet known**. A fresh read-only comparison of v0.5 states at 5.2873 and 129.9988 seconds confirmed identical saved VDC1 CR/latched CR, HDR, VDC2 CR, HuC6202 mixer settings, sprite palette and all four font bitmaps; four SAT subtitle entries are present at both times. These static frames cannot reveal per-line CR changes. The next diagnostic uses Geargrafx's VDC hardware **Trace Logger**, **not another game patch**; v0.5 remains the stable baseline with its five state slots.

**Contemporary reference found (October 24):** the developer/thread behind the October 2026 [Xak I & II subtitle patch](https://github.com/randomprojectsfactory/xak-i-ii-pce-english) reports an **experimental working Xak III subtitle approach** and approximately 30 voiced dialogues to cover. This is not yet a public Xak III source release. An [existing issue requesting Xak III subtitles](https://github.com/randomprojectsfactory/xak-i-ii-pce-english/issues/2) was opened the same day. We will prioritize examining or obtaining those technical methods before more speculative patches, while retaining v0.5 as the stable rollback. See [direct prototype lead and outreach questions](docs/xak-iii-existing-subtitle-prototype-lead-2026-10-24.md).

**Direct implementation investigation (October 24):** We posted a technical question from TopCat to the developer of the [Xak I & II English patch](https://github.com/randomprojectsfactory/xak-i-ii-pce-english/issues/2#issuecomment-6390071301), who reports experimental Xak III subtitles. Separately, we decoded the VCDIFF/LZMA structure of their **Track 02 (7,025-byte)** and **Track 05 (293,217-byte)** xdelta releases and published a checksum-verifying, read-only [reference patch analyzer](tools/analyze_xak_i_ii_reference_xdelta.py) with synthetic tests. The original Japanese Xak I & II data tracks are still necessary to reconstruct and disassemble the modified runtime code; **no transferable engine source has been acquired yet**. See [findings and outreach](docs/xak-i-ii-vcdiff-reverse-engineering-and-outreach.md).

**v0.7 alternate-layer experiment (October 24):** after reviewing Xak I & II's actual black-band subtitle presentation, we created a **save-state-only VDC1 BG/BAT tile probe** from the real v0.5 early King state. Five white 8×8 background glyphs and four candidate `SUB TEST` tile rows test whether the game's background layer remains visible when our sprite subtitle layer is hidden. The offline verified private state4 differs by **196 VDC1 VRAM bytes only**; it leaves the working v0.5 CUE/BIN, audio, original states and embedded thumbnail unchanged. The [reversible builder](tools/build_xak_iii_v07_bg_tile_state_probe.py) and [synthetic tests](tests/test_xak_iii_v07_bg_tile_state_probe.py) are public, while the user-derived native state file remains private. **Actual emulator rendering is not yet tested.** See [v0.7 black-band investigation](docs/pilot-01-v07-black-band-bg-state-test.md).

**Raster visibility breakthrough (October 24):** The real v0.7 background-tile experiment did not produce new visible text. Further read-only investigation of the original v0.5 King state identified native HuC6280 code at **bank81:$65A7**: `LDA $233D; AND #$3F; ORA $3E72,X; ST0 #$05; STA $0002`. At the first King's line the game's raster table has **16 active $80 entries (BG only)**; in later visible shots those entries are **$C0 (BG + sprites)**. This explains why the hook, SAT, font and stored CR can all be correct while subtitles are invisible early. We now have a **one-byte save-state-only v0.8 probe**, temporarily preserving sprite bit $40 by changing `AND #$3F` to `AND #$7F` in loaded CD RAM. The unchanged v0.5 BIN and audio are used through a unique v0.8 CUE/save namespace. Nine local checks passed; real emulator result pending. This may expose native sprites in intentionally blank bands; it is diagnostic, not the final per-line fix. See [evidence and safe test](docs/pilot-01-v08-king-raster-sprite-enable-root-cause.md), [builder](tools/build_xak_iii_v08_raster_sprite_enable_state.py), and [synthetic regression tests](tests/test_xak_iii_v08_raster_sprite_enable_state.py).

See [v0.6 negative test and trace plan](docs/pilot-01-v06-negative-raster-trace-plan.md), [v0.6 early King and raster-band investigation](docs/pilot-01-v06-early-king-raster-band.md), [v0.5 verified runtime checkpoints](docs/pilot-01-v05-verified-early-speech-gap.md), [v0.5 glyph-lifetime design](docs/pilot-01-v05-glyph-lifetime.md), [Xak I & II comparative techniques](docs/xak-i-ii-subtitle-technique-comparison.md), [Disc research](docs/disc-foundation.md), and [Subtitle research plan](docs/subtitle-plan.md).

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
