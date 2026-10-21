# Runtime warning: save-state cross-loading contaminated Pilot 01 tests

**2026-10-20.** User confirmed that experimental `slot 7` was **renamed/copied to slot 1 and loaded while running the original Japanese 35-BIN / 1-CUE disc**. The original English release uses a combined BIN; the Xak III English subtitle experimental disc is a third separate configuration (35 split BIN tracks, translated/patched Track 02).

## Why this matters

Geargrafx matches the disc identity using a CRC of the first 64 indexed user-data sectors, which are common between these images. Therefore an old save may be accepted under another disc even when their **resident executable code is different**. A save restores its CPU program counter, bank mapping, RAM-resident scene code, video data and playback state; loading it does not reload the executable from the newly selected disc.

The original slot-7 diagnostic had:
- `$8593: EA EA EA` (experimental NOPs replacing `STZ $3444`, which the game relies on to clear the sprite count).
- `$3444 = 247`, beyond the initialized 96-selector range.
- Saved PC `$84F0` during the sprite-collector logic.

Thus a renamed **slot 7** is **not a clean slot 1 checkpoint** and can contaminate the Japanese or English disc. In particular, the **SUB TEST disc patch's no-subtitle runtime result must be regarded as inconclusive** until retested with the original clean military-camp checkpoint and a verified, consistent experimental disc load. Some earlier no-subtitle results may have other independent explanations; do not claim *all* prior results were caused by this cross-load.

## Verified safe private recovery checkpoints

Both earlier original user uploads remain available in the working session, were reexamined without mutation, and contain the unmodified `$8593: 9C 44 34` cleanup:

| Scene | SHA-256 of Geargrafx v44 saved file | PC | `$3444` |
|---|---|---|---|
| Military camp, original slot 1 | `8c8f89e94bb7b89c4d76183f562ba7e2742eb385759eda840b1f976fe50183ba` | $8E8F | 36 |
| Royal audience, original save | `d91527353864d7ac1d5aa3b51239582a68ee642fd9b65a5cc58817075a8dbc6b` | $8590 | 0 |

A private recovery ZIP packages those two pristine checkpoints and instructions; neither private state is committed to this public repository.

## Proper validation sequence

1. Completely close Geargrafx to clear old RAM. Pick **one** disc configuration for the session.
2. For the experimental hook: boot `Xak_III_English_SUB_TEST_Pilot01.cue` with the matching modified English Track 02 and original 34 Japanese CD-DA BINs.
3. Load **original clean military-camp slot 1**, not the renamed slot 7 and not an older in-scene save. Save filenames might need to match the chosen CUE stem.
4. Progress normally into King Wavis's royal audience to force a fresh scene-overlay load.
5. Note whether `SUB TEST` appears. Save a **new slot 8 during the scene** for [runtime hook verification](pilot-01-disc-hook-no-subtitle.md), which checks both `$8EE5` and `$9C00` in saved CD RAM.
6. Do not test from the frozen slots 6–7 or edit the game's native `STZ $3444` cleanup.

**Status:** Both the prepared disc hook and subtitle renderer remain **unproven in real emulator execution**; the original CD-DA Track 28 identification/timing and disc-byte forensics remain valid.
