# Pilot 01: disc-hook SUB TEST not visible, need runtime provenance

**User report 2026-10-20:** the experimental English Track 02 disc hook produced **no visible subtitle** in Geargrafx. It is **not a successful emulator validation** of a subtitle renderer. Do not issue another visual sprite-position tweak until the altered code is shown to execute.

## Offline checks completed

The experimental track remains 54,773,376 bytes with SHA-256 `4024e7bbe27af906d9475a83f97cf3d4a82ddc9ed65b00041d8f84cc5f2e8c51`. Raw indexed MODE1 sectors 518 and 520 contain the patch; the JSR at CPU `$8EE5` changes `20 16 85` to `20 00 9C`, redirecting to `$9C00`. The original `$8593: STZ $3444` remains unchanged. The modified sectors have internally consistent EDC/ECC. The CUE correctly names the patched BIN and preserves the audio filenames and pregaps. The first-64-data-sector disc identity CRC remains `EDFD65CB` and remains compatible with the original military camp save.

The **clean original in-scene** state has `$8EE5: 20 16 85` and blank `$9C00` space, as expected. This verifies the comparator's baseline but **does not prove what the experimental disc loaded at runtime**. Source provenance for the patched call is indexed sector 518; its hook lives in previously blank code-bank data at indexed sector 520. Whether that latter sector is actually transferred into live CD RAM, and whether the normal scene loop uses it, remains unverified.

## Required diagnostic (no ROM modifications)

Start the **experimental SUB TEST CUE**, load the original military-camp slot 1, progress to the royal-audience animation and create a fresh native **slot 8** save *during* the scene, preferably while King Wavis speaks. Preserve original slot 1 and experimental slots. Upload slot 8 for read-only analysis.

From the slot-8 native Geargrafx v44 state, check:

1. Bank MPR4 is `$82`, and `$8EE5` is either **`20 16 85`** (original) or **`20 00 9C`** (patched).
2. `$9C00` starts `48 DA 5A AD 6C 9C C9 FF...`, or is missing/overwritten.
3. `$9C6C` initialization flag equals `$FF` (not observed initialized) or `$00` (consistent with hook having run).
4. VDC pattern words 504–507 have nonzero sprite glyphs, and the eight-byte sprite entries occur in SAT and/or its VRAM DMA source.
5. Scene audio (physical Track 28) and progression remain normal.

These checks separate **patch never loaded**, **redirection loaded but body missing**, **hook loaded but not reached**, and **hook executed but marker overwritten or invisible**. A snapshot is not a CPU trace; use execution breakpoints only after analyzing these bytes.

A private read-only script `tools_hook_runtime_probe.py` was written and passed **five synthetic tests**. The tool does not create a new game patch. Proprietary disc and save-state bytes are not committed.

**Next implementation:** repair the verified failure class, then implement an audio-clock-synchronized subtitle cue. Do not regress to slot 6's `STZ $3444` removal, which caused sprite-counter overflow and a frozen scene.
