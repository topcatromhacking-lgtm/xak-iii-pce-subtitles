# Subtitle renderer design (replacing the 4-glyph "SUB TEST" marker)

Status: design + a working homebrew prototype in Mednafen
(`tools/pce_proto/`, screenshots in `review/`). Nothing here has run inside
Xak III yet; that needs Paul's disc (Track 02 + Track 28) and a cinematic save state.

## 1. Constraints (repo facts and hardware)

| Item | Value | Source |
|---|---|---|
| Visible width | 256 px (VCE 5.37 MHz dot clock) | repo v0.10 to v0.21 states |
| Band rows | line 1 at Y184–199, line 2 at Y204–219; 220–223 reserved | repo v0.11 black-band plan (SAT Y 248/268) |
| Sprites per scanline | 16 (hardware). 16 px wide → 256 px max | HuC6270 |
| SAT | 64 entries, auto SATB DMA from VRAM | HuC6270 |
| Native sprites in King scene | 19 native + 4 subtitle records in the producer queue | repo docs v0.18/v0.19 |
| Narrow 4:3 scenes | picture is 64 px narrower; X offset −64 | repo v0.14 |

Derived limits used by `tools/lint_script.py`:

* **Max line width = 240 px = 15 sprites.** This keeps 1 of 16 sprite slots
  per scanline spare for a native sprite that crosses the band, and gives an
  8 px CRT overscan margin on each side.
* **Max 2 lines** (two 16 px sprite rows: Y184 and Y204).
* The font is proportional (8x12 cell, average lowercase advance 5.3 px), so
  240 px fits about 45 typical characters. The style target stays at ≤ 28
  characters per line (WARN) for reading speed. An 8 px fixed font would fit 30.
* Worst case per cue: 2 × 15 = 30 SAT entries. Natives can use at most 34
  more (the King scene uses 19).

## 2. Data format

Offline (`tools/font_build.py`), each subtitle line is rendered to a 16 px
high strip with a 1 px drop shadow, centred, and cut into ⌈w/16⌉ 16x16 sprite
patterns. Pixel 1 = text and pixel 2 = shadow (sprite palette entries 1 and 2), so
only bitplanes 0–1 carry data:

```
sprite pattern (64 words): plane0 rows0-15 | plane1 rows0-15 | plane2 (=0) | plane3 (=0)
```

Planes 2/3 are cleared once when the buffer is set up and never written again.
That means a cue uploads (and stores) only **64 bytes per sprite**: at most
1,920 B per cue, typically ~1 KiB.

Per-scene cue table (generated from `script/xak3_cutscenes.tsv`):

```
struct cue {            // 10 bytes
  u16 start_frame;      // frames since the scene's CD play start (59.826 Hz)
  u16 end_frame;
  u16 pack_offset;      // into the scene's subtitle pack (sprite plane data)
  u8  n1, n2;           // sprites in line 1 / line 2 (0 = absent)
  u8  x1, x2;           // left X of each line (SAT X - 32), already centred
};
```

## 3. Runtime

1. **Buffers.** Two pattern buffers in free VRAM, A and B, each 30 × 64 words
   (3.75 KiB). The cue being shown lives in one buffer while the next cue
   uploads into the other. The prototype uses $4000/$5000; the real addresses
   must come from a VRAM-usage map of the cinematic (save-state diff with
   `compare_vdc_after_resume.py` / `map_audio_savestate.py`). If 7.5 KiB is not free, use
   one buffer: blank the band and upload during the gap (≤ 4 frames at 512 B/frame).
2. **Upload in VBlank.** The VBlank hook (the existing $9C00 hook / $76DF
   raster helper path) moves ≤ 512 B per frame with `TIA` to VDC port $0002,
   setting MAWR per sprite (64 B runs). Measured cost: 6 cycles/B →
   ~3.1 k CPU cycles per frame, well inside the ~10 k-cycle VBlank.
3. **Show.** When `now >= start_frame` and the upload is complete, write the
   cue's SAT entries. They go **in front of** the native entries (lower SAT
   index = higher priority), so on a band scanline the hardware drops a native
   sprite, not a subtitle sprite. Natives are hidden in the black band anyway.
   This replaces the 4 records appended at $9C4B.
4. **Hide** at `end_frame` by writing Y=0 for the subtitle entries.
5. **Clock.** `now` = VBlank frames counted from the moment the scene's
   `CD_PLAY` for its track returns. The hook point is the cinematic's BIOS play call
   (`scan_bios_calls.py` lists it). Optional drift correction: every ~4 s read
   subcode Q (`CD_SUBQ` BIOS call) and re-base `now` on the absolute track time.
   Mednafen's seek latency differs from hardware, so the first-cue offset gets
   measured on Paul's console with `align_cdda_capture.py` (it already fits
   Track 28: recording = 13.064 s + 1.00875 × CD time).

## 4. Where the text data lives

* VS1 has 56 cues, about 56 KiB pre-rendered. All 7 scenes come to roughly 80–100 KiB.
* **Option A (preferred): subtitle pack per scene.** Append the packs as new
  sectors at the end of Track 02 (rebuilding EDC/ECC with
  `xak_iii_disc_utils.py`) and load the current scene's pack into free
  Super-System-Card RAM next to the 192 KiB cinematic overlay at scene start.
  This needs a free-RAM survey.
* **Option B (fallback, no pack): runtime glyph renderer.** Store only the text
  (~30 B/cue) plus the font (`font_build.py asm`: 96 × 12 B + width table ≈
  1.3 KiB) and render each line into the back buffer from the main loop. That costs
  about 60 chars × 12 rows of shift/OR ≈ 30 k cycles, spread over several frames.
  The upload path and SAT handling stay the same.

## 5. Prototype (done)

`tools/pce_proto/run_proto.sh` builds a 32 KiB homebrew HuCard
(`proto.s` + `gen_proto.py`), runs it headless in Mednafen 1.32.1 and saves frames:

* `review/proto_sprite_subs_cue1.png`: VS1-001, two lines in the lower band
* `review/proto_sprite_subs_cue2.png`: VS1-004, after a VBlank-chunked upload into buffer B and a SAT flip
* `review/proto_sprite_subs_cue3.png`: VS1-007, back in buffer A
* `review/proto_sprite_subs_stress_2x15.png`: lint worst case, 2 × 15 sprites
  (240 px per line). No sprite dropout.

The prototype implements steps 1–4 with a frame counter in place of the CD clock.
It uploads full 128 B patterns for simplicity. The 64 B plane-0/1 optimisation is
not in the prototype yet.

## 6. Open risks

* Free VRAM and RAM in the cinematic: unknown until a save state exists.
* Native sprite leakage into the band (repo v0.15/v0.20 issues). The SAT
  ordering above stops subtitles from being dropped, but it does not hide
  natives that are drawn over the band in non-black scenes.
* Scene reload resetting X constants (repo issue). The cue engine must re-init on every
  scene start, keyed on the track number passed to CD_PLAY.
