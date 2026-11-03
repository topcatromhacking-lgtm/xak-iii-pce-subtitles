# Xak III subtitles: restart notes (paused 2026-11-03 10:50, America/Mexico_City)

## State
- Repo: topcatromhacking-lgtm/xak-iii-pce-subtitles (PUBLIC). Work branch grokbot/subtitle-pipeline @ e6939de, draft PR #1. main untouched.
- Commits: 1c9cbcd (script/glossary/lint/font/prototype/timing/tests), 39960d2 (runtime subtitle engine bank $83, raster/width hooks, Mednafen route, timing tools), e6939de (clock calibration 59.7168 Hz / +0.228 s, VS1-VS4 reviewed times).
- Build: xak-subs/build/Xak_III_subs_v030_VS1_Track02.xdelta (VS1 King Webis, Track 28, 55 cues) vs clean Track 02 sha256 af04551c...; see build/README.md.
- Review: xak-subs/review/vs1b/vs1b_sheet.png. Status log: xak-subs/STATUS.md.
- Private (not in git): xak-subs/private/ (asr, timing, states, disc-verify, script with Japanese, nightwolve).
- Box: Mednafen 1.32.1 + syscard3.pce in ~/.mednafen/firmware; gh logged in as topcatromhacking-lgtm (token in ~/.config/gh/hosts.yml). Disc files in /tmp/disc (VOLATILE: re-download from Paul's Dropbox if gone). Git working copy /tmp/xr (volatile; reclone branch if gone).

## Next, in order
1. VS2-VS7 (tracks 29-35): time, insert, verify in Mednafen, contact sheet, xdelta, commit + push, STATUS.md line. One scene per checkpoint.
2. Transcribe 7 open cues from audio (VS2-010, VS2-011, VS3-001, VS4-VS7 gaps); confirm VS7 = track 30 or 35.
3. Check questionable translations (VS1 "Mt. Fuji").
4. Fix layout bugs: X-shift lost on scene reload; 1-frame glitch at scene change.
5. Full-game xdelta (all scenes), playthrough check, then mark PR ready.
