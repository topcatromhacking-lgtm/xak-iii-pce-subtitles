# Pilot 01 v0.7 — background tile rendering in the black band (state-only experiment)

**October 24, 2026. Real emulator test pending. Not a new Xak III game patch.**

## Motivation: Xak I & II uses the black subtitle band

The user provided an actual 256×243 RGB crop from [randomprojectsfactory/xak-i-ii-pce-english](https://github.com/randomprojectsfactory/xak-i-ii-pce-english): character portrait at the top and a two-line white English caption printed directly against the black area beneath it. In that image, text pixels extend to approximately **y=237**, so copying that *exact placement* may be unsafe for a standard **224-line CRT crop** (see the reference project's [issue #1](https://github.com/randomprojectsfactory/xak-i-ii-pce-english/issues/1)). The useful idea is **using the black background band** rather than an overlay that relies on the sprite scanline renderer, **not** copying its Y-coordinate.

The Xak III early King Wavis frame (the user's real v0.5 **Slot 5**, physical CD Track 28 at **5.2873 s**) already has black upper/lower margins. At that frame, **the existing scene-loop hook has run**, the complete sprite font and native SAT entries are present, the palette is white and saved CR is sprite-enabled, yet no sprite text is visible. Real v0.6 testing relocated sprite fragments to y=64/88/112/136 and still found none during the opening King speech. Another coordinate experiment is not warranted.

## New reversible experiment

A **read-only-derived, copy-only Geargrafx v44 state experiment** tests the PC Engine's **background/tile renderer** while original v0.5 sprite hook stays untouched. It creates a new `Xak_III_English_SUB_TEST_v05_Pilot01.state4` from the user's original private `state5`. No new CUE or BIN is created, no original save state is overwritten, and no source content, proprietary memory or screenshot is committed.

Input state5:
- exact file SHA-256 `63a2ea5434314c0303b9c5fb5266962de76c0c260cd093d7f649a760036cc694`
- size **749,238 bytes**, native Geargrafx 1.8.4/v44
- expected VDC1 CR=`$00CC`, MWR=`$0050` (64×64-tile BAT), HDR=`$041F`
- existing BG palette **7**: color 0–14 black, color **15 white (`$01FF`)**
- unused 8×8 tile IDs **2025–2029**, initially zero and **unreferenced by the saved 64×64 BAT**

For five unique Latin glyphs in `SUB TEST` (S/U/B/T/E):
1. Encode a tiny 5×7 pixel capital-letter font as 8×8 **4bpp HuC6270 background tiles** at tile IDs 2025–2029, using each bitmap bit in all four planes for palette color 15.
2. Insert the eight-cell marker into **BAT rows 18, 21, 24, 27**, columns **12–19**, with palette selector 7. Spaces leave their existing background cell unchanged; the probe is not a polished text renderer.
3. This includes four candidate horizontal bands that *would* be at nominal pixel y **144, 168, 192, 216** if no scrolling/raster remapping occurs (all inside 224 lines). **The game's per-scanline BYR changes may map these BAT rows elsewhere or not show them at all.**
4. Strictly limit mutations to **VDC1 VRAM**, validate original Geargrafx save header, leave the embedded screenshot/thumbnail unchanged, and refuse to overwrite the input or any existing Slot 4.

**Actual private output computed:** SHA-256 `8ba7ca4ddd2342ee340385bb7e065c34387137ef3c988da15e3da67c3066ca4e`; exactly **196 differing bytes**, all within the first VDC's 64 KiB VRAM; original game data BIN, Japanese CD-DA, all save metadata and original states unchanged.

**Seven local regression tests pass**, including a real-state read-only fixture check, synthetic BAT updates, font packing, palette and tile collision guards, invalid state input, and exact changed-region protection.

### User Geargrafx test

**No new program/game patch needed.**

1. Back up the existing v0.5 states and keep the clean military-camp state1 and original King-dialogue state5.
2. Copy the separately provided **experimental state4** to the directory holding Geargrafx's v0.5 saved states. **Do not overwrite an existing Slot 4**.
3. Launch the original `Xak_III_English_SUB_TEST_v05_Pilot01.cue`, load Slot 4, and advance a few frames while King Wavis is still in his first spoken phrase.
4. Report which `SUB TEST` lines become visible, if any; whether they disappear on frame advance; and whether native animation/audio survive. Return to Slot 5 and delete experimental Slot 4 after testing.

**Interpretation:**
- Some BG letters visible during the opening King's speech ⇒ strong proof that a background-tile subtitle path can bypass the current sprite visibility limitation. Then trace row mapping and implement timed BAT/tile updates on disc.
- No BG letters visible ⇒ **inconclusive**: tile rows may be masked/remapped/overwritten. Inspect BXR/BYR/CR raster state and scene tilemap ownership rather than concluding tiles are impossible.
- Scene corruption ⇒ discard state4 immediately and restore state5. No BIN or source state changes exist to roll back.

### Reference patch status and permissions

The Xak I & II public Track02 and Track05 xdelta binaries were previously retrieved via the GitHub connector and their VCDIFF/LZMA header/window structure examined. They do **not** contain public assembly source; reverse-engineering actual inserted bytes still needs the matching original Japanese Track02/Track05. No need for the user to resend those **public xdelta files**.

The user explicitly requests **approval before ANY future public comment, issue, or outreach message**. Repository-internal development commits are allowed by the established workflow. The previously posted message on the external author's issue has been removed by the user; do **not** repost it without permission.

## Next milestone

If one or more BG rows visibly work, replace the static state test with a verified source-only **disc-native black-band subtitle path**, using staged VRAM writes, native scene synchronization, reliable cleanup, and 224-line safe placement. Keep real v0.5 as the rollback, with its existing unique CUE and save states. This milestone is **not yet achieved**.
