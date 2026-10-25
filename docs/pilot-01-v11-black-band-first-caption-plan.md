# Pilot 01 v0.10 passes from fresh scene — lower black-band and first caption plan

**24 October 2026.** User's real Geargrafx v0.10 result: **`SUB TEST` appears from the start of the cinematic, before King Wavis's first spoken words.** The square that had hidden subtitle sprites in an earlier scene no longer obscures them. This means the disc-native v0.10 selective raster patch loads from a clean scene and repairs the visibility issue. It does **not** establish correct subtitle onset, removal, font capacity or translations yet.

## Source-verified first dialogue

A contemporaneous historical [Xak III royal-audience translation transcript from 2006](https://www.ysutopia.net/forums/index.php?topic=205.0) reproduces the voiced Track28 dialogue based on NightWolve's earlier translation. The King's **first remark concerns the ceremony and Farland**, while the Gate discussion begins substantially later. It also states the **original patch uses “Ratok Kurt” and “King Webis”**, while the 2006 transcript editorially normalizes those to “Latok Kart” and “King Wavis.”

For consistency with the user's NightWolve English patched Xak III, **provisional subtitle choice**:
- Cue 01, King: `That was quite a` / `ceremony, Ratok.` (16/16 characters)
- Cue 02, King: `Farland's acts were` / `quite impressive this time!` (19/27 characters)
- Following cue, hero: short hesitant reply, timing and exact wording to be checked against the original Track28 audio before implementation.

The quote is used only as a *short pilot excerpt* and credits NightWolve's original translation. Do not copy/publish the full third-party script into the repository. Exact onset/end timestamps **are not yet determined**; must synchronize to the game CD-DA playback, not the earlier `SUB TEST` scene-hook activation.

## Geometry from real Geargrafx native screenshot inspection

Saved rendered 256×240 native screenshots for early King state5, later audience states2 and 3 show the **lower rows 178–239 completely black**. Placement should use the CRT-safe portion only:

- Candidate line 1: native Y **184–199**.
- Candidate line 2: native Y **204–219**.
- Reserve pixels 220–223 plus CRT overscan safety.
- Small pure-white lettering with transparent background and no decorative frame. Center each caption horizontally; target about 27 glyphs/line with 8px fixed-pitch letters.
- These positions are **proposed/test coordinates**, not yet proven visible in an actual native black video band.

### Technical constraint

The v0.9/v0.10 targeted raster helper only enables sprites in bands where background output is enabled. The lower black band is outside the BG-enabled picture. Simply changing the existing SAT Y constants to 184/204 would therefore hide them. Need a narrowly scoped **subtitle-only late-raster-band enable** (BG still black) to keep the rest of the game's native sprite blanking intact.

## v0.11 black-band visibility experiment

A temporary **save-state-only** experiment is available privately to the user:

- Based on exact pinned, successful v0.9 early King state2, SHA-256 `8b40e7d95c5cfc6ec57eeffa00f58058a3b6692c055469e56d579a1bbd5c5fb2`.
- Saves as unique `Xak_III_English_SUB_TEST_v11_Pilot01.state2`, with new `Xak_III_English_SUB_TEST_v11_Pilot01.cue` referencing the existing user's **v0.10** Track02 BIN and unchanged 34 audio tracks.
- Temporarily replaces the helper's `BPL +2` with `NOP NOP`, letting sprites show even with BG disabled. **This may expose native sprites in the letterbox and is NOT a production fix.**
- Relocates 4 existing 16×16 `SUB TEST` sprite blocks to two rows in the lower black band, forming a short test display approximately `SUB` / `TEST`.
- CPU code table at `$9C9A-$9CA5` supplies SAT Y positions 248/268 (screen Y184/204) and new X positions 144/160 for each line.
- Exactly **12 resident CD RAM bytes changed**: two instruction bytes plus ten coordinate-table bytes. All other CPU code, VRAM/BAT, palettes, native SAT buffers, thumbnail, Japanese audio state and original files remain byte-identical.
- Resulting SHA-256 `6dd5ad0601c6a28e05952acbfb985bdef4bebe67105cd56bc5430041e686d309`.
- **Nine synthetic regression tests plus pinned original-state transformation succeeded.** The real v0.11 emulator result remains **untested**.

**Quick test:** place the two prebuilt v0.11 files beside the v0.10 BIN and original audio, launch new v0.11 CUE, load its Slot 2, advance a few frames at the King's first speech, observe whether `SUB` / `TEST` appears in black lower band or whether sprites unexpectedly bleed into borders. If unwanted sprites or freeze, discard the v0.11 files and return to verified v0.10. No rebuild necessary.

## Next milestones

1. User confirms actual lower black-band rendering in v0.11.
2. Replace unconditional diagnostic sprite enable with **precisely gated bottom-band raster control** to avoid exposing other scene sprites.
3. Scale from eight-letter marker to a safely budgeted **two-line variable-glyph** renderer; protect VRAM lifetime and native sprite budget.
4. Derive timecodes from physical CD Track28, display Cue01 **only after the first King's words**, remove it before Cue02 and synchronize subsequent spoken lines.
5. Test all the way through the complete royal-audience scene from clean v0.10-compatible bootstrap. Preserve Japanese CD audio and NightWolve's English gameplay translation.

**External collaboration:** the user requires prior permission before any public third-party comment, issue, or outreach. No external messages were sent.
