# Xak III Pilot 01 — v0.5 runtime passed; early King speech uncovered

**Geargrafx 1.8.4 / v44, October 24, 2026.** Genuine user-supplied `.state1`, `.state2`, and `.state3` were inspected read-only. No source saves, embedded framebuffers, or proprietary video/audio bytes are included here.

## v0.5 successfully repairs the persistent `SU` corruption

The unique v0.5 CUE and source-only builder created a valid new data Track 02 with SHA-256 `a87babc4dafa0f43091015b86014036978940fdf3c44048409727a0f9acdc207`. The user's real emulator playback reports that `SUB TEST` is readable through the remainder of the cinematic without the persistent `SU` damage seen in v0.4.1.

### Snapshot validation

The actual Geargrafx v44 layout places VDC1 VRAM at file offset `0x48C67`; a 16×16 sprite's 128-byte data occupies `VRAM + 128 × pattern ID`. The live SAT follows the 64 KiB VRAM and VDC registers. Comparison establishes:

| Real native state | CDDA Track 28 elapsed | Pattern 43 | Patterns 56–58 | Pattern 59 | Subtitle SAT |
| --- | ---: | --- | --- | --- | --- |
| v0.4.1 Slot 3 | **14.4639 s** | Original `SU` glyph | Intact | Empty | Original sprite references 43/56/57/58 |
| v0.4.1 Slot 4 | **32.3324 s** | Overwritten | Intact | Empty | Original sprite references |
| v0.4.1 Slot 5 | **72.5824 s** | Overwritten | Intact | Empty | Original sprite references |
| **v0.5 Slot 2** | **74.3040 s** | Overwritten by game | Intact | **Original `SU` glyph intact** | All four expected 59/56/57/58 entries present |
| **v0.5 Slot 3** | **129.9988 s** | Overwritten again | Intact | **Original `SU` glyph intact** | All four expected entries present |

The complete 128-byte glyph in pattern **59 is byte-identical** across the two v0.5 checkpoints and matches the old clean pattern-43 glyph from v0.4.1 Slot 3. This is a clear verified success of the relocation; intermediate frames cannot be exhaustively proven from saves alone. Native Japanese speech/CD audio continues.

In v0.5 Slot 2, the framebuffer shows characters in the foreground obscuring portions of `SUB TEST`; Slot 3 displays complete text again. CR remains `$00CC`, and all four subtitle SAT entries remain present. **There is no evidence of VRAM font overwrite at either v0.5 point.** The exact occlusion mechanism (game-native sprite priority, black image masks, raster/window behavior, or combinations) still requires tracing; do not label it a font failure.

The original military-camp state is preserved in v0.5 Slot 1. Geargrafx scopes its five state slots by unique CUE filename; preserve that convention.

## Why the first King's spoken line is not subtitled

**A previously analyzed v0.4.1 Slot 2 is actually already 9.3999 seconds into Track 28**, not before playback. It has:
- `MPR4=$85`;
- the new hook's bytes are resident in CD RAM, but the first-invocation flag at `$9C99` is still **`$FF`**, meaning the patch has not executed;
- the existing redirection `$8EE5: JSR $9C00` is present in the CD RAM's bank-82 code copy.

By v0.4.1 Slot 3 at **14.4639 seconds**, `MPR4=$82` and the first-invocation flag has become **`$00`**, matching successful execution and visible text. Later scenes switch MPR4 again (e.g. `$84` at 32.33s) while preserving the initialized hook flag.

**Consequence:** the v0.5 marker has a demonstrated **coverage gap in the opening segment**. We cannot fix the King's first speech merely by moving X coordinates or adjusting a static audio time. We need an earlier execution path or scene-phase dispatcher, correctly integrated with bank switching, and explicit title/display cleanup. The exact code address for that earlier phase is **not yet verified**.

## v0.6 engineering direction

1. **Early-scene provenance first.** Save a v0.5 **Slot 4 while King Wavis is actually speaking his first line**, before the hero responds, keeping Slots 1–3 unchanged. Inspect PC, MPRs, VDC, resident code and initial flag; map active code to disc sectors before modifying a new hook. Reuse the existing validated patch only where it is truly executed.
2. **Keep verified glyph lifetime fix.** Maintain pattern 59 for `SU` and patterns 56–58 for the remaining glyphs. No repeated 512-byte VRAM upload.
3. **Scene-aware presentation.** The cinematic's VDC1 HDR changes between `$0C0F` and `$041F`; avoid fixed coordinates that become obscured by native scene sprites/masks. Resolve the effective active region and sprite priority through a raster- and SAT-aware display path.
4. **Actual spoken-line subtitle.** Anchor the first English caption to physical Track 28's confirmed audio, add correct on/off timing, and preserve skip/transition cleanup and original Japanese voices.
5. **Reversibility.** Create new v0.6 CUE, own five save slots, verified source BIN hash, and checksum-corrected MODE1 sectors; never overwrite v0.5.

Reference for related implementation lessons: [Xak I & II subtitle patch](xak-i-ii-subtitle-technique-comparison.md); preceding experiment [v0.5 design](pilot-01-v05-glyph-lifetime.md).

**No new v0.6 game patch has been built or tested.** The read-only snapshot comparison is independent of runtime emulation.
