# Pilot 01 v0.10 — promote verified selective raster fix to Disc Track 02

**October 24, 2026.** Geargrafx runtime **v0.9 state-only** passed: the tester reports all good, meaning the King's first speech displays `SUB TEST` without black-border corruption or interrupted dialogue. The **v0.10 disc patch has NOT been tested by Geargrafx**.

## Recovered native raster bytes

Resident HuC6280 bank81 at `$65AA`, original:

```asm
AND #$3F
ORA $3E72,X
```

v0.9 verified overlay:

```asm
$65AA: JSR $76DF
       NOP
       NOP

$76DF: AND #$3F
       ORA $3E72,X
       BPL .done
       ORA #$40
.done: RTS
```

Early-King raster `$80` becomes `$CC` (sprites + background on). Blank `$00` stays `$0C` (both disabled), and later `$C0` stays `$CC`. Unlike v0.8's unconditional sprite enable, the v0.9 fix preserves intentionally blank raster bands. It may still reveal game sprites in other background-enabled bands; those scenes are **not** validated.

## Exact disc provenance and scope

The existing Xak III NightWolve English cinematic CD-RAM bank segment maps to **indexed Track02 ISO user offset `0xFE800`**, with 225 raw-sector pregap. Mapping a CPU address `A` in the mapped `$4000–$BFFF` area:

```text
indexed_user = 0xFE800 + (A - 0x4000)
raw_sector = 225 + indexed_user // 2048
raw_byte = 2352 * raw_sector + 16 + (indexed_user % 2048)
```

Verified offsets:
- CPU `$65AA` -> raw **sector 738**, byte **`0x1A821A`**.
- CPU `$76DF` -> raw **sector 740**, byte **`0x1A95AF`**.
- Existing subtitle hook `$9C00` -> raw sector 745 at `0x1AC0C0` (unchanged).

The proposed builder uses the verified **v0.5 Track02 SHA256 `a87babc4dafa0f43091015b86014036978940fdf3c44048409727a0f9acdc207`**, checks the original 13-byte native code context, the still-empty **128-byte** code cave, subtitle hook and font references, and valid MODE1 EDC/ECC before writing. It changes **only 15 user-data code bytes in raw sectors 738 and 740** and regenerates those two sectors' EDC/ECC, then checks exact sector differences and applies the IPS back to verify the output. No other game sectors, the native sprite writer or Japanese audio tracks are modified.

We inspected the **actual user v0.9 state2**, confirming its 5-byte callsite is `20 DF 76 EA EA` and 10-byte helper is `29 3F 1D 72 3E 10 02 09 40 60`, exactly what the builder writes. **12 synthetic regression tests passed** locally; these did not use the complete real v0.5 data BIN, which resides on the user's own PC.

The private ZIP supplied to the user, **`Xak_III_v10_Disc_Native_Selective_Raster_Source_Only.zip`**, includes the guarded Python builder, a standalone MODE1/IPS utility module, synthetic tests and instructions. It contains **no proprietary ROM, audio, patches derived from the game, or save states**.

## Next real Geargrafx validation

Extract the source-only ZIP into the existing Xak III game directory, preserving the `v10_source/` directory. In PowerShell:

```powershell
py -3 .\v10_source\build_xak_iii_v10_disc_raster.py --track02 ".\Xak_III_English_Track02_SUB_TEST_v05.bin" --cue ".\Xak_III_English_SUB_TEST_v05_Pilot01.cue"
```

Outputs a **new** `Xak_III_English_Track02_SUB_TEST_v10.bin`, `Xak_III_English_SUB_TEST_v10_Pilot01.cue`, a v0.5→v0.10 IPS, JSON report and a separate Slot 1 copied only from the SHA-verified clean camp checkpoint.

Launch the new v0.10 CUE, load **v0.10 Slot 1**, play into the King Wavis audience from camp, and verify `SUB TEST` is present from the very first King's speech; continue through the hero's first response and check that borders, native animation and Japanese voice remain intact. Upload JSON report and any failure-only save state/screenshot.

If the builder stops because its source code cave is occupied in the **disc** (despite seven zero-filled state checkpoints), do **not** patch or force it; report the exact error so we can revisit the disc source location. Original v0.5 BIN, CUE, states, all audio and prior experiments remain untouched.

Only after a real v0.10 fresh-load validation should the next version replace the static marker with an actually synchronized English subtitle event tied to physical CD Track 28.

No external comments or outreach made.