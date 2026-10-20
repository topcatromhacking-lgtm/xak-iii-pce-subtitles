# Pilot 01: first synchronized English subtitle

Status: **static reconnaissance only**. No subtitle display or cutscene hook has yet been implemented or tested.

## Target

Start with one early Japanese-voiced scene, preferably the throne-room encounter with King Wavis, Latok and Pixie. Preserve Japanese voices, animation and music. Show one timed English subtitle before attempting a full translation.

A 2006 discussion of the original Xak III translation reports that one early cutscene already has translated script text in the ISO, but the game apparently doesn't display it: https://www.ysutopia.net/forums/index.php?topic=205.0 . Verify rather than assume it is reusable directly. The fan transcript calls that sequence "Visual Scenario 1" and labels OST MP3 track 28. An OST MP3 track number **does not prove the corresponding physical CD track number**.

## Initial binary research (2026-10-20)

Both user-supplied Japanese Track 02 and the independently reconstructed English Track 02 were scanned as MODE1/2352 data sectors with a **225-sector pregap**. The PC Engine System Card exposes CD_PLAY at $E012 and related CD/ADPCM functions via BIOS jump-table calls (https://www.zeograd.com/download/pce_bios.html).

| Pattern | Possible call | JP candidates | EN candidates |
|---|---|---:|---:|
| 20 12 E0 | JSR $E012 / CD_PLAY | 15 | 15 |
| 20 09 E0 | JSR $E009 / CD_READ | 63 | 63 |
| 20 33 E0 | JSR $E033 / AD_TRANS | 19 | 19 |
| 20 39 E0 | JSR $E039 / AD_PLAY | 3 | 3 |

Candidate locations are **identical** across both discs. The first CD_PLAY-looking sequence is at indexed user-data offset 0x1077 and raw Track 02 offset 0x82617. Some byte-pattern matches may be graphics/data or duplicate code and **must not be patched without a runtime trace**.

Run locally (report belongs in an ignored private folder):

    python tools/scan_bios_calls.py "Xak III - The Eternal Recurrence (Japan) (Track 02).bin" --compare "Xak_III_English_Track02_Reconstructed.bin" --out "/private/xak3_scan.json"
    python -m unittest discover -s tests -p "test_scan_bios_calls.py" -v

## Practical test sequence

1. Boot the existing English translated Track 02 **with the other 34 original Japanese tracks**, using our split-track English CUE; check normal dialogue and audio.
2. Reach any convenient early **voiced** scene. Make a 30–60 second video with original audio, and a save state or normal save immediately before the scene. Note your emulator and BIOS/System Card versions.
3. Use an emulator debugger, preferably **Mednafen**, to trace actual disc-audio/ADPCM playback and the active scene-rendering loop. Its debugger is accessed with **Alt+D**. Reference: https://mednafen.github.io/documentation/debugger.html . Disc offsets from the scan are **not CPU breakpoint addresses**.
4. For one voice line, verify the English words, onset/offset timing, screen area, text rendering and a safe clearing mechanism.
5. Only then produce a small, reversible test patch displaying one English subtitle, with Japanese voice, soundtrack, animation, controls and saves unchanged.

## First milestone acceptance

One subtitle is visible and legible for the intended voice line, appears and disappears at correct timings without overwriting important visuals, and leaves game/audio execution unaffected. Once this passes, scale to a timed scene-script format and the remaining voiced cutscenes.

Do not commit any disc data, original sound, third-party PPFs or extracted assets to this public repository.
