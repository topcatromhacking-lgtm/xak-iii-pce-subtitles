# Pilot 01: Royal audience capture inspection

Review date: 2026-10-20. Source: a user-supplied **216.2-second video with original audio**, inspected privately; the video, screenshots and music/voice recordings are **not** in this public repository.

## Confirmed

The recording contains Xak III's first royal-audience cinematic, the one that the existing fan translation companion script calls *Visual Scenario 1: In the Throne Room of King Arband Wavis*. Reference: https://www.ysutopia.net/forums/index.php?topic=205.0 . That script offers English dialogue and consistent spellings for Wavis, Latok, Pixie, Beluga and the magician. It is **not yet time-aligned**, and its OST MP3 track number does not independently establish an actual CD track.

The original animation and Japanese voice audio play, but **no English subtitles are visible**. The scene is presented through drawn/animated character portraits, palace backgrounds, layered sprites and fades, rather than a visible ordinary video file. Many shots retain black lower margins that may be useful for a subtitle overlay, **subject to actual VDC/VRAM and palette analysis**.

### Coarse video shot timeline (relative to submitted recording)

| Recording time | Visible action | Notes |
|---|---|---|
| 00:00–00:07 | World map and transition | Not the cutscene proper |
| 00:08–00:13 | Black transition | Video/audio fades |
| 00:14–00:21 | Wide royal audience chamber | Approximate scene start |
| 00:22–00:35 | Latok kneels, then close-up | Character-reaction sequence |
| 00:35–00:45 | King Wavis portrait | Dialogue |
| 00:45–00:54 | Pixie appears; wing animation | Potential overlay/graphics resource changes |
| 00:54–01:03 | Latok holding tiny Pixie; ensemble | Dialogue |
| 01:03–01:13 | General Beluga portrait | Dialogue |
| 01:13–01:24 | King Wavis portrait | Dialogue |
| 01:24–01:35 | Group and audience | Dialogue |
| 01:35–01:51 | White-haired magician portrait | Exposition |
| 01:51–02:23 | Intercut group, magician and king | Gate discussion; align to audio before cueing |
| 02:23–02:55 | Audience, king, Latok and Beluga | Various exchanges |
| 02:56–03:13 | Latok close-up, Pixie on shoulder | Dialogue |
| 03:14–03:18 | Pixie close-up, wing spread | Dialogue/reaction |
| 03:19–03:28 | Tiny Pixie on Latok, final close-up | Ending exchange |
| 03:29–03:36 | Black screen | Captured audio also silent through end |

Audio included: AAC stereo at 48 kHz. Video: H.264, 1248x870 at 30 fps (desktop capture, **not** evidence of native game frame rate). Audio activity begins around the cinematic transition and falls to digital silence near 03:27; cutscene timing should ultimately be traced inside the emulator, not inferred solely from capture-wall-clock time.

## What this does NOT verify

- No voice has been transcribed or synchronized word-by-word from Japanese audio yet.
- No evidence yet that a particular physical CD-DA track number plays for the whole sequence; earlier online numbers are soundtrack labels.
- No VSync/render callback or safe RAM/VRAM allocation has been identified.
- No working on-screen subtitles or modified disc have been tested.

## Immediate next capture/debug task in Geargrafx

1. **Save a state immediately before triggering the audience scene**, on the world map or preceding transition. Keep that state privately; it will make experiments reproducible.
2. While the first King Wavis line is heard, inspect Geargrafx debugger **CD-ROM audio status** and **ADPCM status**. Note active playback type and disc LBA/track, if displayed.
3. With a state backup, enable a short trace around scene entry, filtering to CD-ROM/SCSI and ADPCM activity rather than collecting an entire multi-minute CPU instruction trace. See https://github.com/drhelius/Geargrafx/blob/main/MCP_README.md .
4. Preserve a screenshot or exported text trace. Do **not** yet patch any of the 15 static CD_PLAY-looking signatures: these are ROM byte matches, not established call sites.
5. Use the existing English reference transcript to prepare original editorial subtitle lines and assign real frame/audio cues only once the playback timing origin is known.

**Milestone:** one real Japanese spoken line, one synchronized English subtitle, original audio and all animation unchanged.
