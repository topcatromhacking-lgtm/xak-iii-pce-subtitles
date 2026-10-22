# Xak III Pilot 01 v0.4.1 — centered subtitle visibility probe

**2026-10-21. Source-only diagnostic: 9 offline tests pass; real emulator rendering unverified.**

## New evidence from the actual v0.3 framebuffer

The original, unmodified visual scene at 14.43 seconds into physical Track 28 occupies approximately **screen X=64–191** with black side regions. v0.3's subtitle sprites were placed at SAT X=112,128,144,160, but Geargrafx's captured framebuffer places those four 16px glyphs at **screen X=144–207**. The final glyph, corresponding to the ending `ST` of `SUB TEST`, lies **entirely to the right of the displayed scene area**, explaining the visible `SUB TE` without requiring a missing font. This is consistent with the user's observation of black masking moving over the subtitle during the animated scene. The save only captures one frame and **does not yet establish whether the black area is an overlay object, scene crop, raster-display control or another masking mechanism**.

Separately, the striped distortion below the character in v0.3 is absent in v0.2. This correlates with repeatedly uploading glyphs to sprite patterns 30 and 31, whose VRAM word addresses also lie in the background attribute table. These are **two distinct problems**; do not conflate the original black masks with the new bottom stripe artifact.

## v0.4.1 diagnostic build

A separately packaged **source-only** builder creates a new test directly from the **verified v0.3 Track02**, SHA-256 `d87e285018b89416f18bfdc6c9af10e2251aa3234170383deefdcbc6616f0b32`. The input is the user's authorized BIN plus v0.3 CUE. The v0.4 build does not need to be generated or tested first.

It combines the previously prepared v0.4 stability changes with a third independent change:

1. Restore one-time font initialization by changing CPU `$9C08` from two NOPs back to `BNE +$41`, avoiding 512-byte glyph reuploads on every scene loop.
2. Move glyph patterns from `30,31,43,56` to `43,56,57,58`; adjust matching SAT2 references. New positions were checked as non-colliding with the visible tilemap rows in recorded states, not proven safe at all cinematic times.
3. **Center glyphs inside the original scene image**: change CPU `$9CA2–$9CA5` SAT X coordinates from `$70,$80,$90,$A0` (112,128,144,160) to `$40,$50,$60,$70` (64,80,96,112). Predicted screenshot text X becomes **96–159**, leaving 32px margins within observed 128px viewport X=64–191.
4. Retain Y=128, all other native sprite code, the scene-loop hook, and crucially original `$8593 STZ $3444`.
5. Regenerate MODE1 EDC/ECC for **raw sector 745 only**. All other data and original Japanese audio tracks remain unchanged. Export delta IPS and SHA-256 manifest; never overwrite existing files.

The unique `Xak_III_English_SUB_TEST_v041_Pilot01.cue` gives v0.4.1 a separate namespace for **five Geargrafx save slots**. The builder copies a specifically verified clean camp `.state1` if found.

**Nine tests passed on a full-sized synthetic Track02** (hash guards mocked only to exercise code execution; real user-owned BIN is checked strictly when building). No actual v0.4.1 Track02 or emulator screenshot has been created in this development environment, so rendering remains **unverified**.

### Follow-up test and branch

Launch v0.4.1 from clean camp Slot 1. Enter King Wavis scene, watch 15–20 seconds. Note whether all of `SUB TEST` remains visible, the stripe artifact is gone, and any growing black mask blocks the letters; save into v0.4.1 Slot 3 for further VRAM/CR analysis. If the black mask still occludes centered text, the next intervention is tracing Xak III's own raster/window state and comparing to Yuna 2's raster-based subtitle display handling, not another blind glyph relocation.

Related: [v0.4 hypothesis](pilot-01-v04-stability-probe.md), [v0.3 initial rendering experiment](pilot-01-v03-visibility-probe.md). Source inspiration: [Yuna 2](https://github.com/suppertails66/yuna2tools/blob/master/yuna2/asm/scene_main.s), [Emerald Dragon](https://github.com/suppertails66/emdrtools/blob/master/emdr/asm/generic/scene/scene_std.s). Never publish copyrighted disc files or private save states.
