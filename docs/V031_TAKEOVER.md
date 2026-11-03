# Xak III v0.31 — continuation and v0.30 freeze

3 November 2026. The inherited `grokbot/subtitle-pipeline` branch and draft PR #1 are intact. Development happens on the separate `chatgpt/v031-stabilization` branch, starting from commit `7be17f6`. No native game data, audio, or previous save states were modified.

## VS1 baseline

The user provided the v0.30 VS1 patch and a screenshot sheet showing real, two-line English subtitles across different cinematic compositions. The branch documents 55 timed cues (56 script records including one skipped system-text record), a runtime bank-$83 engine, an original proportional font, black-band masking by 8 native-sprite-budget blocker sprites, width-mode raster hooks and a calibrated 59.7168 FPS / 0.228-second offset. The previous collaborator reported Mednafen success and examined 4,566 frames. The screenshot is not a hardware validation or complete independent timing audit.

An independent metadata pass on the uploaded xdelta succeeded: 210,217 bytes, SHA256 `9a36d3ca5d2adf2f388c7afbb271b9c36169e2f649407a0be0744810dda6246e`, 7 valid VCDIFF windows, output 54,773,376 bytes. Its application header names clean Japanese Track 02. Full xdelta decoding and source/output hash comparison are NOT yet verified in this environment: the original clean 54,773,376-byte Track 02 and xdelta3 decoder are not available. Do not claim a fully reproducible release until these are tested.

`tools/verify_v030_release.py` checks patch identity and parsed metadata without copyrighted data. With the clean source and `xdelta3` it additionally checks clean-source SHA256, decodes to a **temporary** file, confirms the 225-sector pregap stays unchanged, and validates EDC/ECC for every changed Mode1 sector. `tests/test_verify_v030_release.py` covers corruption and VCDIFF parsing.

## Current scene coverage (public TSV)

| Scene | Physical CD track | Records | Timed cues | Readiness |
|---|---:|---:|---:|---|
| VS1 | 28 | 56 | 55 | Runtime reported verified; text remains `DRAFT`; inspect `VS1-005 ???`, `VS1-056 ...`, `Mt. Fuji` and six possible timing anomalies. |
| VS2 | 31 | 11 | 2 | 9 cue timing gaps; some are text-box sequences, not necessarily voiced. |
| VS3 | 32 | 12 | 6 | 6 cue timing gaps; long monologue remains draft. |
| VS4 | 29 | 1 | 1 | Only one cue; verify dialogue/script coverage before claiming scene complete. |
| VS5 | 33 | 1 | 0 | Audio transcription and timing missing. |
| VS6 | 34 | 1 | 0 | Audio transcription and timing missing. |
| VS7 | 30 | 1 | 0 | Track 30 confirmed in current engine notes (Track 35 instrumental); audio transcription/timing missing. |

`tools/audit_cutscene_progress.py` prints current counts and flags unfinished cue IDs and explicit placeholders. It never invents dialogue or timing. This is a **readiness audit**, not an in-game test or a replacement for listening.

## Follow-on work, in order

1. **Preserve VS1 v0.30.** Run the full patch verifier when clean Japanese Track 02 becomes available; record decoded output hash. Retain the working visual configuration without silently changing timing, sprite budget, or raster hooks.
2. **Close VS1 gaps.** Listen to the actual Track 28 around `VS1-005`, inspect the exact Japanese transcript for `Mt. Fuji`, compare six transition times with recording frame numbers, and confirm scene reload/one-frame transition behavior in Mednafen and Geargrafx. Do not guess dialogue.
3. **Inventory VS2 before timing.** From physical Track 31 audio, distinguish voiced cuts from game dialogue boxes, then collect a near-scene native state and validate free bank-$83 memory, the bank-$81 code cave, VRAM patterns and palettes. The current builder cannot be safely reused for other scenes without this validation.
4. **One scene at a time:** VS2 through VS7, each with a dedicated cue script, alignment, clean patch, scene-specific screenshots/reviews, and independent checks. Preserve Track28 and the original Japanese CD-DA unchanged.
5. **Long-term:** regression tests on scene transitions, save/load, real console sprite priority / raster timing, plus full-disc patch only after all scenes pass.

Do not merge draft PR #1 into `main` until its description and completed tests reflect actual integrated runtime status; the PR currently describes an unintegrated prototype. User approval is required before contacting third-party authors or making comments on third-party repositories.
