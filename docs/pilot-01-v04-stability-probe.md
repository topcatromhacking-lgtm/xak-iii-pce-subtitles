# Xak III Pilot 01 v0.4 — stable in-picture subtitle probe

**2026-10-21. Offline-generated source; not yet Geargrafx-validated.**

## Proven v0.3 milestone

The first actually visible text appears in Geargrafx v44 `state3` 14.4305 s into physical Track 28. Capture shows `SUB TE` inside the picture, but the lower edge of the character portrait is visibly corrupted. The hook at `$8EE5 -> $9C00`, four sprite entries in live/DMA SAT, and native `STZ $3444` cleanup are verified.

## Root-cause candidate

In v0.3, two of the four repeatedly uploaded 16x16 sprite patterns occupy VDC1 VRAM words `$0780` and `$07C0`. The scene's VDC MWR is `$0050`, setting a 64x64 background-attribute-table (BAT). Those addresses therefore also cover background map rows **30 and 31**. Forced overwrites of these words plausibly explain the visible picture corruption. Patterns **43 and 56** survive later scene snapshots; **57 and 58** are zero in the observed early/later states. This is scene-specific evidence, not guaranteed ownership throughout the game.

## v0.4 controlled test

The source-only v0.4 builder requires exact v0.3 raw Track 02 SHA-256 `d87e285018b89416f18bfdc6c9af10e2251aa3234170383deefdcbc6616f0b32` and accompanying 35-track v0.3 split CUE. It generates uniquely named v0.4 files without overwriting v0.3.

1. Restore first-invocation font guard at CPU `$9C08` from `EA EA` to `D0 41` (one-time 512-byte upload).
2. Relocate glyphs to sprite patterns **43, 56, 57, 58**, VRAM words `$0AC0, $0E00, $0E40, $0E80`.
3. Update all four SAT2 indices to `$56, $70, $72, $74`.
4. Retain v0.3's visible screen Y=128, game-native sprite writer and counter reset.
5. Regenerate and verify raw MODE1 EDC/ECC. **Only Track 02 sector 745 changes**; Japanese CDDA remains untouched.
6. Assign the **new v0.4 CUE name** to keep its five Geargrafx save slots separate. Auto-copy the pinned clean v0.3 military-camp Slot 1 where present in the CUE folder.

Seven local offline tests pass, including a full-size synthetic Track 02, IPS roundtrip, exact-byte guards and sector checksum. This does **not** establish working emulator rendering.

## Next Geargrafx checkpoint

Boot v0.4 clean camp Slot 1, enter King Wavis's scene, observe 10–20 seconds. Test whether the white `SUB TEST` is complete and whether the character portrait is free of corruption. Save Slot 3 under the v0.4 CUE namespace. If stable, proceed to final text layout and one synchronized English line; otherwise inspect BAT and SAT without abandoning v0.3 rollback.

Conceptual precedents: [Yuna](https://github.com/suppertails66/yunatools/blob/master/yuna/asm/overlay/scene.s), [Yuna 2](https://github.com/suppertails66/yuna2tools/blob/master/yuna2/asm/scene_main.s), [Emerald Dragon](https://github.com/suppertails66/emdrtools/blob/master/emdr/asm/generic/scene/scene_std.s).

No copyrighted game media or private states should be committed.
