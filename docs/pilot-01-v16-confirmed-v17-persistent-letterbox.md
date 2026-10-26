# Pilot 01 v0.16 runtime results → v0.17 persistent letterbox

**October 26, 2026.** Real Geargrafx v0.16 A/B feedback received. The user's six native v0.14 glitch screenshots and v0.16 visual test are the evidence; do **not** claim the known native sprite clipping issue is fixed.

## Actual v0.16 results

- **Slot 3 (swap font slots):** user sees `B` and `ST` instead of the previously visible `SU` and `TE` in the affected portions; 16:9 shots display the swapped `B [space] SU` and `STTE` ordering. Glyph pattern data are fine; the missing fragments follow the current sprite selection/position. A font overwrite is no longer the leading explanation.
- **Slot 4 (all subtitle X−16):** on initial load, there is a brief `SUBU`/`TETE` composite, then the usual full `SUB / TEST`; 16:9 scenes render properly.
- **Slot 5 (restore v0.14 X−64):** on the first frame the user sees `SU`/`TE`, then the full `SUB / TEST` returns and works, **including 16:9**. This is the user's preferred mode and our new exact geometry baseline.
- **The pixie's upper black-mask failure persists across all slots**, demonstrating it is separate from the stable subtitle font/coordinates.
- The single-frame transitions are consistent with a mismatch between serialized live SAT and subsequently rebuilt scene SAT. Their exact timing/ownership is not yet hardware-traced; do not claim more.

## Why v0.17 uses a disc patch

In the authentic later pixie saved state, the `$9CA2..$9CA5` subtitle coordinate table was **`90 A0 90 A0`**, although the initially working v0.14 Slot4 had set **`50 60 50 60`**. This reveals that temporary state-only values do not consistently persist through cinematic module reloads. The v0.16 Slot5 experiment confirmed that restoring the same X table immediately recovers the complete text.

A new **source-only** v0.17 builder promotes those exact code constants into a separate v0.10-derived disc Track02, retaining the existing NightWolve English game and original Japanese CDDA. It is **not** a final English subtitle engine, and deliberately retains the already-observed v0.11 sprite leakage.

### Strict source

- **v0.10 English raw Track02 SHA-256:** `64ef0a47b2beeefc12e6a113a056964e01b67e5b71d201449c699ed5f0bb9e46`
- Source filename: `Xak_III_English_Track02_SUB_TEST_v10.bin`
- Source 35-track CUE: `Xak_III_English_SUB_TEST_v10_Pilot01.cue`
- Source Track02 size: **54,773,376 bytes**
- Original v0.10 code/raster, PAT references, native scene hook, MODE1 EDC/ECC and Track28 voice are validated; unexpected hashes, byte sequences, existing target files and nonstandard raw sectors are rejected.

### Exact new source-code data edits

| CPU location | Original v0.10 bytes | New v0.17 bytes | Purpose |
| --- | --- | --- | --- |
| `$76DF` | `29 3F 1D 72 3E 10 02 09 40 60` | `29 3F 1D 72 3E EA EA 09 40 60` | Restore v0.11's diagnostically unconditional black-band sprite visibility |
| `$9C9A` | `C0 C0 C0 C0 00 00 00 00` | `F8 F8 0C 0C 00 00 01 01` | Two text rows at native Y184 and Y204 |
| `$9CA2` | `40 50 60 70` | `50 60 50 60` | Position the two columns exactly as successful v0.16 Slot5 |

The CD-RAM mapping uses source indexed user offset `0xFE800`, Track02 225-sector raw pregap, and the standard 2352-byte MODE1 sector with a 2048-byte payload. Therefore **only raw sectors 740 and 745** change, including their regenerated EDC/ECC. The existing `$65AA` raster JSR, `$9C00` subtitle writer, VRAM glyph pattern references `76 70 72 74`, scene-loop JSR `$8EE5`, native counter cleanup and original Track28 audio are preserved.

The replacement helper is **not** a solution to unintended native character sprites in the black region. It still permits pixie, hero, NPC and mouth sprite overflow. Never claim otherwise.

## Generated artifact and offline QA

Private conversation ZIP:

`Xak_III_v17_Persistent_Black_Band_Source_Only.zip`

- Contains `v17_source/build_xak_iii_v17_persistent_letterbox.py`, `v17_source/xak_iii_disc_utils.py`, `v17_source/test_xak_iii_v17_persistent_letterbox.py` and `v17_source/README_Xak_III_v17.txt`.
- SHA256 **`0403dac96f75634c2b6d7402ffe2b7b308d49800cedae9d044ed0d8de535f94e`**
- ZIP CRC/integrity passed.
- **18 synthetic offline tests passed**: exact two-sector scope, guarded fonts/hook coordinates, correct MODE1 EDC/ECC, bit-exact IPS round-trip, source SHA and code guards, valid 35-track CUE, optional clean camp hash.
- The three new payload spans were compared against the previously accepted real **v0.16 Slot5 native state**, and match exactly.
- **No real v0.17 clean-boot Geargrafx result yet.**
- No copyrighted disc image, audio, or derived native user states are distributed inside this source-only package.
- **v0.10 remains unchanged as verified disc rollback**; v0.16 Slot5 is still the best current saved-state visual result.

### Windows / PowerShell

Extract `v17_source` into the existing Xak III directory. Run:

```powershell
py -3 .\v17_source\build_xak_iii_v17_persistent_letterbox.py --track02 ".\Xak_III_English_Track02_SUB_TEST_v10.bin" --cue ".\Xak_III_English_SUB_TEST_v10_Pilot01.cue"
```

The builder writes a **new** `Xak_III_English_Track02_SUB_TEST_v17.bin`, `Xak_III_English_SUB_TEST_v17_Pilot01.cue`, `Xak_III_v17_from_v10_Track02.ips` and JSON report. If a SHA-verified clean-camp checkpoint is available as `Xak_III_English_SUB_TEST_v05_Pilot01.state1` or v0.10 Slot1, it copies the checkpoint into a uniquely named v0.17 Slot1. Never overwrite source/rollback files.

### Meaningful next real test

Start the v0.17 CUE from the clean camp/game save, enter the royal audience and verify **both complete rows** are already in the black band at the start of the scene, during subsequent cinematic transitions and after a fresh disc initialization. Confirm the normal pixie/body/mouth leaks are **unchanged**, not increased. Report any subtitles resetting their horizontal coordinates. Send the JSON report if verification fails.

After a disc-native v0.17 pass, solve **native-sprite clipping without exposing the background layer**, then expand the glyph font and synchronize the first King Wavis English caption to CDDA Track28 speech onset.

**External communication:** no third-party comments/issues/outreach without the user's prior approval.
