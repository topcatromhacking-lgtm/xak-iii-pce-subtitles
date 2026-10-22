# Comparative engineering reference: Xak I & II PC Engine English patch

**Reference checked: October 22, 2026**

- [randomprojectsfactory/xak-i-ii-pce-english](https://github.com/randomprojectsfactory/xak-i-ii-pce-english)
- [Development notes](https://github.com/randomprojectsfactory/xak-i-ii-pce-english/blob/main/DEVELOPMENT.md)
- [Changelog](https://github.com/randomprojectsfactory/xak-i-ii-pce-english/blob/main/CHANGELOG.md)
- [README](https://github.com/randomprojectsfactory/xak-i-ii-pce-english/blob/main/README.md)

## Verified public properties of the reference

Xak I & II is a different game compilation and a **29-track** CD image. Its localization modifies raw **data Tracks 02 and 05**, retaining the other 27 tracks, original Japanese voice and CD audio. The repository contains two published binary **xdelta** patches, hashing/patching scripts, screenshot examples, and high-level development notes. Its public tree **does not provide original assembly sources, an annotated scene-disassembly listing, or a standalone subtitle-engine implementation**.

Its 2026.10.19.1 changelog explicitly identifies corrections for corrupted cinematic subtitle graphics and scene fragments, misplaced save/load HUD screen bands, and backup-memory return transitions. The development document describes:

- In-game scene and speech-event subtitle triggers, cleanup at transitions and skip boundaries, and distinct CD-DA/ADPCM timing analysis.
- Subtitle graphics rendered using the game's **native tile/palette/scrolling/scene-update pipeline** rather than an external video overlay.
- Staged tile/palette updates and corrected display handoffs to prevent transient wrong pixels.
- Letting native raster/display interrupts continue during larger-font drawing and uploads.
- Display-sensitive backup-memory operations that retain critical interrupt-based screen splits and restore bank mappings.

The README claims hardware validation on PC Engine GT and SuperGrafx/Turbo EverDrive Pro. These are the other project's **reported** results, not reproduction in our Xak III environment.

## Mapping to our actual Xak III observations

| Xak III problem | Relevant lesson | What is established vs. unknown |
| --- | --- | --- |
| `SU` font pattern 43 overwritten by ~32.33s into Track 28 | Respect **lifetime/ownership** of VRAM allocations, not just empty snapshots | v0.5 moves `SU` to pattern 59; it is empty in three states but might still be written between captures |
| v0.3 BAT rows damaged by per-loop 512-byte font uploads | Stage graphics writes, avoid live BAT/pattern collisions, refresh only at safe scene transitions | Earlier Xak III corruption is verified; scheduling remains to be implemented |
| VDC HDR changes between 128px and 256px scene presentation | Preserve raster interrupts and account for active viewport/window per scene | Xak III's exact interrupt logic and VDC2/mixer relevance still need direct tracing |
| Speech begins before our static `SUB TEST` marker | Hook real scene/speech events rather than relying solely on a free-running renderer | Physical Track28 and scene entry are confirmed; spoken-line segmentation and subtitle display time are not yet authored |
| Subtitle may persist after a shot or skip | Explicitly clear or hide subtitles during native scene transitions and on skip | Future architecture required |

## Recommended implementation order

**Do not alter the pending Xak III v0.5 runtime test.** Its main purpose is isolated: determine whether moving only the overwritten `SU` pattern from 43 to 59 stabilizes the full cinematic without introducing other graphics damage.

**After v0.5:**

1. **VRAM ownership map:** trace writes over time in the King Wavis sequence, including DMA and native decompression, and reserve stable backing graphics space. Compare before/after subtitle bytes and scene background. Do not assume patterns 57–59 are universally available.
2. **Staged uploads:** upload/double-buffer font or composed subtitle tiles at safe frame boundaries; preserve the game's raster IRQ and its ordinary SAT cleanup. Avoid continuous 512-byte VRAM writes from the scene-loop hook.
3. **Scene-aware display window:** measure changes in VDC HDR/CR and relevant line/window control at exact subtitle scanlines; derive horizontal positioning and crop/mask rules from active width.
4. **Audio-driven scripts:** maintain Track 28 Japanese audio, create a timed English caption event table anchored to verified audio and scene events; subtitle appearance/clearing and skip cleanup must be explicit.
5. **Regression:** continue the unique CUE-per-build five-slot Geargrafx system, verify 35-track disc / MODE1 EDC/ECC integrity, then test across multiple shot changes and from clean boot.

## Portability constraints

Xak I & II's binary patches are **not** compatible with Xak III's 35-track release or our NightWolve translated Track02. No source-level reuse is possible from the public files as published. The techniques are strong *design evidence*, not proof the three Xak games share the same cutscene engine, VRAM map, bank conventions or raster IRQ addresses. No claim of actual Xak III v0.5 display success is made here.
