# Xak III: direct contemporary subtitle implementation lead (24 October 2026)

## Most important discovery

The author/thread behind [randomprojectsfactory/xak-i-ii-pce-english](https://github.com/randomprojectsfactory/xak-i-ii-pce-english) has described **already testing a working subtitle approach in Xak III**, not merely Xak I & II. The relevant public discussion is [Reddit, 19–22 October 2026](https://www.reddit.com/r/retrogaming/comments/1x9r0t2/pce_supercd2_msx_ten_hack_video_subtitles/). In response to an October 21 request for Xak III and Fray CD subtitles, a reply dated **October 22** says:

> Xak III is possible, I looked into the Japanese build and could make something work already.

The same reply estimates **around 30 dialogues** requiring subtitles and indicates Fray was not yet unpacked. These are **the poster's reports**, not a published Xak III patch, source repository, or validated executable. No standalone public Xak III patch or original assembly source was verified during this review.

A second October 23 Reddit release post, [Cosmic Fantasy PC Engine English script and subtitles](https://www.reddit.com/r/TurboGrafx/comments/1xd1r93/release_cosmic_fantasy_english_script_subs/), attributes to learning from Xak I & II a custom subtitle renderer for **364 captions across 59 audio tracks**. This strongly suggests that direct design discussion with the developer could be more valuable than replicating guessed tricks.

## Existing live GitHub issues

**Do not post a duplicate issue without checking existing discussion first.**

1. [Issue #2: Character Name Consistency with Xak III translation](https://github.com/randomprojectsfactory/xak-i-ii-pce-english/issues/2), **opened 24 October 2026**. It explicitly asks for either Xak I & II naming consistent with NightWolve's Xak III patch, **or a Xak III subtitle patch**. At the time inspected, it had **0 comments**. This is the most relevant existing place to follow a developer reply about a Xak III patch.
2. [Issue #1: Patch uses 240 lines instead of 224](https://github.com/randomprojectsfactory/xak-i-ii-pce-english/issues/1), **opened 23 October 2026**. The reporter warns the Xak I & II patch locates text in overscan outside a typical CRT's **224 visible lines**. This is a **user report**, not an independently replicated hardware finding, but the distinction matters: Xak III subtitles should fit conservative 224-line safe presentation.

## What the Xak I & II repository actually gives us

- Binary `xdelta` patches for Japanese Tracks 02 and 05, plus a hash-verified patch application tool.
- High-level [DEVELOPMENT.md](https://github.com/randomprojectsfactory/xak-i-ii-pce-english/blob/main/DEVELOPMENT.md) describing native tile/palette/scroll pipelines, staged graphics updates, preservation of raster interrupts, speech event synchronization, and display handoffs.
- A release changelog describing fixes to subtitle graphics corruption and displaced background fragments.
- **No published assembly implementation** or ready-to-transplant subtitle source. Applying its 29-track xdelta to Xak III's 35-track NightWolve English BIN is invalid.

Recovering exact changed code from the xdelta requires the matching original Xak I & II raw disc tracks, particularly Track 05, so the delta can be decoded and pre/post regions disassembled. The public manifest contains source hashes but not the copyrighted source disc. A diff alone is not proof of runtime hook or raster behavior.

## Concrete technical questions for the Xak III prototype author

The missing **first King Wavis spoken line** has become our most constrained problem:

- v0.5 Geargrafx state **5.2873 seconds into Track 28** proves **our existing hook has executed**, with four healthy VRAM glyph bitmaps, white palette, intact SAT entries, and a saved enabled sprite CR. Yet the frame has **no visible subtitle**.
- v0.6 tested the glyph fragments at **four vertically separated heights (Y=64,88,112,136)**. The user saw **none during the King speech; all become visible once the hero speaks**. This argues against a single fixed vertical crop but is not a complete raster trace.
- Later v0.5 cinematics display all sprites and preserve the font. The original persistent `SU` overwrite was fixed by relocating glyph pattern 43 to 59.

Ask the author **which Xak III cutscene bank/event they hooked**, **whether their proof-of-concept uses sprites or background tiles**, and **how they maintained text visibility during the King's first speech and camera/window transitions**, including any VDC CR/RCR change, SAT synchronization, or line-area compositing. A small abstract code sketch or pseudocode would be enough to transfer the method without requesting proprietary disc contents. Request 224-line safe placement for hardware compatibility.

## Engineering decision

**Keep v0.5 untouched as the stable rollback** (unique CUE and 5 save slots). **Do not build v0.7 from blind coordinate or CR changes.** First pursue the published author's Xak III-specific method and the existing GitHub issue; in parallel, if feasible, disassemble the released Xak I & II diff *with legitimately supplied matching raw tracks*. If no direct method becomes available, fall back to the targeted Geargrafx VDC register/IRQ/SAT trace already specified in [v0.6 diagnostic plan](pilot-01-v06-negative-raster-trace-plan.md).

This entry distinguishes **first-hand author reports**, **user issue reports**, and **our own Geargrafx runtime evidence**. It does not claim that the Xak III prototype or Xak I & II source code has been acquired.
