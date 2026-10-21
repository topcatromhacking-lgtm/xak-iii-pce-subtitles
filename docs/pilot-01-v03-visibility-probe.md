# Pilot 01 v0.3 — subtitle visibility diagnostic (source-only test)

Date: 2026-10-21. **Status: prepared offline; not yet tested in Geargrafx.**

## Why v0.2 is not a visible subtitle

A user-supplied Geargrafx v44 `.state4` saved **14.4305 seconds into physical Track 28** was inspected read-only. The original Japanese voice track plays. The injected hook at CPU `$8EE5 -> $9C00` is resident and initialized; the original `$8593: STZ $3444` sprite-count cleanup remains intact.

All four expected subtitle entries occur in both the live SAT and its automatic-DMA shadow. Sprite display is enabled in the **saved** VDC1 control register (`CR=$00CC`), but that snapshot alone cannot establish the control state throughout each raster line. The diagnostic font patterns **30 and 31 were overwritten** by the game, while patterns **43 and 56 survived**. The embedded framebuffer has no marker pixels in the expected lower-margin rectangle. The tester reported never seeing `SUB TEST` in normal playback.

Thus there are at least two hypotheses to separate: **VRAM pattern reuse** and **raster-line/cropping display suppression**. Merely relocating VRAM patterns without controlling their lifetime is inadequate.

## External implementation references inspected

- [Galaxy Fraulein Yuna: scene sprite clear interception and sync refresh](https://github.com/suppertails66/yunatools/blob/master/yuna/asm/overlay/scene.s) — protects subtitle SAT data during native sprite clears and updates the SAT/palette in sync logic
- [Galaxy Fraulein Yuna 2: raster-controlled subtitle windows](https://github.com/suppertails66/yuna2tools/blob/master/yuna2/asm/scene_main.s) — turns sprites on in subtitle windows; handles cropping and palette fades
- [Emerald Dragon: subtitle and SAT timing](https://github.com/suppertails66/emdrtools/blob/master/emdr/asm/generic/scene/scene_std.s) — waits for SAT update before displaying subtitle windows

These are conceptual implementations, **not drop-in patches** for Xak III. We should independently establish Xak III's own VDC timing before editing its line interrupts.

## v0.3 controlled experiment

A separate, reversible **source-only builder** was prepared and supplied in the development conversation, not yet added to this public repository. It requires the user's own pinned v0.2 raw Track 02 and CUE and generates new `v03` BIN, CUE, delta IPS and report alongside the originals. It **never overwrites v0.2**.

The builder makes only these intended hook changes within raw **sector 745**:

1. CPU `$9C08`: `D0 41` (`BNE`, skip first-load glyph transfers) -> `EA EA` (`NOP NOP`), so all four glyph patterns refresh on every scene-loop call.
2. CPU `$9C9A–$9CA1`: four SAT Y positions change from `$010F` (visible y=207) to `$00C0` (visible y=128). This relocates the marker to the active picture rather than the lower letterbox.

Other sprite fields, the game-native writer, the original `STZ $3444`, the rest of the data track, and all 34 unmodified CD audio tracks are preserved. MODE1 EDC/ECC is regenerated and checked. The generated delta IPS is verified by a round-trip test; input SHA-256 is pinned to v0.2 `c69aa8dd3f0878dc70e8e80f804d0160a5b5c3572c4bad9ebcea711082a2268d`.

Five local **synthetic/offline** tests passed. Since there is no v0.2 54-MB BIN in the assistant's working environment, no complete new BIN hash or actual new Geargrafx display is asserted. Source and synthetic QA do **not** establish runtime success.

## Next checkpoint and decision

Boot the generated v0.3 split CUE from a verified clean military-camp save, then enter the throne room normally and watch the white `SUB TEST` marker at **screen y≈128** for at least ten seconds. Preserve earlier checkpoints; save a new later-scene state in a free slot.

- **Visible, stable marker:** rendering is possible in the central picture; refine glyph ownership and then implement proper raster-window placement.
- **Visible but flickering/slowing:** identify frame-safe VRAM transfer scheduling and shorten transfers.
- **Still invisible with all four glyphs preserved:** trace active/latched CR and sprite fetch in the actual scanline; move to a Yuna 2-style raster-window intervention after determining Xak III's own crop/interrupt logic.
- **Freeze or corrupted picture:** revert immediately to untouched v0.2. No risky NOP of native count cleanup is permitted.

This is a short **diagnostic**, not a release or synchronized English subtitle translation. Do not commit personal game disc images, private save states, audio, or screenshots to the public repository.
