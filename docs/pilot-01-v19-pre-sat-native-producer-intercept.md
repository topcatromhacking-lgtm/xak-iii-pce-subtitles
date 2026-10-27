# v0.19 — Xak III pre-SAT native sprite producer hook (Geargrafx test pending)

**26 October 2026.** This is the first runnable user-specific *producer-level* clipping experiment, built from the user's **confirmed v0.16 Slot 5 pixie-frame save**. It does **not** modify the game disc.

## Background

The user correctly identified the missing architectural idea in [Yuna 2's assembly](https://github.com/suppertails66/yuna2tools/blob/master/yuna2/asm/scene_main.s): protect the subtitle sprite windows with separate raster states, but remove or minimize unwanted **native** sprites **before** their SAT entries are generated. Earlier Xak III attempts altered already-built live SAT and VRAM SATB, which were immediately superseded by the game's own sprite production.

The authentic Xak III native producer in bank82 (from the user's pixie checkpoint):
- **$84F0–$84FA:** `AD 44 34 42 99 A4 2E 42 EE 44 34`, or `LDA $3444; SAY; STA $2EA4,Y; SAY; INC $3444`; the HuC6280 `SAY` instruction swaps A and Y without changing ordinary NZ/C flags.
- **$84EE:** original `INC $36` just before queue insertion, which a reject path must undo.
- **$84FB:** continuation after enqueue. The native SAT output begins later at $8516.
- **$9C4B:** separate subtitle sprite insertion; the new hook does **not** intercept this routine.

## v0.19 saved-code experiment

A fresh user-only ZIP was built:

`Xak_III_v19_PreSAT_Native_Sprite_Crop_Ready_To_Test.zip`

**ZIP SHA-256:** `f7b3f9b23b9778e6e54f3ac76d21850d208c903412bf6747dc0304ffa94bc635`

**Source:** exact v0.16 Slot 5 checkpoint, SHA-256 `b09b9f3bd43fee4aacc2e7ee9fd932a3183d969624075651eefab43b7359c4d9`.

- In copied bank82 CD RAM, replace native **$84F0 `LDA $3444` (three bytes)** with `JMP $7700`.
- Insert a guarded helper at unused resident bank81 **$7700** (verified empty over $7700–$77CF in this exact checkpoint). This same mapped CD-RAM module has MPR `FF F8 80 81 82 83 84 00`.
- The accept branch executes the **identical 11-byte native enqueue sequence**, then `JMP $84FB`. The reject branch **decrements $36** to reverse the original $84EE increment, skips enqueue, and returns via `JMP $84FB`. No JSR return addresses are leaked.
- Native candidate geometry is read from converted SAT arrays: Y low `$3324,Y`, Y high `$3384,Y`, height mode `$3204,Y & $30`. Unrecognized Y high bytes are conservatively retained.
- Fixed **pixie-only** sample crop interval Y **[50,178)**. This is **not a dynamic/general crop solution** and is **not yet Yuna-like partial 16/32/64-pixel sprite minimization**.
- Diagnostic counters (mod 256) at previously zero resident addresses `$76ED` visited, `$76EE` rejected, `$76EF` accepted. An optional read-only telemetry script can inspect a later emulator checkpoint.
- Four separate v0.19 states under their own 35-track CUE referencing unchanged **v0.10 Track02**:
  - Slot2 original confirmed v0.16 Slot5 copied byte-for-byte.
  - Slot3 intercept hook with exact native pass-through.
  - Slot4 reject native candidates completely outside picture (predicted **7 / 19** in saved source queue).
  - Slot5 reject completely outside plus any crossing the upper picture boundary (predicted **13 / 19**, can remove legitimate artwork).

### Validation

- **18 local unit tests passed**.
- Includes a synthetic interpreter for the generated HuC6280 opcodes and tests the whole **256 Y-value range for each 16, 32, 64-pixel height mode**, in each hook mode. Verifies legal branch targets, queue count, original array-index exchange, temporary counter restoration, stack balance and sentinel return address.
- Exact real-state SHA, module bank map, native queue instruction fingerprint, still-empty helper cave, independent subtitle writer, unchanged subtitle X/Y/VRAM and unchanged save metadata verified.
- ZIP CRC/contents and all four 749,238-byte saved states checked; no copyrighted BIN or CDDA material included.
- **No actual Geargrafx execution or visual pass yet.** Static saved producer records may differ from the next frame's regenerated queue.

### User test

Extract ZIP into existing game directory, launch `Xak_III_English_SUB_TEST_v19_Producer_Crop_Pilot01.cue` and compare Slots **2→3→4→5** while the pixie animates. For each record: complete `SUB TEST`, overflow, missing character art, freezing. If all equal or no hook effect, save a running v0.19 scene to its unused Slot1 and upload. Run `inspect_xak_iii_v19_telemetry.py` on that saved state to learn whether producer interception survived.

### Next engineering gate

- If Slot3 changes graphics, correct the hook’s preservation of native queue semantics before any cropping.
- If Slot4 improves picture and preserves characters, expand to dynamic scene crop-variable acquisition and **actual Yuna 2-style partial sprite minimization**, respecting 16/32/64 sprite constraints and flipped patterns.
- If Slot5 removes legitimate characters, it confirms why full-intersection rejection is diagnostic only.
- If results are identical and telemetry remains zero, trace bank/module reload and move the hook into guarded **disc-native** code rather than further SAT save-state changes.
- Preserve verified v0.10 disc rollback, desired v0.11/v0.16 Slot5 two-line lower-black-band text, Japanese voices, and the independent subtitle insertion writer.
- Do not contact third-party authors or post on external GitHub issues without the user's prior approval.
