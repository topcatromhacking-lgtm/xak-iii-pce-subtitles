# Xak III Pilot 01 — v0.6 negative test and raster trace next

**2026-10-24. No v0.7 game patch has been built.**

## User-reported v0.6 result

The source-only v0.6 probe placed four existing sprite-font fragments at distinct screen Ys **64, 88, 112 and 136**, retaining v0.5's stable pattern IDs **59, 56, 57 and 58**. The tester reports **none of the fragments appears during the King's initial speech; rendering still begins only at the hero's first dialogue**.

This is a **real test observation**, but no new v0.6 save state or trace file was supplied for independent memory analysis. It argues against a simple fixed-Y clipping issue. Do not overclaim that it proves sprites were disabled; sprite limit, priority, raster writes, palette changes and compositor behavior can be frame-dependent.

## Direct comparison of existing genuine v0.5 states

The original v0.5 Slot 5 was taken as King Wavis starts speaking at **5.2873 seconds** into physical Track 28; the v0.5 Slot 3 is **129.9988 seconds**, with visible stable `SUB TEST`. Both are native Geargrafx 1.8.4/v44 files, inspected read-only.

| Saved measurement | Early King / v0.5 Slot 5 | Later visible / v0.5 Slot 3 |
| --- | --- | --- |
| CD-DA position | 5.2873s | 129.9988s |
| VDC1 CR (register 5) | `$00CC` | `$00CC` |
| VDC1 **latched** CR | `$00CC` | `$00CC` |
| VDC1 HDR (register 11) | `$041F` | `$041F` |
| VDC1 RCR (register 6) | `$0040` | `$0040` |
| VDC1 MWR (register 9) | `$0050` | `$0050` |
| VDC1 DVSSR | `$0C00` | `$0C00` |
| VCE sprite palette 15 / color 15 | `$01FF` | `$01FF` |
| VDC2 CR | `$0000` | `$0000` |
| Serialized HuC6202/VPC mixer settings | 33 all-zero bytes | identical |
| VRAM font patterns 59,56,57,58 | intact | byte-for-byte **identical** |
| Four subtitle SAT records | indices 0–3 | indices 1–4 |
| Number of nonempty live SAT entries | 4 | 5 |
| V0.5 hook initialization flag `$9C99` | `$00` | `$00` |
| Visible subtitle in embedded frame | **No** | **Yes** |

Original SAT Y=192 / screen Y=128; four records use SAT2 `$76,$70,$72,$74`, flags `$008F` and hardware X=64,80,96,112.

The comparison rules out a **static** missing font, missing live SAT record, absent initialized hook, saved palette problem, saved CR bit or saved display-width difference. The early state has fewer SAT sprites than the later, making static SAT saturation implausible at that instant.

**Important limitation:** Geargrafx snapshots are not a record of prior scanlines. Identical CR and latched CR at the **save instant** do **not** prove identical per-line sprite enablement, SAT transfer timing, priority effects or window control throughout the earlier frame. These are hypotheses to instrument, not results already established.

The read-only state comparison is reproducible using the new private-source-free tool `tools/compare_xak_subtitle_stage_v07.py`, intended for Geargrafx 1.8.4/v44 **749238-byte** native saves. It does not write save states, discs, or game media.

## Decisive next test: Geargrafx VDC hardware trace, no new patch

Geargrafx's own current [Trace Logger GUI source](https://github.com/drhelius/Geargrafx/blob/main/platforms/shared/desktop/gui_debug_trace_logger.cpp) supports **Filters > VDC / VPC > Register Writes, IRQs, DMA, Sprite Budget**, CPU trace filtering, and **Disk** output. The [trace formatter](https://github.com/drhelius/Geargrafx/blob/main/platforms/shared/desktop/trace_logger_formatter.cpp) labels `CR($05)`, `RCR($06)`, `HDR($0B)`, SATB DMA, VBlank/scanline IRQs, and sprite limit hits. Check whether these controls exist in the tester's installed Geargrafx build; public `main` source may be newer than the installed binary.

Recommended narrow trace:
1. Launch the original **v0.5** split CUE (not v0.6) and load the existing **v0.5 Slot 5** at the King's first spoken phrase. Pause.
2. In **Trace Logger** select **Disk** output (e.g., 10 or 50 MB), **disable CPU Instructions**, enable **VDC / VPC Register Writes + IRQs + DMA**, and optionally **Sprite Budget > Limit Hits**. Extra non-VDC tracing is unnecessary.
3. Start capture, resume the King's speech, then stop immediately after the hero's first dialogue starts and the marker becomes visible.
4. Preserve the log file. Compare register 5 low-byte values for sprite-enable bit 6, raster IRQ timing, SATB DMA and any sprite limit events before and after the visual handoff.

**Do not** install a second scene hook, move the glyph again, force CR values blindly, or bypass native `STZ $3444` while the frame pipeline is untraced. Once a CPU origin and display handoff are known, produce a tightly scoped v0.7 reversible patch with its own unique CUE and five save slots.

Previous: [v0.6 raster-band experiment](pilot-01-v06-early-king-raster-band.md); [v0.5 early-scene valid hook](pilot-01-v05-verified-early-speech-gap.md); [Xak I/II technique comparison](xak-i-ii-subtitle-technique-comparison.md).
