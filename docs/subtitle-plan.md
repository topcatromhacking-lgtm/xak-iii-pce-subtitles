# Subtitle engine engineering plan

## Goal

Preserve Japanese voices and original game animation while rendering synchronized English subtitles in voiced cutscenes. Use the established English text translation as a reference, not as a guarantee that all audio dialogue already has corresponding in-game English text.

## Phase 1: Audio and cutscene tracing

Trace real CD audio play commands, ADPCM transfers and cutscene scene-loading control flow in Xak III. Map each voice segment to a physical CD track or ADPCM object, and record scene-relative start/end times from actual emulator captures. Do not assume OST naming equals on-disc track numbering.

**Pass condition:** one scene has a reliable list of Japanese voice events, speaker identities and English translation lines.

## Phase 2: Text renderer and video resources

Identify the existing Latin 8×16 font, text-printing routine, relevant overlays and memory map. Inspect VDC tilemap/sprite use, palette limits and VSync update behavior during cutscenes. Compare architecture with [Yuna](https://github.com/suppertails66/yunatools) and [Emerald Dragon](https://github.com/suppertails66/emdrtools); do not transplant foreign code without compatibility checks.

**Pass condition:** demonstrate a safe cutscene hook and a readable two-line overlay without affecting original scene graphics.

## Phase 3: One timed subtitle

Insert a single nonintrusive subtitle for a chosen short Japanese voice line; synchronize to the real playback trigger. Guard against scene skips and text remaining on screen after playback ends.

**Pass condition:** captured emulator test shows subtitle legibility and timing while original voice, music, animation and gameplay remain intact.

## Phase 4: Scripts and QA

Write original English subtitle scripts with cue times, speaker labels and review state in UTF-8 TSV/JSON. Produce deterministic patch outputs and regression tests. Exercise normal playback, scene skips, timing drift, opening and ending sequences, save/load, and representative emulators.

**Pass condition:** all subtitled cutscenes tested with logs and screen/audio recordings; output can be applied to a user-owned source disc. Do not distribute complete game images or third-party patch files.
