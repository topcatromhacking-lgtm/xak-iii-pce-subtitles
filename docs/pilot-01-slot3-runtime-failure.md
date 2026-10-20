# Pilot 01: Slot 3 runtime failure (video review)

**2026-10-20.** The user supplied a **20.6-second Geargrafx recording** of the corrected `slot 3` test. The initial green status message confirms **"State loaded from slot 3"**. The King Wavis audience scene then plays, advances through portrait changes and a Latok close-up, and exhibits no visible interruption.

**Result:** the white `ENGLISH SUBTITLE` marker is **never visible**, despite the intended initial draw at roughly native-screen coordinates (64,207). This is the **second failed runtime test**, after slot 2. Do not describe this save-state technique as demonstrated/working.

## What is and is not known

- The private slot-3 state does contain nonzero glyph patterns in VDC1 VRAM, eight nonzero live SAT entries, and the same entries in the automatic SAT DMA source.
- A verified original-vs-patched snapshot comparison establishes those bytes before restoring emulator execution. This is **not** evidence that Xak III preserves or uses them after its first VBlank.
- The recording confirms the user loaded slot 3 successfully and played approximately 20 seconds. We cannot determine exact VDC writes or display rejection from the video alone.
- Possible explanations include a later VRAM/SAT rewrite by the cutscene engine, changes to VDC control/display state, offscreen placement due to game-specific active-picture mapping, or a sprite encoding issue.
- Continued guessing and creating more patched states without hardware-state evidence is counterproductive.

## Next diagnostic (no new patch)

1. Restore **slot 3** with the English split-track disc.
2. Let the game advance **approximately one second**. Then save the current game state to a new **slot 4** (do not overwrite slots 1 or 3).
3. Compare v44 Geargrafx VDC1 data between the supplied slot 3 and resulting slot 4. Inspect VDC1 CR (`$00CC` at initial snapshot), DCR (`$0010`), DVSSR (`$0C00`); the 512-byte **live SAT**, the 512-byte source at **VRAM word $0C00**, and the eight sprite-pattern IDs `504,505,506,507,30,31,43,56`.
4. If both glyph patterns and live SAT persist in slot 4, investigate VDC active-area offsets, sprite hardware encoding, and sprite priority/visibility in the **Geargrafx debugger's video/sprite viewer** instead of assuming RAM was overwritten.
5. If they disappear, trace writes to the specific VRAM/SAT region. Only after proving the actual update mechanism should we design an executable scene hook.

The original Japanese Track 28, scene audio alignment, game data and original slot 1 checkpoint remain preserved.

The video and private state binaries are **not** uploaded to this public repository.

### Supporting source

- [Geargrafx native debugger and VDC viewer](https://github.com/drhelius/Geargrafx)
- [Geargrafx VDC sprite rendering, SAT DMA and VBlank code](https://github.com/drhelius/Geargrafx/blob/main/src/huc6270.cpp)
- [Previous slot 3 DMA correction analysis](pilot-01-sat-dma-v2-diagnostic.md)
