# Pilot 01 v0.2 — v0.1 actually ran, but its font was overwritten

**2026-10-20. Runtime evidence analyzed from clean user-supplied Geargrafx slot 3.** The file is named `Xak III - The Eternal Recurrence (Japan)(1).state3`, but **its resident code proves that the experimental English SUB TEST v0.1 disc had loaded and executed**. Save filename alone does not establish disc identity.

## Conclusive v0.1 observations

- Geargrafx v44 snapshot SHA-256: `8dcf424e986b9696077d12a9a02ac0125169ce6fc846e2bad534b132f504889d`.
- MPR4 = `$82`, saved PC = `$858D`, in the **original native SAT writer**.
- At CPU `$8EE5`: patched `20 00 9C` = `JSR $9C00`.
- At `$9C00`: **the complete expected 653-byte v0.1 code/font payload**, except its intentional one-byte initialization change.
- The v0.1 initialization flag at `$9C6C` was **`$00`**, proving the first-run upload path was reached.
- All four injected SAT records are in both the VDC's live sprite table and its automatic DMA source. CR = `$00CC`, DCR = `$0010`, DVSSR = `$0C00`.
- The four glyph patterns 504–507 at VRAM word `$7E00` were **not** the expected `SUB TEST` bitmap. Pattern 504's first 32 bytes exactly match the injected **four SAT entries** (`0F 01 70 00 F0 03 8F 00 ...`), and patterns 505–507 contain no nonzero glyph bytes. The same entries are present in VRAM at word `$0C00`.

The **exact instruction that replaced the v0.1 glyphs has not been traced**. But v0.1's issue is now localized to VRAM glyph placement or persistence, **not disc mounting, hook entry, or the native sprite queue**. There is no reason to edit the original `STZ $3444` cleanup.

## v0.2 response: relocate glyphs to four separately checked regions

Instead of storing all four glyphs contiguously at risky patterns **504–507** (VRAM word `$7E00`), v0.2 uses sprite patterns **30, 31, 43, 56** at respective VRAM word addresses **`$0780, $07C0, $0AC0, $0E00`**.

All four locations contained only zero bytes in both the original clean audience state and the v0.1 runtime state. None is referenced by the visible scene background-tile map in those snapshots. **Future frames have not been exhaustively tested**, so this is a controlled experimental relocation, not an unconditional guarantee of ownership.

The hook performs four distinct 128-byte HuC6280 `TIA` transfers to the selected VDC1 VRAM words on first invocation, then enqueues the same four native SAT sprites each frame. The game-native `$8516` SAT writer is called exactly once; the original `$8593: STZ $3444` cleanup is preserved. No unsafe slot 6–7 state or in-RAM NOP patch is used.

## Binary and provenance checks

- Required reconstructed English split Track 02 input SHA-256: `c3aef214616309a6a87f9836bdc8062e57b3e2d5b492b089f72fd52848cd9b72`.
- v0.2 experimental raw Track 02 SHA-256: `c69aa8dd3f0878dc70e8e80f804d0160a5b5c3572c4bad9ebcea711082a2268d`.
- [v0.2 IPS patch](../patches/Xak_III_Pilot01_SUB_TEST_v02_Track02.ips), SHA-256: `74b0291217c3b880683e56b5ec73e1d9055571b5d477df956092be85948e4d4d`.
- Git blob SHA-1 of published IPS: `5f4fc5acc27490ab539591268072c7b309b1b50b`.
- Only raw Track 02 sectors **743 and 745** differ from the pinned source. Proper MODE1 EDC/ECC for these two sectors verified.
- The scene-loop `$8EE5` still calls `$9C00`; relocated hook length **698 bytes**, fitted within a 1024-byte verified vacant code cave.
- `$8593` still contains `9C 44 34` (`STZ $3444`).
- All other sectors and original Japanese CD-DA tracks are unchanged; CUE has 35 tracks with **only Track 02** replaced.
- Four independent additional synthetic tests plus legacy coverage: **14 local tests passed**. Tests are limited and do **not** prove Geargrafx renders the new glyph locations.

## Exact next runtime test, Geargrafx 5 slots only

1. Close Geargrafx completely. Use the **new v0.2** `Xak_III_English_SUB_TEST_v02_Pilot01.cue`, matching patched Track 02 and your original Japanese audio Tracks 01, 03–35.
2. Load **original clean camp slot 1**, not the v0.1 audience slot 3 or the contaminated slots 6–7. Loading an already-in-scene save would restore old resident code.
3. Walk into King Wavis's royal audience. Look for the white **SUB TEST** marker and confirm the Japanese voice and animation.
4. Save the **v0.2** audience while running to **slot 4** and upload that file. Preserve clean camp slot 1, clean original audience slot 2, previous v0.1 slot 3. Slot 5 remains free/reusable.
5. Inspect v0.2 runtime flag **`$9C99`**, the four sprite references in SAT, and the glyph bitmap at 30/31/43/56. Do not judge by the thumbnail.

**Status:** v0.1 hook execution is confirmed by a real user save; **v0.2 display is untested**. Japanese voices will remain original. No copyrighted game/voice BIN or private save has been committed to this repository.
