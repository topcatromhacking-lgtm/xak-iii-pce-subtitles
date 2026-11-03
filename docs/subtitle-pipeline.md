# Subtitle pipeline (branch `grokbot/subtitle-pipeline`, 2026-11-03)

This is the groundwork for real English subtitles, replacing the 4-glyph "SUB TEST" marker. All of it was built and
tested without game data. Every test is synthetic.

| Area | Files | State |
|---|---|---|
| Script | `script/xak3_cutscenes.tsv`, `tools/make_script_tsv.py` | **7 visual scenarios, 83 cues.** 55 DRAFT (VS1/Track 28, JP aligned to NightWolve's Jap2Eng script by byte offset + segment), 20 DRAFT-verify-audio (VS2/VS3, JP from in-game text that matches the cinema), 1 SKIP (system text), **7 TODO-needs-audio** (VS2-010/011, VS3-001, VS4–VS7). The English is a concise new subtitle translation using NightWolve name spellings. **This public TSV has `ja_text` and the NW English reference blank.** It keeps only `ja_source` pointers (`NW-Jap2EngScript@offset#segment`). Run `python3 tools/make_script_tsv.py --nw-zip XakIII-Jap2EngScript.zip` locally to fill them. |
| Glossary | `script/glossary.md` | NW ↔ JP ↔ 2006 Ys Utopia transcript names, plus an `avoid:` list (Latok→Ratok, Wavis→Webis, …) |
| Lint | `tools/lint_script.py` | ≤ 2 lines, ≤ 240 px/line (15 sprites: 1 per-scanline slot spare plus 8 px overscan margins), font coverage, avoid list, overlaps, ≤ 17 cps. Current result: 0 errors, 0 warnings, widest line 144 px. |
| Font | `font/glyphs.txt` → `font/xak3_subfont.png`, `tools/font_build.py` | Original 8x12 proportional font (78 glyphs) with drop shadow. Renders lines → centred 16x16 sprite patterns. `asm` emits a font table for a runtime renderer. |
| Renderer | `docs/renderer-design.md`, `tools/pce_proto/` | Homebrew HuCard prototype (ca65), verified in Mednafen 1.32.1: double-buffered sprite strips, ≤ 512 B/VBlank TIA upload, SAT flip, worst case 2×15 sprites. Screenshots in `review/`. **Not hooked into Xak III yet.** |
| Timing | `tools/timing/`, `docs/timing.md` | CUE/BIN → WAV extraction; music-robust VAD → cue proposals and Audacity labels → `--write` into the TSV. Synthetic self-test passes (0.12 s max error). |
| Tests | `tests/test_subtitle_pipeline.py` | 15 synthetic tests |

Blockers: the disc tracks (02, 28–35) and System Card 3.0 BIOS from Paul's own media; the local v0.3–v0.5 / v0.17–v0.21
builders and save states (never pushed to this repo); and listening transcription for the 7 TODO cues.
