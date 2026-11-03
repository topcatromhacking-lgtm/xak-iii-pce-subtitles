# Runtime subtitle engine (v0.30)

Full-font subtitles for the voiced cinematics, rendered at run time by a small HuC6280
engine in the free CD-RAM bank `$83`. Built by `tools/engine/build_subs.py` on top of the
user's own v0.10 SUB TEST Track 02 (which already hooks the scene loop at `$8EE5 JSR $9C00`
and the raster CR write at `$65AA JSR $76DF`). The output is a build product: never commit it.

## Memory map (King Webis audience, measured in Mednafen states)

| Where | Use |
|---|---|
| bank `$83` (`$A000-$BFFF`) | all `$FF` in every state: engine code + font + cues (~5 KB), `satbuf`/`linebuf` at `$B980`, `patbuf` at `$BC00` |
| bank `$81` `$76DF` | raster CR helper (26 bytes) |
| bank `$81` `$65D3` | raster routine tail `STA $0003/RTS` -> `JMP $7700` |
| bank `$81` `$7700-` | width tail + `setn`/`setf` (zero in all states and on disc up to `$785E`) |
| bank `$81` `$76FC-$76FE` | `WIDE`, `NARROW`, `RFLAG` flags |
| bank `$82` `$8D44`/`$8D59` | game's 128-px / 256-px display-width routines: first 4 bytes -> `JSR setn/setf; NOP` |
| bank `$82` `$9C00` | stub: map bank `$83` at `$A000`, `JSR $A000` |
| VRAM `$0D00-$0EFF` | 8 sprite patterns (16x16, 4 planes) = 32 text cells |
| sprite palettes 6, 7, 13, 14 | one per bit plane: white where the plane bit is set |

## Per frame (called once per scene main-loop pass)

1. Frame counter = VBlank counter `$2338` deltas since the first call. Cue times become
   frames as `(t - 0.228 s) * 59.7168` (`build_subs.py` defaults `CLOCK_OFFSET`, `CLOCK_FPS`).
   The VBlank counter runs 0.183% slow relative to CD audio in this scene, so the nominal
   59.826 Hz drifted subtitles +0.26 s late by the end of the scene. Both constants were fit
   from a Mednafen recording (audio cross-correlated against the track to place the CD
   clock, band-text changes detected per frame); see `tools/timing/align_recording.py`.
2. State machine per cue: render (proportional 8x12 font, up to two lines split by `|`,
   centred, packed into up to 32 16x16 cells) -> wait for start -> upload 1 KB of
   patterns with `TIA` -> shown until end -> next cue.
3. SAT write (replaces the native writer `$8516`): text cells first, then 8 blocker sprites
   (32x64, X off screen, Y = band top 176), then native sprites (capped at 64 total).
   The blockers use up the 16-sprites-per-line budget on the band lines only, so native
   sprites (Pixie's wings, etc.) vanish exactly below line 176 and stay whole above it.
4. `RFLAG` = 1 only while a cue is shown, and only from the VBlank after the SAT with the
   text and blockers was written (otherwise one frame of natives leaks into the band).

## Raster side

The helper turns sprites on in the lower letterbox band (start line `$A8-$DF`) while
`RFLAG` is set. It runs inside the RCR interrupt before the CR write, so it must stay short
(a slower helper let the first band line show picture garbage).

During the 128-px "close-up" shots the game narrows the display (HSR `$0A02`, HDR `$0C0F`),
which also clips sprites. The tail at `$7700` (after CR/BYR/BXR are written) widens the
subtitle band to 256 px (HSR `$0202`, HDR `$041F`) and restores the game's width at the
next band. The game's width routines are hooked to keep `NARROW` current.

## Verified (Mednafen 1.32; screenshots kept privately, not in the repo)

* Text fits and is centred in every shot type, including the narrow close-ups.
* Full-frame scan of 4,566 recorded frames over all King-scene shots: no non-text pixels
  and no stray white in the band, no picture garbage at the band edge.

* Timing (calibrated build, 55 cues, Track 28 cross-correlated at NCC >= 0.988): start
  error median -6 ms, 49 of 55 cue starts within -25..+10 ms. Six back-to-back
  changes measured +64..+254 ms late; spot checks of those frames show the change on time,
  so this looks like a frame-index vs. timestamp mismatch in the recording. The last
  cue ("...") is too small for the detector.

## Scene status

| scene | track | timing | in-game |
|---|---|---|---|
| VS1 King Webis audience | 28 | reviewed (ASR + hand) | verified in Mednafen |
| VS2 Fray/Pixie meeting | 31 | 2 cues timed; the other rows belong to a text-box scene | no save state nearby |
| VS3 Necromancer / father | 32 | timed (ASR draft for the long opening monologue) | no save state nearby |
| VS4 airship landing | 29 | partial, med/low confidence | no save state nearby |
| VS5 / VS6 / VS7 | 33 / 34 / 30 | ASR mostly failed; low confidence | no save state nearby |

VS7 is Track 30 (Track 35 is instrumental). To hook scenes other than VS1, the engine
needs (a) to select the cue table by the CD track being played, and (b) a check, per scene,
that bank81 `$76E9-$785E`, bank83 and sprite palettes 6/7/13/14 are free there. This needs
save states close to those cinematics.

## Risks on real hardware (not testable in Mednafen)

* Mid-frame HSR/HDR changes during close-ups (line-boundary width switch).
* Per-frame VCE palette writes during active display can show dots on real consoles; they
  could be limited to the upload frame since the palettes are otherwise unused.
* Offscreen-X sprites counting toward the per-line limit is standard HuC6270 behaviour,
  but untested on a console.
