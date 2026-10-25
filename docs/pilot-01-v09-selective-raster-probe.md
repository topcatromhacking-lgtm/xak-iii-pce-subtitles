# Pilot 01 v0.8 in-game success -> v0.9 selective raster probe

**24 October 2026. v0.8 has been visually verified by the user; v0.9 is prepared but not yet emulator-tested.**

## Confirmed v0.8 result

The user loaded the ready-to-test v0.8 native Geargrafx state at the start of King Wavis's first dialogue and reported: **"Sub test appears since the beginning of the load"**. The v0.8 experiment differs from the original saved CD RAM in exactly one byte, changing the HuC6280 `AND #$3F` operand at bank81 CPU `$65AB` to `AND #$7F`.

This proves the **first King's speech can display our v0.5 `SUB TEST` sprite marker** without any new font upload, secondary scene hook, altered CD audio or sprite repositioning. It corroborates the native raster-code hypothesis documented in [v0.8 technical investigation](pilot-01-v08-king-raster-sprite-enable-root-cause.md).

Do not yet claim a complete subtitle system: these are diagnostic glyphs, not timed English dialogue; the emulator test did not establish behavior across every raster band, scene transition or skip.

## Why v0.8 needs refinement

The game's native raster update contains:

```asm
LDA $233D        ; base CR low byte, $CC in verified scene
AND #$3F         ; clear BG ($80) and sprite ($40) bits
ORA $3E72,X      ; per-band raster enable table
ST0 #$05
STA $0002        ; write VDC1 CR low byte
```

At the King's opening, the table's 16 active entries hold `$80`, i.e. background enabled and sprites disabled. Later dialogue changes them to `$C0`. v0.8's `AND #$7F` retains the sprite bit unconditionally, so even bands with **table value `$00`** can render sprites. This is a risk of unwanted graphics in intentionally blank/letterboxed bands.

## v0.9 narrow rule

The newly prepared v0.9 saves only modify **resident CD RAM**, leaving original v0.5 disc and audio files untouched:

```asm
; In bank81 native code at CPU $65AA:
JSR $76DF
NOP
NOP

; Ten-byte helper at $76DF, originally zero in 7 inspected v0.4.1/v0.5 states:
AND #$3F
ORA $3E72,X
BPL .done         ; bit $80 (BG enable) not set -> leave sprites disabled
ORA #$40          ; BG-enabled band -> preserve BG, enable sprites
.done:
RTS
```

At the verified base CR low byte `$CC`:

| Raster table | Native control | v0.8 | v0.9 |
| --- | --- | --- | --- |
| `$80` BG-only King | `$8C` | `$CC` | **`$CC`** |
| `$00` blank | `$0C` | `$4C` | **`$0C`** |
| `$C0` normal later | `$CC` | `$CC` | **`$CC`** |

This preserves the original N/Z/C/V result semantics of the CR calculation, because `BPL` branches on the result of the original ORA and does not modify flags; the ORA on the other branch updates N/Z without changing carry/overflow. The helper uses no added stack pushes or clobbered X/Y; native `JSR/RTS` pairs. The original display register write sequence remains intact.

**Remaining risk:** some native BG-enabled scenes may intentionally suppress sprites even when `$80` is active. This probe allows sprites in any BG-enabled band, not exclusively the first King's speech. It therefore remains diagnostic pending full-scene testing. The proposed code cave `$76DF` was observed to remain zero in **seven** authentic scene snapshots, but its lifetime outside the sampled frames is not proven.

## Artifact details and test

The privately packaged ZIP `Xak_III_v09_Selective_King_Raster_Probe_Ready_To_Test.zip` includes:

- `Xak_III_English_SUB_TEST_v09_Pilot01.cue` — a unique 35-track CUE pointing to the unchanged v0.5 English BIN and 34 original Japanese audio tracks.
- `Xak_III_English_SUB_TEST_v09_Pilot01.state2` — new Geargrafx v44 state, seeded from original pinned v0.5 King-start state5.
- JSON report, source-only state builder, regression tests, and concise README.

Pinned original v0.5 state SHA-256: `63a2ea5434314c0303b9c5fb5266962de76c0c260cd093d7f649a760036cc694`. Resulting v0.9 state SHA-256: `8b40e7d95c5cfc6ec57eeffa00f58058a3b6692c055469e56d579a1bbd5c5fb2`. Exactly **15 state bytes** differ: the 5-byte callsite plus 10-byte helper. Video RAM, video hardware registers, screen thumbnail, CD audio state and original v0.5 files are unchanged.

**Nine local synthetic and pinned native-state checks pass. No emulator result for v0.9 is claimed.**

### Minimal Geargrafx procedure

1. Extract the v0.9 ZIP into the existing Xak III v0.5 game folder; do not overwrite prior saves.
2. Boot the new `Xak_III_English_SUB_TEST_v09_Pilot01.cue`, load **v0.9 Slot 2**.
3. During the King's opening speech check whether `SUB TEST` is visible, that black borders remain clean, and that character animation and Japanese voice continue.
4. Continue through the hero's first reply; stop if any stray sprite or scene corruption appears. Upload a screenshot or save if anything unexpected occurs.

## Next validated engineering gate

After a real v0.9 pass, map the same two resident code locations through the verified 64 KiB CD-RAM/Track02 provenance (cinematic banks start at indexed ISO offset `$FE800`), then build a *new source-only disc Track02 patch* using strict original BIN SHA-256, code-byte guard, EDC/ECC restoration for changed MODE1 sectors, and an IPS round-trip test. The disc patch must be tested from a clean camp state, not only a mid-scene RAM save, and must not overwrite the proven v0.5 build.

Avoid any public comments or outreach without the user's explicit prior approval.
