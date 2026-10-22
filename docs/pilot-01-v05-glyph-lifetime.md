# Pilot 01 v0.5 — real cinematic glyph corruption isolated

**October 21, 2026. Offline builder prepared; visual result not yet validated.**

## Five v0.4.1 Geargrafx v44 checkpoints

A user-supplied video and five native Geargrafx snapshots were examined **read-only**. All raw saves, screenshot assets and the user's audio recording remain private.

| User save | Position in physical CD Track 28 | Observation |
| --- | --- | --- |
| v0.4.1 Slot 1 | Before audience | Original clean military-camp checkpoint; pinned SHA-256 `8c8f89e94bb7b89c4d76183f562ba7e2742eb385759eda840b1f976fe50183ba` |
| v0.4.1 Slot 2 | Before Track 28 | Black scene transition, not yet in the subtitle code overlay |
| v0.4.1 Slot 3 | **14.4639 s** | Full visible `SUB TEST`; patterns 43, 56, 57, 58 intact |
| v0.4.1 Slot 4 | **32.3324 s** | `SU` is corrupted; VRAM pattern **43 changed 64 of 128 bytes**; other glyphs intact |
| v0.4.1 Slot 5 | **72.5824 s** | Pattern 43 still damaged with the **same** pattern bytes as Slot 4; glyphs 56–58 intact; a video-window/crop transition changes the apparent visibility |

Every examined later state retains the four subtitle SAT records, behind the game-native moving sprites. The video corroborates that the subtitle starts readable and only later becomes corrupted. The VRAM overwrite is persistent, rather than an isolated one-frame symptom.

**Independent second issue:** VDC register **HDR changes from `$0C0F` in Slot 3 to `$041F` in Slots 4–5**, corresponding to a change from a 128px-wide picture to a 256px-wide picture. The fixed sprite position appears in different captured-screen horizontal coordinates after that transition, explaining some of the reported black-mask/visibility behavior. Do not conflate it with the damaged `SU` glyph.

## v0.5 experiment

A standalone source-only v0.5 builder, based on the already verified **v0.4.1 Track 02 SHA-256** `fb74bbfdbedeec414c38ede2c37b0917372eb6669986c36cefd90fbe930c4fda`, makes the smallest plausible fix:

- Relocate only the first sprite font bitmap from VRAM pattern **43** (word `$0AC0`) to pattern **59** (word `$0EC0`). Pattern **59 was all zero** at 14.46, 32.33 and 72.58 seconds.
- Change CPU hook byte `$9C0F` (VDC VRAM destination high byte) `$0A -> $0E`.
- Change CPU hook byte `$9CAA` (first subtitle SAT2 sprite pattern) `$56 -> $76`.
- Recompute raw MODE1 EDC/ECC for **Track 02 raw sector 745 only**.
- Preserve one-time font upload guard, all other glyphs, SAT X/Y positions, all 34 original CD-DA tracks, the original game-native sprite writer and crucial `$8593 STZ $3444` cleanup.
- Create new `Xak_III_English_SUB_TEST_v05_Pilot01.cue` basename with its **own five save-state slots**. The verified original clean camp save can be copied to v0.5 Slot 1.

**Eleven offline regression tests passed**, including full-size synthetic Track02, exact user-data changed-byte count, MODE1 checks, IPS round-trip and hash/foreign-hook refusal. These are software tests; **Geargrafx has not validated v0.5 rendering yet**.

Pattern 59 is still part of the wider video-RAM address space used for the scene background attribute table. Its emptiness at three states is strong scene-specific evidence, **not proof that every intermediate/later frame leaves it untouched**. If the next video shows any new image artifact, revisit VRAM lifetime. Do not resume repeated font writes to the collision-prone original regions.

## Subsequent milestone

Verify continuous uncorrupted `SUB TEST` through the hero speech and a later scene using separate v0.5 states (early, ~32s, ~70–100s). After visual stability, address **adaptive horizontal placement during HDR width changes**, then add the first spoken-line synchronized English subtitle using Track 28 timing.

Previous reports: [v0.4.1](pilot-01-v041-centered-mask-probe.md), [v0.4](pilot-01-v04-stability-probe.md), [v0.3](pilot-01-v03-visibility-probe.md).
