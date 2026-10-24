# Xak III Pilot 01 — Early King checkpoint and v0.6 raster-band probe

**October 24, 2026.** A real user-supplied Geargrafx 1.8.4 native v44 `Xak_III_English_SUB_TEST_v05_Pilot01.state5` was saved **exactly when King Wavis starts his first dialogue**. It was inspected **read-only**. The original state, game memory, audio and embedded screen image are private, and are **not committed**.

## New early-scene evidence

| Measurement | Verified value |
|---|---|
| State file SHA-256 | `63a2ea5434314c0303b9c5fb5266962de76c0c260cd093d7f649a760036cc694` |
| CD-DA physical track | **28** (start LBA `164129`) |
| Current CD-DA position | **5.2873 seconds** elapsed |
| CPU PC, MPR4 | `$858D`, bank `$82` |
| Existing redirection | `$8EE5: JSR $9C00` present in live CD RAM |
| First-execution flag | `$9C99=$00` — native subtitle hook has already run |
| VDC1 CR, HDR, RCR | `$00CC`, `$041F`, `$0040` |
| Native SAT and VRAM DMA shadow | All four v0.5 sprite records present and matching: SAT Ys `192`, Xs `64,80,96,112`, patterns `59,56,57,58`, flags `$008F` |
| Sprite font VRAM | Patterns 59, 56, 57, 58 all intact |
| VCE sprite palette 15, color 15 | `$01FF` white |
| Captured screen | **No visible subtitle** at original Y=128 |

**Correction to the earlier v0.5 status:** We previously inferred that the first King's line might require an earlier or second scene-hook installation. This new save disproves that explanation for **the recorded early frame**: the current hook **has already executed and populated the sprite table**. The missing early pixels are in the graphics/display stage, not in initial hook entry. A separate earlier v0.4.1 save at 9.3999 seconds had MPR4=`$85` and first-use flag `$FF`; it is a different point and test version and cannot override direct evidence from this v0.5 5.2873-second checkpoint.

**Remaining unknown:** saved `CR=$00CC` and latched CR `$00CC` at VBlank do **not** demonstrate that sprite output was enabled at the actual subtitle scanlines while the screenshot was rendered. The scene may alter its raster display mask, scanline CR, priority/composition or video window. A static state cannot by itself prove which of these caused the missing pixels. Do not blindly install a second hook or reupload the font each loop; that would regress earlier fixes.

The same screenshot is a normal, wide throne-room scene (256px mode). The lack of a visible sprite marker despite white palette, working font and native SAT is the decisive observation.

## v0.6 four-height visibility diagnostic

**Source-only package created in the user's conversation:** the builder and helper Python source, twelve passing offline regression tests, a README, and a redacted read-only JSON audit. No game data, patch payloads from third parties, Japanese soundtracks or saves are distributed.

The standalone builder requires **exact v0.5 Track02 SHA-256**
`a87babc4dafa0f43091015b86014036978940fdf3c44048409727a0f9acdc207`.

In raw Track02 **sector 745 only**, it changes exactly **four user-data bytes at loaded CPU addresses `$9C9A–$9C9D`**, giving the existing sprites these individual locations:

| Glyph fragment | Old on-screen Y | New on-screen Y | New SAT Y |
|---|---:|---:|---:|
| `SU` | 128 | 64 | `$80` |
| `B` | 128 | 88 | `$98` |
| `TE` | 128 | 112 | `$B0` |
| `ST` | 128 | 136 | `$C8` |

This creates a **vertical diagnostic**, deliberately **not** a readable single-line `SUB TEST`. The scene hook, glyph destination patterns **59,56,57,58**, SAT Xs, palette and priority, initial upload guard, original `$8593 STZ $3444` cleanup, Japanese audio and every other disc sector remain unchanged. MODE1 EDC/ECC and output IPS are independently verified. The output uses its own `Xak_III_English_SUB_TEST_v06_Pilot01.cue`, preserving all five v0.5 state slots.

The eleven other verified source properties and **twelve synthetic/offline tests** do not establish emulator rendering. A real v0.6 Geargrafx test is required.

### Minimal next runtime test

Launch the new v0.6 split CUE with an original clean military-camp Slot 1. During the King's first spoken line save **v0.6 Slot 2**, and at the first hero dialogue save **v0.6 Slot 3**. Note which fragments, if any, appear at the four different heights. A short state comparison at those two times will distinguish vertical/raster-dependent suppression from scene-wide output disabling, without changing v0.5 or losing prior checkpoints.

A result of *none visible* early but *some visible* later would favor a scene-wide enable or display-handoff problem and motivate tracing per-scanline VDC CR/RCR and video-compositor state; some fragments visible early would instead identify a usable band. Neither outcome is yet observed.

See [v0.5 verified runtime checkpoint](pilot-01-v05-verified-early-speech-gap.md), [Xak I & II implementation lessons](xak-i-ii-subtitle-technique-comparison.md), and [Geargrafx HuC6270 raster sprite rendering](https://github.com/drhelius/Geargrafx/blob/main/src/huc6270.cpp).
