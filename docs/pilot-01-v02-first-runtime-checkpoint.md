# Pilot 01 v0.2: all four subtitle sprites survive in the first live audience checkpoint

**2026-10-20 runtime report (analysis of newly uploaded Geargrafx `.state3`).** This is stronger than any previous subtitle test, but **not a confirmed on-screen subtitle**.

### Authenticated checkpoint
- User file name: `Xak_III_English_SUB_TEST_v02_Pilot01.state3`; file SHA-256 `f79c574249d2cdccd29c1cd2769d7e8448a2fd5851521f45b0117c29f17cdcce`.
- Geargrafx v44, disc CRC `EDFD65CB`, CPU PC `$858D`, MPR4 `$82`.
- Patched scene-loop call `$8EE5: 20 00 9C` (`JSR $9C00`) present. Hook code header at `$9C00` matches v0.2. Initialization flag at `$9C99` = `$00` (executed). The original native count cleanup at `$8593: 9C 44 34` is intact.
- Sprite renderer VDC1 `CR=$00CC`, `DCR=$0010`, `DVSSR=$0C00`, latched CR `$00CC`. Sprite rendering is enabled, with automatic SAT-DMA.
- The original **v0.2 glyph font data is present byte-for-byte** in VRAM patterns 30, 31, 43, 56. Nonzero byte counts: 56, 28, 56, 56. This resolves the v0.1 `$7E00` overwrite in the captured state.
- The four correct `Y=271; X=112,128,144,160; pattern SAT2=60,62,86,112; flags=$008F` entries are simultaneously present in **both** the live 512-byte SAT and the shadow SAT-DMA source at VRAM word `$0C00`.
- The exact palette color used is sprite palette 15 / color 15 = VCE color index 511, which is `$01FF` (white). The sprite flag priority bit `$0080` is set (foreground), and the color planes decode to nontransparent pixels. A direct model of scanline 211 predicts **29 opaque white pixels** across the four 16×16 sprites at screen positions x=80–143, y=207–222.
- **But the snapshot's embedded actual frame** has no nonblack pixels in x=80–143, y=207–222. This is an observed discrepancy, not evidence that font or SAT construction failed.

### Crucial capture timing

The CD-DA state is at physical Track 28 elapsed **0.5235 seconds**, compared with original clean scene state `0.4800` seconds. The saved VDC1 `vpos=256`, `raster_line=239`, while the CPU executes the native SAT writer around `$858D`. Thus the screenshot was saved **at the end of a frame, around only 2–3 frames after the original scene entry**. The video image embedded in a save may reflect the prior scanout, while the live SAT and VRAM reflect writes performed at frame end; a frame-phase difference remains a strong, testable possibility. Do **not** claim a proven VDC bug, missing palette, or incorrectly assembled hook without later evidence.

### No patch change indicated yet

The immediate **read-only** experiment is to keep this exact v0.2 disc and clean checkpoint setup, advance the scene **3–5 seconds beyond its beginning**, and record **slot 4** as a later snapshot, leaving slots 1 (clean camp), 2 (clean original audience), and 3 (v0.2 initial audience) untouched. Ask whether `SUB TEST` was visible during those several seconds.

Compare the later state with slot 3: live SAT, shadow SAT, glyph patterns, VCE color 511, hook flag, current VDC registers, and embedded captured frame. Distinguish font eviction, SAT rebuild/removal, render-window clipping, and saved-frame latency before making any new disc patch. The index/pixel model and analyzer are synthetic/local, **not Geargrafx execution**.

No game data/audio, private saved checkpoints or screenshots should be committed to this public repository.

Related: [v0.2 relocated patterns](pilot-01-v02-glyph-relocation.md).
