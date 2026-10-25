# Pilot 01 v0.14 — v0.11 letterbox preservation + measured 4:3 correction

**2026-10-25 — emulator test pending.**

## User choice

The user explicitly selected **v0.11** as the best black-band visual baseline, especially in most widescreen shots. Do **not** promote v0.12 or the untested v0.13 background-layer probes into the production disc. The verified disc rollback remains **v0.10**, whose native raster fix allowed first-King-dialogue `SUB TEST` to render from a clean scene entry.

## Direct pixel observations

The user provided ten 256×240 authentic Geargrafx v0.11 screenshots. Measuring **white subtitle pixels in lower native rows 180–221** reveals:

- Seven normal widescreen frames: `SUB / TEST` bbox left **X=113**, right 141, Y=189–215.
- Three narrowed/cropped frames (screens #3, #5, #7): visible text bbox left **X=177**, right 189, Y=189–215. Part of the text is clipped at the picture edge.
- Displacement **+64 pixels**. This is a **measured on-screen translation**, **not yet an identified hardware-register cause**. We must not infer from it alone that VDC HDR, VPC window, or HSR controls the offset.

Separate failure: v0.11 removes raster sprite blanking throughout previously black lines. This exposes parts of hero/pixie sprites in frames #6–7 and a moving mouth in #10. These are native sprites; v0.12's background-only variant re-exposes artwork in the black band instead. Neither global render-plane forcing approach is suitable for release.

## v0.14 isolated geometry A/B

Downloadable **private** artifact: `Xak_III_v14_v11_Letterbox_Centering_AB_Ready_To_Test.zip`

Source is the exact user's previously successful **v0.11 early-King Slot 2**, SHA-256 `6dd5ad0601c6a28e05952acbfb985bdef4bebe67105cd56bc5430041e686d309`.

The package includes its own uniquely named 35-track CUE, four uniquely named Geargrafx v44 saved states, JSON technical report, Python builder, synthetic regression tests, read-only comparison analyzer, and README. It reuses the existing user-owned **v0.10** English data Track02 plus all original Japanese CDDA tracks, which are **not included or modified**.

The *only* changes in geometry variants are four code constants for native subtitle sprite X positions at CD-RAM **`$9CA2–$9CA5`**:

| v0.14 Geargrafx state | SAT X coordinate values | Offset relative to v0.11 |
| --- | --- | --- |
| Slot 2 | `$90 $A0 $90 $A0` | 0, original control |
| Slot 3 | `$60 $70 $60 $70` | −48 |
| Slot 4 | `$50 $60 $50 $60` | **−64**, measured displacement |
| Slot 5 | `$40 $50 $40 $50` | −80 |

The v0.11 subtitle Y rows **184 and 204**, native glyph patterns 59/56/57/58, raster helper `AND #$3F / ORA $3E72,X / NOP NOP / ORA #$40 / RTS`, VRAM, native SAT, embedded screenshot, CD audio state and all source files remain byte-for-byte unchanged. The control state is an exact copy; each shifted variant alters four source bytes only.

**15 synthetic regression tests** passed; the private pinned original native state was separately checked, and each variant's source diff confirmed. ZIP SHA-256 `5902172527d8c639495a6b7a50dda70439c2e1ae23cd73c6908b3df7e306b127`. **Real v0.14 Geargrafx result not yet claimed.**

### User test

Extract ZIP beside the user-owned v0.10 split disc, boot v0.14 CUE. Compare Slot 2 baseline and Slot 4 **during a narrow, previously offset scene**. The shifted variants will necessarily be off-center in some normal widescreen scenes; v0.14 is not yet an adaptive solution. Compare Slot 3/5 if needed. Retain v0.10 as stable rollback.

## Separate native-sprite diagnosis

We verified the corresponding Geargrafx HuC6270 renderer at `src/huc6270.cpp`: the hardware consumes SAT sprite entries in order, honors 16 sprite subcells per scanline, supports 16/32/64-pixel sprite heights, and reads VRAM SATB DMA. Arbitrarily removing native sprites globally will also remove valid picture artwork.

The downloadable source contains an **optional, private-state-only `--mode sprite-isolation`** that can operate on a Geargrafx v0.11 native save captured **during an actual glitch frame**. It produces A/B states that mask native SAT entries wholly outside the known picture bands or touching them; the actual native and shadow SAT entries are modified in the copied state only, excluding our four subtitle glyph IDs. **This is exploratory and may be overwritten by the game's next SAT update. It is not a permanent clipping method.** No such glitch-scene save has been supplied yet.

A second script, `analyze_xak_iii_v14_two_scenes.py`, accepts one wide and one narrow v0.11 saved state and produces read-only VDC/VPC/SAT deltas to identify the *runtime scene selector* needed for automatic 64px compensation. The opaque VPC bytes are reported rather than assigned guessed meanings.

Recommended next engineering gate after user v0.14 test: use one native widescreen checkpoint and one of the problematic 4:3/glitch checkpoints to identify a reliable mode flag, then apply conditional SAT X correction in the disc-native scene hook. Analyze the actual overflowing native SAT patterns before designing a safe lower-band-only overlay that cannot uncover character elements.

**Communication rule:** no third-party GitHub comments/issues or outreach without prior user approval. Public updates in the user's own Xak III source repository are authorized by the project's existing workflow.