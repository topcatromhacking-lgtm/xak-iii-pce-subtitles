# Pilot 01: v0.14 Slot 4 confirmed — proceed with native-sprite clipping research

**25 October 2026.** The user clarified that **all six screenshots were recorded with v0.14 Slot 4** (the −64-pixel horizontal adjustment), **not** baseline Slot 2.

## Confirmed real-emulator results

- **Subtitle centering and legibility:** user reports all subtitles work, including the previously shifted 4:3 scenes, and **no new glitches** in v0.14 Slot 4. The 64-pixel compensation is the accepted visual reference.
- **Remaining artifacts:** six examples of **native character sprites crossing intentionally blank upper/lower letterbox areas**, not broken font or the new horizontal correction:
  1. Pixie's full sprite body is visible above/below the intended image instead of clipped by the black band.
  2. Hero's legs or lower body extend into the bottom black band.
  3. A tiny isolated animated mouth appears in the top/right black margin.
  4. A walking NPC's lower body extends into the bottom band.
  5. Another shot of the same lower-body overflow.
  6. The pixie's lower body similarly extends beyond the intended picture.
- v0.11 still provides the successful **two-line lower-band sprite subtitle design**; v0.10 remains the last clean-scene-tested BIN/disc rollback.
- v0.12's background-blanking override produced duplicated artwork, so **do not revive v0.12/v0.13 as the main rendering path**.

## Hardware and saved-state findings

Read-only inspection of the **authentic v0.14 Slot 4** checkpoint shows four appended font sprites (SAT patterns `$76,$70,$72,$74`), all still stored with their old v0.5 live SAT coordinates **until subsequent scene-loop refreshes the SAT**. The code constants already contain the tested Y184/Y204 and X−64 positioning. **The stored early-King state contains no native character SAT entries at its sampled instant**. Accordingly, an edit to that existing state cannot reproduce or classify the six later native sprite leaks.

Geargrafx HuC6270 renders lower SAT indices on top of higher indices, supports 16/32/64-pixel native sprites, and processes at most sixteen sprite subcells per scanline. A brute-force black mask or simply disabling all sprites would risk occluding the desired subtitle and removing valid character artwork.

## v0.15 source-only static SAT diagnostic

A standalone, fail-closed **source-only** builder has been packaged privately as `Xak_III_v15_Native_Sprite_Clipping_Diagnostic_Source_Only.zip`. It contains a native Geargrafx v44 state inspector and creates a unique CUE and independent save slots based on **a new actual v0.14 Slot4 glitch-frame state**. No game files or saved states are included. **Twelve synthetic tests pass**, and input validation of the original v0.14 Slot4 early-King saved state succeeded.

The tool refuses a source without native sprites and compares:
- **v0.15 Slot 2:** exact reference state
- **Slot 3:** remove only *native sprites wholly outside the y50–177 picture field*
- **Slot 4:** remove all native sprites **touching either** upper or lower letterbox (aggressive diagnostic)
- **Slot 5:** remove native sprites extending into the lower black band

Only the selected native SAT Y words in live SAT and the VDC1 SATB DMA VRAM shadow are moved offscreen; the four subtitle sprites are explicitly protected; program code, the working v0.10 Track02 and all Japanese CDDA are unchanged. This is **not** a permanent fix: the game may rewrite SAT the very next frame, and hiding any native sprite intersecting the picture edge could remove legitimate art. The test isolates root causes rather than prescribing a release algorithm.

### One new input needed

**Capture one real glitch-frame state, not another screenshot:**

1. Open `Xak_III_English_SUB_TEST_v14_Pilot01.cue` and load **Slot 4** (already proven centered).
2. Advance to one of the six observed glitches, ideally the tiny stray **mouth** or exposed **pixie body**.
3. While the offending sprite is visible, save the scene as **v0.14 Slot 1**, which was unused by the delivered v0.14 test package. Avoid overwriting Slots 2–5.
4. Upload `Xak_III_English_SUB_TEST_v14_Pilot01.state1` (native Geargrafx 749,238 bytes). This is the actual source needed to identify the offending native SAT indices and test suppression reproducibly.

Once a glitch state is received, derive privately the corresponding four ready-to-load v0.15 states, inspect all native sprite indices and whether they traverse y50/y178, then select a minimal long-term engine modification (per-frame SAT filtering or appropriate per-line sprite isolation). Do **not** globally enable background tiles again.

**Release objective:** v0.11's visually successful two centered lines in the lower black band, position corrected as v0.14 Slot4, without exposed mouth/legs/pixie and without corrupting native scene art, before replacing `SUB TEST` with audio-timed King Wavis dialogue.

**External communication:** no third-party outreach or GitHub comments/issues without user's prior approval.
