# Xak I & II / Xak III: direct implementation investigation

**24 October 2026. Actual published patch headers decoded; author contacted.**

## Direct technical question has been posted

On [randomprojectsfactory/xak-i-ii-pce-english issue #2](https://github.com/randomprojectsfactory/xak-i-ii-pce-english/issues/2#issuecomment-6390071301), the project's **TopCat** GitHub account posted a short public, technically specific request for the developer's Xak III proof of concept. The comment explains the existing v0.5 stable sprite system and the missing initial King Wavis subtitle, and requests:

- Xak III subtitle presentation via sprites/SAT versus background-tile graphics
- Exact game scene-update/voice-event hook (or enough pseudocode to reproduce safely)
- Visibility during first King Wavis line, even when existing hook/SAT/font/palette all show correct values
- Raster CR/RCR, SATB DMA ordering, scene-window changes
- Credit and no request for proprietary source media

The author has **not yet publicly responded at the moment this record was created**. We cannot characterize their prototype as published, complete, compatible with NightWolve, or available for reuse. The October 22 Reddit author's statement is evidence of an **experimental working result on the Japanese Xak III build**, not an engineering design document or finished patch: [original announcement](https://www.reddit.com/r/retrogaming/comments/1x9r0t2/pce_supercd2_msx_ten_hack_video_subtitles/). The author estimated approximately 30 required dialogue subtitle events.

## Actual VCDIFF / xdelta3 structural inspection

Both public files from [Xak I & II](https://github.com/randomprojectsfactory/xak-i-ii-pce-english) have VCDIFF magic `D6 C3 C4 00`, header indicator `$05` (secondary compressor and application header), and secondary compressor ID **2 = LZMA**. All observed window sections (data, instructions, addresses) were separately compressed (`$07`). Checksums are four-byte Adler-32 values.

**Track 02:**

- Public patch: **7,025 bytes**
- Source/target track size: **1,827,504 bytes**
- One window of 1,827,504 target bytes; source offset 0, source length 1,827,504
- Compressed section lengths: data **4,683**, instructions **1,146**, addresses **982** bytes
- One window checksum: `9c3faec1`

**Track 05:**

- Public patch: **293,217 bytes**
- Full reconstructed target size: **24,947,664 bytes**
- Three target windows:
  1. Output offset **0**, length **8,388,608**; copy-source offset **0**, length **24,928,768**; stored sections data/instructions/addresses **63,108 / 13,328 / 18,434** bytes
  2. Output offset **8,388,608**, length **8,388,608**; copy-source offset **531,267**, length **24,390,411**; stored sections **74,353 / 18,219 / 27,154** bytes
  3. Output offset **16,777,216**, length **8,170,448**; copy-source offset **531,267**, length **24,416,397**; stored sections **60,359 / 8,293 / 9,694** bytes

The window-source lengths are **VCDIFF reference spans**, not counts of changed bytes or scene locations. We have **not** located the subtitle engine's CPU routines or source sectors from this metadata alone.

**Key limitation:** the public xdelta data is LZMA-compressed and encodes COPY operations referring to the original copyrighted Xak I & II BIN tracks. Exact before/after bytes for program disassembly require the matching original Japanese tracks and an LZMA-capable xdelta3 decoder. We will not claim a source disassembly from patch sizes or high-level development notes.

## Reproducible reference analyzer added to our repository

New original code: [`tools/analyze_xak_i_ii_reference_xdelta.py`](../tools/analyze_xak_i_ii_reference_xdelta.py), with [six synthetic tests](../tests/test_analyze_xak_i_ii_reference_xdelta.py). The tool:

1. Reads public xdelta files, validates and reports VCDIFF windows, compressor ID, section sizes and checksums **without the game disc**.
2. Optionally accepts the public `source-hashes.json` and checks the patch SHA-256.
3. If and only if a legitimate matching Japanese source track is supplied, verifies its original SHA-256, uses external xdelta3 with LZMA to create a **temporary** reconstructed output, verifies its target SHA-256, and reports contiguous changed raw 2352-byte sector ranges and changed-byte counts.
4. Deletes the reconstructed copy after inspection; neither prints nor exports copyrighted game bytes. Does not modify input BINs or save states; refuses to overwrite an existing JSON report.

Example without original disc:

```powershell
py -3 .\tools\analyze_xak_i_ii_reference_xdelta.py --patch ".\Xak-English-Track05.xdelta" --manifest ".\source-hashes.json"
```

With original (optional, LZMA-capable xdelta3 on PATH):

```powershell
py -3 .\tools\analyze_xak_i_ii_reference_xdelta.py --patch ".\Xak-English-Track05.xdelta" --manifest ".\source-hashes.json" --source "D:\Xak-I-II\Xak (Japan) (Track 05).bin" --report ".\xak-track05-sector-map.json"
```

The original source and patch filenames in these commands are **illustrations**, not assertions that those files exist on the user's machine. This is a read-only analytical workflow, **not** a request for the user to test a new Xak III build.

## What is still missing, and why no v0.7 game patch yet

Our current best-tested build remains Xak III **v0.5**. v0.6 moved font fragments to Y=64, 88, 112, 136; the tester reported that none appeared during the first King's speech but they appeared with the first hero dialogue. An early 5.2873-second native state confirms the hook flag is initialized, all glyphs intact, four SAT records present, white palette, and saved VDC1 CR enabled; nonetheless the *captured framebuffer has no text*. This is a **display/handoff** problem, not a glyph-lifetime or initial-hook problem.

If the Xak I & II developer shares implementation details, first compare **the Japanese Xak III target scene** with our NightWolve reconstructed Track 02, then adapt the **mechanism** without overwriting translated gameplay code, moving original CDDA or publishing third-party proprietary material.

Keep in mind [Xak I & II issue #1](https://github.com/randomprojectsfactory/xak-i-ii-pce-english/issues/1): a user reports subtitles landing in the 225–240 overscan rows. We should keep all essential Xak III subtitles inside the **224-line CRT-safe region** and validate on emulator settings that actually crop to 224 lines.

**Next meaningful milestone:** actual implementation-level insight into the Xak III author's technique or a verified source-vs-patched sector map from the appropriate original Xak I & II track. Further blind sprite-coordinate experiments are deferred.
