# Pilot 01 v0.11 real screenshots -> v0.12 background-only letterbox experiment

**2026-10-25.** The user supplied ten actual Geargrafx screenshots from `Xak_III_English_SUB_TEST_v11_Pilot01.cue`. Their original screenshots are **not checked into this repository**.

## v0.11 visual findings (real emulator, not synthetic)

| Frame | User observation | Assessment |
| --- | --- | --- |
| 1 | Correct `SUB / TEST` on lower black band | Native subtitle coordinates visible, no obvious leakage |
| 2 | Correct | Same |
| 3 | Caption shifted right | Viewport-dependent horizontal coordinate system |
| 4 | Correct | Same |
| 5 | Caption shifted right | Same as 3 |
| 6 | Hero's lower sprite exposed below picture, covering subtitle | Unmasked native sprites in previously blank raster band |
| 7 | Pixie sprite fragmented/exposed and caption shifted right | Unmasked native sprites, plus second horizontal viewport |
| 8 | Correct | Same |
| 9 | Correct | Same |
| 10 | Stray animated mouth in upper right | Unmasked native sprite in normally hidden part of picture |

The underlying cause is **not** a lost font or missing disc-level hook. v0.11 replaced `BPL +2` with `NOP NOP` in the v0.9/v0.10 helper at bank81:`$76E4`. Consequently, the VDC1 sprite-enable bit was forced on even when the scene's raster table intentionally set both background and sprites off. That produces the native sprite leak. Restoring clipping while using identical sprite text coordinates would hide the subtitles again.

Screenshot-based text movement is about **96 pixels** between the two presentation regimes. This is an **observed displacement**, not yet an identified VDC register or complete runtime transform; do not hardcode a 96-pixel compensator into production without paired scene-state verification.

## Revised architectural priority

Preserve the v0.10 raster helper, which correctly masks sprites in blank bands, for any production disc patch. Explore rendering the subtitle *background tiles* in a dedicated late-raster black band instead of enabling all sprites. If the native background scroll shows artwork there, reserve a clean BAT row and set per-band scroll/BAT position through the game's already-existing raster tables.

The bank81 native raster routine was inspected from a real user save. In addition to CR at `$65A7-$65B7`, **it writes VDC1 BYR and BXR from scene-local indexed WRAM tables** at `$65B9-$65D3`:
- `$3F32,X` / `$3F72,X` supply low/high scroll Y
- `$3EB2,X` / `$3EF2,X` supply low/high scroll X
- `$3E72,X` supplies raster BG/sprite plane-enable values.
These tables provide plausible controls for later per-band subtitle positioning; their ownership and safe writing lifetime are not yet proven. The v0.12 test is deliberately less invasive.

## v0.12 two-state A/B diagnostic, private user files

Ready-to-test user-specific ZIP: `Xak_III_v12_BG_Only_Letterbox_AB_Ready_To_Test.zip`.

- Source: exact pinned v0.9 King checkpoint `state2`, SHA256 `8b40e7d95c5cfc6ec57eeffa00f58058a3b6692c055469e56d579a1bbd5c5fb2`.
- CUE: unique `Xak_III_English_SUB_TEST_v12_Pilot01.cue`, points to user's **unchanged v0.10** Track02 BIN and the original 34 CDDA tracks.
- **Slot 2:** changes **six resident CD RAM bytes only**, replacing the 10-byte helper with a 13-byte one:

```asm
AND #$3F
ORA $3E72,X
BMI .bg_originally_enabled
ORA #$80                 ; blank band: BG on, sprites OFF
RTS
.bg_originally_enabled:
ORA #$40                 ; usual band: sprites ON
RTS
```

- This produces CR `$8C` for native table `$00` (BG enabled, sprites still disabled), `$CC` for `$80`, and `$CC` for `$C0`.
- **Slot 3:** same helper, plus 5 temporary 8x8 four-plane white BG glyphs in reserved/empty tile patterns 2025–2029, and `SUB TEST` in six candidate BAT rows 18, 21, 24, 27, 30, 33. It changes **230 state bytes**, confined to resident helper and VDC1 VRAM. Existing scene art may be visibly disrupted; **not a final patch**.
- Exactly nine local tests pass with the authentic pinned source, distinct modes, guards for reserved font tiles/palette, and unchanged native-state header/screenshot.
- Final ZIP is a valid archive, SHA256 `b6184a013f77c06c61c919eed1c41eb2c737c8324b46b55324c3081193d8ac07`. **No experimental Geargrafx result yet.**
- No original v0.5/v0.9/v0.10 BIN, CDDA, save states or source media were modified. The derived native state files remain private to the chat and are not committed to GitHub.

### Minimal emulator A/B test

1. Extract the ready ZIP beside original Xak III split files and the user's existing v0.10 Track02. Start the separately named **v0.12 CUE**.
2. **Load Slot 2**, advance a few frames. Does background picture/colour leak into the previously black bottom band? Are native character sprites still clipped?
3. **Load Slot 3**, advance a few frames. Are any new **BG** letters visible in lower band, and which other artwork areas change? Does native sprite leakage remain absent?
4. Return to the already-tested v0.10 CUE if excessive corruption, or simply close the experiment without saving over original states.

Do not interpret failure to draw a BAT character as proof BG cannot work—per-raster BYR/BXR may map different rows. The next detailed investigation would identify line-to-tile mapping and choose a reserved blank region, not enable native sprites again.

**Next milestone:** a black, bounded two-line subtitle field with **no native sprite leaks** and **scene-independent centering**, followed by correctly audio-timed King Wavis dialogue. Do not begin broad text/font expansion until band masking and viewport transforms work.

**Third-party communication rule:** seek explicit approval before any public external GitHub issues/comments or other outreach; no such outreach was made.
