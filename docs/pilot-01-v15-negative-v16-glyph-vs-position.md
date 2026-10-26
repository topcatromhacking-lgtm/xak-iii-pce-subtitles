# Xak III v0.15 negative result and v0.16 glyph/geometry isolation

**25 October 2026.** User's real Geargrafx test of `Xak_III_v15_Pixie_REAL_SAT_AB_Ready_To_Test.zip`: **Slots 2–5 look identical; all show native artwork outside the letterbox, and only `SU` / `TE` appears, with `B` / `ST` absent.** v0.15 SAT deletion did not resolve the problem. Do not repeat or promote its native-sprite culling algorithm.

## Verified forensic facts (not hypotheses)

- The packaged v0.15 Slot 2 is **byte-for-byte identical** to the user's uploaded v0.14 glitch-state `Xak_III_English_SUB_TEST_v14_Pilot01.state1`. Both SHA-256: `14f9a90e1b00bb00606b56eb9fe4706b14fce8288fa20e08d57d8ceef603e9bb`. Therefore a missing-letter symptom common to all four v0.15 slots cannot be attributed to v0.15's native-SAT deletions alone.
- The source state **already had only `SU` / `TE` in its embedded screenshot**, even before any v0.15 edits. A saved screenshot does not necessarily represent the same raster timing as a serialized live SAT; the actual user also observed partial text in the emulator after loading.
- VRAM pattern data for all four subtitle glyph blocks **59(`SU`), 56(`B`), 57(`TE`), 58(`ST`) is byte-for-byte identical** between the saved pixie glitch, verified v0.5 early King state, and verified v0.5 later scene state. In this checkpoint, the missing two glyphs are **not caused by overwritten bitmap data**.
- The real v0.14 Slot 4 early-King save has resident horizontal SAT X constants at CPU `$9CA2–$9CA5 = 50 60 50 60` (a −64px shift from v0.11). The **later user pixie glitch** state instead contains `90 A0 90 A0`: the values demonstrably reverted by that later checkpoint. This is evidence of **nonpersistent state-only geometry** across the scene/module lifecycle, although the exact code load that restored the values has not yet been traced.
- The real pixie save still has four live subtitle SAT entries in indices **3–6**, with font words `76 70 72 74`, Y native screen 184 and 204, and X source constants `90 A0`. The native 3 SAT entries are separate; v0.15 changed only their live and/or shadow SAT Y words, which may immediately be rebuilt by native game code.

## v0.16 isolated missing-glyph root-cause test

Using the **same real SHA-pinned v0.14 pixie glitch** state, a unique **private** ZIP `Xak_III_v16_Glyph_vs_Position_Ready_To_Test.zip` was constructed containing a new 35-track v0.16 CUE referencing the unchanged verified v0.10 English Track02 and original Japanese CD-DA, source code, 16 passing regression tests, a JSON audit and four native save states. New CUE: `Xak_III_English_SUB_TEST_v16_Pilot01.cue`.

- **Slot 2**: byte-identical unchanged baseline (0 bytes).
- **Slot 3**: exchange only subtitle PAT word positions between left and right columns — SU ↔ B and TE ↔ ST — in the 4 resident code pattern references **and** four live subtitle SAT pattern words (8 bytes changed). If the missing glyphs become visible in the previously visible *left* positions, disappearance follows the horizontal column, rather than which VRAM font pattern is selected.
- **Slot 4**: shift both sprite columns 16px left using both code X constants and live subtitle SAT X words (8 bytes changed).
- **Slot 5**: restore **v0.14 Slot 4's exact −64px correction** in those same code constants and live SAT X values (8 bytes changed). Tests whether immediately restoring the lost position data improves the pixie scene.
- **Absolutely no native SAT deletion or blanking**, VRAM bitmap changes, palette changes, disc-code modification or Japanese CDDA changes in any variant. All original save states remain untouched.

Source SHA pin, CPU code guards and exact allowed-byte-change audits passed. The ZIP was CRC-verified after its final update and all **16 local synthetic tests**, including the real pinned checkpoint when available, passed. A runnable source builder and test script are included in the **private user ZIP**, but user-derived native save states are **not published** on GitHub.

**Emulator result pending.** Test Slots 3, 4, 5 in that order; evaluate live frames after loading rather than unchanged thumbnail. If no variant differs, that would indicate that the game's ongoing state/module reload and SAT rebuilding defeat static post-save edits; the next step should be a **disc-native persistent source patch** for the verified `$9C9A–$9CAD` subtitle fields and/or a dynamic raster/SAT writer diagnostic, **not** another indiscriminate sprite cull.

## Production target unchanged

v0.11 two-line subtitle layout in the lower black band, **v0.14 Slot 4's successful widescreen/4:3 placement**, properly masked native character bodies and mouth, sound untouched, English text synchronized to the voiced King Wavis scene. v0.10 remains the stable **disc-level** rollback. Obtain approval before external GitHub comments or outreach.