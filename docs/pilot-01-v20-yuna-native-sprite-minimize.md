# Pilot 01 v0.20 — Yuna-style native sprite minimization before SAT

**2026-10-26. Built from the actual pixie-glitch v0.16 Slot 5 checkpoint. Offline tested; Geargrafx result pending.**

## What changes from v0.19

v0.19 proved an assembly-level candidate for redirecting Xak III native sprite queue insertion from bank82:`$84F0` to checked space at bank81:`$7700`, but it only **discarded** whole sprites. No user emulator result for v0.19 has been reported, so its hook has **not** been validated in Geargrafx.

v0.20 preserves that producer-hook path and introduces **hardware-valid sprite minimization before SAT insertion**, following the design of [Yuna 2's documented native cropper](https://github.com/suppertails66/yuna2tools/blob/master/yuna2/asm/scene_main.s#L1458-L1805). It is a *new saved-code experiment*, **not a patched disc**.

The actual original Xak III enqueue sequence at `$84F0–$84FA` is:

```asm
LDA $3444
SAY
STA $2EA4,Y
SAY
INC $3444
```

The new helper processes each native candidate in converted SAT-coordinate arrays **before those exact instructions**. It either returns through the original enqueue path or rejects the candidate (undoing the preceding `INC $36`, retaining correct native counter semantics). It never hooks the separate subtitle path at `$9C4B`.

### Native candidate arrays

| Work RAM | Meaning |
| --- | --- |
| `$3324,Y` / `$3384,Y` | Native screen-space SAT Y, with hardware's +64 offset |
| `$30E4,Y` / `$3144,Y` | Native sprite PAT word |
| `$33E4,Y` / `$3204,Y` | Native sprite flags (upper byte encodes height, flip and width) |
| `$2EA4` / `$3444` | Producer queue index array and item count |
| `$76ED..$76F0` | Experimental counters: visited, rejected, accepted, row trims, each mod 256 |

### Native-only cropping algorithm

For the **sample pixie scene's** measured image interval `Y=[50,178)`:

- Reject native sprites whose entire vertical extent is above Y50, or whose top starts at/after Y178.
- For *unflipped*, partially visible sprites, trim a complete **upper** 16-pixel row from a 32px-high sprite: Y+=16, PAT+=4, height→16.
- For *unflipped*, partially visible 64px-high sprites, trim a complete **upper** 32px group: Y+=32, PAT+=8, height→32; if another entire upper 16px row can be removed, trim again to height16, Y+=16, PAT+=4.
- Optional bottom minimization: shrink 64→32 when at least 32px overdraws the bottom picture boundary, and 32→16 when at least 16px overdraws; keep Y and base PAT unchanged for these unflipped bottom reductions.
- Leave partially visible **Y-flipped** native sprites unmodified; fully invisible flipped sprites are still rejected.
- Preserve 16px-high sprites with any visible portion, without attempting impossible sub-16px sprite heights.
- Preserve existing subtitle sprite insertion code at `$9C00–$9CBF`, its font/position tables, the working raster code and game audio **byte-for-byte**.

**Limits:** the native PCE sprite hardware cannot encode a 48px sprite height; reductions are quantized and **may still overdraw up to 15px** into black bands. Correct general clipping ultimately requires a separate raster window for subtitles and native image, or partial pattern masking. The boundary Y50/178 is from this one sample, **not a verified per-scene variable**. Do not apply this patch unconditionally across other cinematic scenes.

### Authentic pixie queue prediction

The user's pinned v0.16 Slot 5 source save has producer queue `$3444=23`: **19 native + 4 subtitle entries**. The v0.20 top minimizer predicts:

- **7 native sprites wholly outside** the picture: rejected.
- **5 partially visible native sprites**: trimmed at the upper edge (one 64→32→16, four 32→16); residuals typically start near Y45.
- **7 remaining native sprites**: accepted unchanged.
- **All 4 subtitle sprites**: appended independently and protected.

The saved generator queue is a snapshot, not a live execution trace. The exact visible result and the helper's survival across module loads require Geargrafx testing. No v0.19 runtime outcome is presumed.

## User-specific deliverable

Private ready-to-load ZIP (in this conversation):

`Xak_III_v20_Yuna_Native_Minimization_Ready_To_Test.zip`

- **SHA256:** `e594cd832db0688d5b21d52f3b60c21127c1e0739f7af5f52c7c45408e8120c0`
- **11 files;** archive CRC validated.
- Pinned source **v0.16 Slot5** SHA256 `b09b9f3bd43fee4aacc2e7ee9fd932a3183d969624075651eefab43b7359c4d9`.
- Output includes separate `Xak_III_English_SUB_TEST_v20_Yuna_Pixie_Pilot01.cue` (references unchanged user's own v0.10 Track02 and 34 original Japanese audio tracks), four unique `.state2`–`.state5` saved states, machine-readable JSON report, original v0.19 support module, new v0.20 builder, bytecode tests, telemetry reader, and test instructions.
- **20 local tests passed**, including an independent subset HuC6280 bytecode interpreter; exhaustive Y values (0–255) for each sprite height in both new clipping modes; native Y/PAT/height restoration, pattern-high-byte carry, flipped-sprite nonmutation, native enqueue semantics, saved-source checks and protected subtitle fields.
- The new code is contained in the authentic zero-filled `$7700–$785F` candidate cave (largest helper 332 bytes, finishing at `$784C`) with exact source-guard. The new save changes **only resident code/hook bytes**; original v0.10 disc, all CDDA, and old saves are unchanged.

### Real Geargrafx evaluation

Extract ZIP alongside existing v0.10 game/audio, boot `Xak_III_English_SUB_TEST_v20_Yuna_Pixie_Pilot01.cue`:

| Slot | Experiment |
| --- | --- |
| **2** | Byte-identical original successful v0.16 Slot5 pixie checkpoint |
| **3** | Interception with original native enqueuing reproduced, no filter |
| **4** | Reject wholly outside sprites, **minimize upper** edge |
| **5** | Slot4 + **minimize lower** edge |

Examine **the pixie's upper body**, whether other character pixels are lost, complete subtitle lettering, and whether animation/audio continue. The loaded thumbnail and initial frame may be stale relative to the serialized SAT; judge moving frames. **If all look identical, save a running v0.20 Slot1** and upload that native state. Then run `inspect_xak_iii_v20_telemetry.py` to see if the native hook remained loaded and the counters incremented. Stop if it freezes or produces substantial scene corruption.

No user-side disc rebuilding is required; no external GitHub comments/issues/outreach made. The next milestone after a visually successful hooked prototype is **disc-native installation** and **scene-dependent crop bounds**, then raster-phase separation for pixel-clean bands and finally synchronized King Wavis English text.
