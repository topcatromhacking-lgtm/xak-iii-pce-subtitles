# v0.15 — actual pixie-glitch saved-state forensic results and SAT A/B

**2026-10-25. Read-only forensic analysis complete; real A/B emulator result pending.**

The user uploaded the previously requested native Geargrafx v44 `Xak_III_English_SUB_TEST_v14_Pilot01.state1`, **749,238 bytes**, SHA256 `14f9a90e1b00bb00606b56eb9fe4706b14fce8288fa20e08d57d8ceef603e9bb`. The private state and its embedded screenshot remain outside GitHub. The screenshot embedded at serialized byte offset `503278`, 256×240×4 RGBA, displays **the actual pixie/body overflow** and the two-line `SU / TE` letterbox caption.

### Important correction to the planned source-only v0.15 diagnostic

The earlier builder required resident subtitle X table `$9CA2–$9CA5` to equal `50 60 50 60` (v0.14 Slot4), and presumed native SATB and live SAT contain the same native entries at the same indices. **Both assumptions fail in this actual, relevant saved state.**

- Resident raster callsite `$65AA = 20 DF 76 EA EA` and lower-band diagnostic helper `$76DF = 29 3F 1D 72 3E EA EA 09 40 60` are present.
- Stable glyph pattern references `$9CAA = 76 70 72 74` and native subtitle Y table `F8 F8 0C 0C 00 00 01 01` are present.
- **Resident X table is `90 A0 90 A0`**, not the earlier edited `50 60 50 60`. The save may have been taken after native module code/data was reloaded. This indicates we need to investigate persistence of the v0.14 horizontal correction in later scene transitions, without contradicting the user's earlier successful visual comparison. We do not change X in the new diagnostics.
- **Live VDC1 SAT:** exactly 3 native sprites, indices **0,1,2**, all start at screen Y **−12**, then 4 subtitle entries, indices **3,4,5,6**, at actual Y **184/204**, stored X **112/128**, glyph PAT words `$76/$70/$72/$74`.
- **VDC1 VRAM SATB shadow:** **9 different native sprite entries**, indices **0–8**, with original Y values **−3 to 77**, various widths and heights; *no subtitle entries* at these indices. Sprite locations and pattern IDs differ from the live SAT. The debugger snapshot and already-rendered thumbnail need not represent the same instant in the native scene's frame update; do not assume the currently listed SAT generated every visible pixel in the saved screenshot.
- Saved VDC1 SATB source remains `$0C00`, which is verified.

This means the earlier global y50–178 native sprite cull could be both ineffective and destructive. **Do not run the older generic source-only v0.15 builder on this checkpoint; use the new A/B package instead.**

### Exact private v0.15 A/B artifact

New private download `Xak_III_v15_Pixie_REAL_SAT_AB_Ready_To_Test.zip`, generated exclusively from the exact user state and the existing public v0.14 CUE, includes unique new CUE, v0.15 Slots 2–5, JSON inspector report, a Python builder and 15 synthetic regression tests. The archive passed ZIP integrity checking (SHA256 `00ac797460ea1fe424ea07428a1506d34e88f3f63cb1d0d702ed5aa0c5dd081a`).

- **Slot 2:** exact original glitch state, unchanged.
- **Slot 3:** set offscreen Y `$03FF` for **3 native live SAT entries**, indices `0,1,2`, without touching shadow.
- **Slot 4:** set offscreen Y `$03FF` for **9 native shadow SATB entries**, indices `0–8`, without touching live SAT.
- **Slot 5:** set offscreen Y in both native groups.

Diff sizes: **0 / 6 / 18 / 24 bytes**, respectively. All edits target live SAT or VRAM SATB Y words only. Every live subtitle entry remains untouched, as do CD RAM code and subtitle X/Y tables, embedded screenshot, CPU registers, v0.10 game BIN/CUE, Japanese audio, and prior save namespaces. **15 synthetic tests pass**; the four private derived states were hash-checked. The embedded screenshot is intentionally not edited; emulator test must inspect the **live output after loading and running frames**, not the thumbnail.

### Expected interpretation

If Slot 3 changes the glitch, active SAT is implicated. If Slot 4 or 5 changes the glitch, the pending SATB shadow/DMA path is implicated. If none changes the visible output after advancing frames, the game's native **per-frame SAT update, sprite buffering or raster timing** may immediately restore entries. Such a negative result cannot prove that character-sprite clipping is not involved. A partial fix or missing character art is diagnostic **only**; indiscriminate native-sprite deletion is not our intended production solution.

**Next step:** user compares Slot2/3/4/5 briefly at the same pixie scene and reports whether pixie overflow disappears, subtitles remain, and native animations survive. Then design a per-frame **subtitle-aware sprite selection or masking mechanism** rather than a permanent brute-force SAT mask.

Keep preferred visual baseline v0.14 Slot4 and verified disc rollback v0.10. No communication with third-party authors was initiated; obtain user approval before external outreach.
