# v0.20 actual Geargrafx result → v0.21 isolate native pixie sprite trimming

**27 October 2026.** The user tested the v0.20 **Slot 4** *real emulator*, confirming:

> Slot 4 erased the two left wings from pixie and her mouth; it hides a little more of the body.

## Interpretation

- **Positive:** native producer-level interception **visibly changes** pixie sprites; the hook is not merely rewriting an inert live SAT or hidden SAVESTATE table. At least some sprite filtering/minimization is happening in the tested scene.
- **Negative:** deleting two visible wings and the mouth is *unacceptable artwork loss*. The remaining pixie body is only *partly* concealed. **Do not declare clipping fixed.**
- Unconfirmed: whether the artwork loss is caused by native 64→32 trimming, native 32→16 trimming, the shared whole-outside rejection rule, a scene-specific crop boundary error, or combination. We need separate controls.
- No result for v0.20 Slot 3 or Slot 5 was reported, nor definitive statement about subtitle glyphs in this test; do not invent their outcomes.

## v0.21 ready-to-load A/B experiment

Private ZIP in conversation: `Xak_III_v21_Pixie_Native_Trim_Isolation_Ready_To_Test.zip`.

- **ZIP SHA-256** `579fba796975847fb12b1c7f7bdcbe2fed04f52388db6ad3712dec51f90db72c`; archive CRC and all 11 files verified.
- **Exact input:** user-tested `Xak_III_English_SUB_TEST_v20_Yuna_Pixie_Pilot01.state4`, SHA-256 `32bf29092d0d3a1195d01b40e1a501fde0bcb6609c80760b35ee5239846140bb`.
- The four state files reference the **unchanged user's own v0.10 35-track CUE and Track 28 original Japanese audio**. No BIN/audio bundled or modified.
- All variants retain the native producer hook at `$84F0 JMP $7700`, original native whole-outside rejection, original enqueue/accept path, successful v0.16 Slot 5 X geometry (`50 60 50 60`) and independent four subtitle sprites.
- v0.20 helper contains a single `JSR trimTop32` at **`$773B`** and a single `JSR trimTop16` at **`$7752`**. Their target subroutines live at `$77AA` and `$77DE`, respectively. The code after trimming proceeds via `after_top=$7762`.
- To isolate the two reductions, v0.21 changes each selected 3-byte **`JSR` to `JMP $7762`**. This removes a selected trim *without changing any full-outside sprite rejection* or subtitle logic.

| State | Code sites changed | Native trimming left enabled | Actual bytes changed |
| --- | --- | --- | ---: |
| Slot 2 | none; byte-identical v0.20 Slot4 reference | both | 0 |
| Slot 3 | `$773B: 20 AA 77 → 4C 62 77` | 32→16 only | 2 |
| Slot 4 | `$7752: 20 DE 77 → 4C 62 77` | 64→32 only | 2 |
| Slot 5 | both `$773B` and `$7752` | neither; still reject fully hidden | 4 |

Subtlety: disabling the 32→16 operation also prevents the second pass of an already 64→32 minimized candidate; this is expected and must be considered when interpreting results.

### User test and decision tree

Extract the standalone v0.21 ZIP into the original v0.10 game folder, launch `Xak_III_English_SUB_TEST_v21_Pixie_Trim_Isolation.cue`, and load Slots **2,3,4,5** briefly. Compare the **two left wings**, **mouth**, **lower-body overlap**, full **SUB TEST** glyph rendering, and native animation. Ignore saved thumbnails when deciding.

- Wings return in Slot 3 but not 4: a 64→32 crop is implicated.
- Wings return in Slot 4 but not 3: a 32→16 crop is implicated.
- Wings return only in Slot 5: the two reductions interact.
- Wings absent throughout: more likely whole-outside rejection, erroneously static `Y=50` boundary or another producer path.
- Hiding slightly more body with wings lost is *not* an acceptable optimization. Favor sprite preservation and refine the dynamic crop boundary / independent raster subtitle windows once culprit identified.

### QA and restrictions

- **20 offline regression tests passed on the exact private state**: 0/2/2/4 changed bytes only, code targets verified, Y/X unchanged, original native reject/accept bytes unchanged, zero VDC/SAT/VRAM changes, subtitle code untouched, original native state header intact.
- **No real v0.21 Geargrafx test yet.**
- Original disc/saves, Track 28 audio, and existing v0.10/v0.14/v0.16/v0.17/v0.19/v0.20 rollback namespaces untouched.
- Source-only builder, its v0.20/v0.19 dependencies, 20 tests, report, and 4 private states are bundled in the conversation ZIP. No user proprietary data uploaded to GitHub.
- The Pixie frame's fixed `Y=[50,178)` is an observed picture extent, *not* a universal cinematic runtime parameter. Subsequent production code must acquire scene-specific crop bounds and preserve flipped sprites, correct 32/64 pattern layout and animation, and a pixel-clean subtitle band.
- No third-party comments/issues/outreach without prior user approval.
