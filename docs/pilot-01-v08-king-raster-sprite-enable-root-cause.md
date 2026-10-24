# Pilot 01 v0.7 failure -> v0.8 King-opening raster visibility root cause

**24 October 2026. Real v0.7 user result: no additional BG text visible. v0.8 save-only test prepared and offline validated, emulator result pending.**

## v0.7 background-tile outcome

The user loaded our VRAM-only v0.7 modified early-King v0.5 state4 and reported that **only the previous text appeared**, with no new background-tile `SUB TEST` text visible. It is a negative *runtime visibility* test, not proof that the text patterns were malformed.

In a private local reconstruction from the actual modified save's VDC1 VRAM, all four inserted BAT text rows and 8x8 glyphs appeared correctly in the simulated background. The cinematic's **actual native framebuffer** shows the throne-room artwork displaced vertically and black upper/lower regions, unlike the naive static BAT decoding. That points to line-sensitive raster/video control, native scroll and composition; merely inserting visible VRAM tiles at arbitrary BAT rows does not mean those rows appear on screen. The private screenshots, proprietary state bytes and entire user game data remain uncommitted.

## Newly isolated King-opening sprite-disable logic — concrete source bytes

From the authentic pinned v0.5 **state5**, at **5.2873 seconds** into physical Japanese voice Track 28, we extracted the active Super CD RAM in CPU page bank **$81**, and independently mapped the live VDC1 and WRAM shadow registers.

A **preexisting native HuC6280 instruction sequence** at CPU `$65A7` is:

```text
$65A7  AD 3D 23     LDA $233D       ; original game VDC1 CR low-byte shadow $CC
$65AA  29 3F        AND #$3F        ; strip BG bit $80 AND sprite bit $40
$65AC  1D 72 3E     ORA $3E72,X     ; raster table selects BG/sprite enable per band
$65AF  03 05        ST0 #$05        ; VDC control register
$65B1  8D 02 00     STA $0002       ; write CR low byte
$65B4  AD 3C 23     LDA $233C       ; CR upper byte $00
$65B7  8D 03 00     STA $0003
```

The immediate byte at **CPU $65AB** is exactly `$3F` in the real early-King save. It lives at file offset **42,436 ($A5C4)** in Geargrafx v44 serialization, corresponding to the physical bank81 CD RAM offset `$25AB`.

The native writable raster enable table is in **WRAM at $3E72**. Comparing three genuine v0.5 native checkpoints:

| Track 28 checkpoint | Within first 96 raster-table bytes | Meaning |
| --- | --- | --- |
| Early King state5 / 5.2873 s | **16 entries $80**, 80 zeros, no $C0 | BG enabled, sprites disabled in those 16 active entries |
| Later state2 / 74.3040 s | **16 entries $C0**, 80 zeros, no $80 | BG and sprites both enabled in active entries |
| Later state3 / 129.9988 s | **16 entries $C0**, 80 zeros, no $80 | Same sprite-capable raster mode |

The per-band enabling equation is **(`$CC & $3F`) | table[X]**:

- King's opening: `$0C | $80 = $8C` ⇒ VDC sprites disabled at active raster bands despite saved CR `$CC` at VBlank.
- Later scene: `$0C | $C0 = $CC` ⇒ sprites enabled.

**This explains why a static snapshot of CR=$00CC, valid sprite SAT, live glyph VRAM and white palette still yielded no subtitle early on.** The snapshot is at another raster phase; the native code changes CR during display. The disassembly/table values are directly extracted from user-provided state, not inferred from the Xak I & II patch.

## v0.8 controlled experiment: preserve sprite-enable bit

Instead of modifying the data track before verifying the interaction, build **an entirely separate experimental save namespace** using the original **v0.5 Track02 BIN unchanged** and a renamed duplicate of its 35-track CUE:

- Name: `Xak_III_English_SUB_TEST_v08_Pilot01.cue`.
- Read-only-derived `Xak_III_English_SUB_TEST_v08_Pilot01.state2`, sourced from the exact original v0.5 early-King state5, changes exactly **one resident CD RAM byte**: the `AND #$3F` operand at `$65AB` to **`AND #$7F`**.
- New equation: `($CC & $7F) | $80 = $CC`: sprite enable bit `$40` survives; unchanged v0.5 subtitle graphics and native SAT injection should become visible during the King.
- VDC register saves, VRAM/BAT, audio state, thumbnail, other CPU code and all original v0.5 files are **byte-identical**.
- Pinned input state SHA-256 `63a2ea5434314c0303b9c5fb5266962de76c0c260cd093d7f649a760036cc694`.
- Derived state SHA-256 `96ac478112668b0d355edc4300a09b3ea0ff5e7cb7748c3e6f1a2328cd8d6fc7`.
- **Nine local synthetic and pinned-source tests passed**. Actual Geargrafx visual result **has not been tested**.

**Crucial qualification:** `AND #$7F` preserves sprite bit in raster table areas that previously carried `$00`, too. This **may expose unrelated sprites in normally blanked areas or cause scene artifacts**. It is deliberately a short visibility probe, not a safe general subtitling fix. If it works, the proper design is to change only the King's appropriate active raster bands (`$80→$C0`) at controlled times and avoid forcing sprites on in lines where both planes should be off.

### Minimal user action

1. Close Geargrafx, extract `Xak_III_v08_King_Raster_Sprite_Probe_Ready_To_Test.zip` **into the existing v0.5 game directory**.
2. Load `Xak_III_English_SUB_TEST_v08_Pilot01.cue`; it uses the already-existing v0.5 BIN and the unchanged 34 Japanese audio tracks.
3. Load **v0.8 Slot 2**, which resumes at the King's very first speech. Check whether `SUB TEST` appears **before** the hero speaks.
4. Stop immediately if graphics are corrupted. Report success/failure and a screenshot. Do not overwrite original v0.5 saves.

No request for a trace logger, audio re-recording, another large BIN or original Xak I & II disc is needed for this **immediate** experiment.

## Provenance and boundaries

All code and WRAM table evidence is from the v0.5 user state, with the Geargrafx v44 serializer layout cross-checked against upstream. The temporary save-state patch is derived from the user's original private state and distributed privately in chat, **not** committed to GitHub. Repository source/tests, findings and README may be committed as ongoing engineering.

The user requests approval before any public third-party comments, issues, or outreach. **Do not contact the Xak I & II author without prior approval.**

Previous: [v0.7 BG diagnostic](pilot-01-v07-black-band-bg-state-test.md), [v0.5 glyph-stability result](pilot-01-v05-verified-early-speech-gap.md).
