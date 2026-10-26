# Yuna 2 technique transfer → Xak III native sprite generator (v0.18 research)

**26 October 2026.** The user correctly emphasized that [Yuna 2](https://github.com/suppertails66/yuna2tools) does not simply turn sprite output on during subtitle areas. It uses a multi-state raster window controller **plus native sprite crop minimization before SAT entries are sent**. This is the missing architectural distinction behind our unsuccessful v0.11–v0.16 cropping tests. This document records authentic source-code and state evidence, not a working v0.18 game patch.

## Directly verified Yuna 2 assembly

[scene_main.s, lines 859–1035](https://github.com/suppertails66/yuna2tools/blob/master/yuna2/asm/scene_main.s#L859-L1035) implements six raster phases:

0. enable top subtitle sprite window
1. disable top subtitle sprite window
2. enable/start native cropped image
3. end native cropped image
4. enable bottom subtitle sprite window
5. end bottom subtitle window

The handler conditionally skips unnecessary phases; uses native scene crop coordinates `cropUpperY=$280D`, `cropLowerY=$280E`; and enables sprites without enabling background in the lower subtitle window. Top/bottom subtitle-window constants are 8–40 and 192–224, respectively, for **Yuna 2**; these are **not** Xak III coordinates.

[scene_main.s, lines 1458–1805](https://github.com/suppertails66/yuna2tools/blob/master/yuna2/asm/scene_main.s#L1458-L1805) hooks the native writer at `$48F2` using `JMP doSpriteCropMinimize` immediately before native eight-byte SAT transfer `TIA $28C1,$0002,$0008`. The routine can completely reject sprites by jumping to the preexisting no-send continuation `$48FC`, or reduce partially visible 32px/64px sprites before sending by updating their Y, pattern and height. Its code explicitly handles Y-flipped sprites and mentions the fundamental **absence of a 48px hardware sprite height**, so chunk minimization is **not pixel-perfect cropping**. In particular, minimizing partial sprites may still expose 1–15 lines near a boundary unless the raster/window system also confines the output.

[scene_main.s, lines 1080–1250](https://github.com/suppertails66/yuna2tools/blob/master/yuna2/asm/scene_main.s#L1080-L1250) shows a separate subtitle SAT-writing path and frame-level SAT management. The `spriteCropMinimize_on` toggle is activated by a subtitle-related cutscene opcode around [line 3153](https://github.com/suppertails66/yuna2tools/blob/master/yuna2/asm/scene_main.s#L3153).

## Xak III's actual equivalent, recovered from real native Geargrafx state

The user's pixie-glitch checkpoint `Xak_III_English_SUB_TEST_v14_Pilot01.state1` (749238 bytes) has original HuC6280 code loaded in bank82. We inspected it directly:

| CPU | Existing behavior | Consequence |
|---|---|---|
| `$843F–$8503` | Native sprite candidate evaluation and attribute construction | Earliest practical interception area |
| `$84CA–$84EF` | Convert fractional/8-bit producer coordinates into SAT Y/X arrays `$3264/$32C4` and `$3324/$3384`, fill pattern `$30E4/$3144` and flags `$33E4/$3204` | Cropping needs to use converted screen-space SAT coordinates, sprite heights, patterns and flip bits |
| `$84F0–$84FA` | Assign candidate array index to native queue `$2EA4` and increment `$3444` | **Useful possible producer-hook site before native queue commit, rather than changing the final SAT** |
| `$8516–$8594` | Consume queue and write eight SAT attribute bytes per sprite to VDC1 `$0002/$0003` | Native output serializes here, after generation |
| `$9C4B–$9C94` | Our distinct v0.5 subtitle hook inserts four sprite entries by appending to same generated queues | **Native producer interception does not have to alter subtitle sprites** |

The code fingerprints were validated against the authentic checkpoint, and a read-only Python analyzer verified that the producer's `$3444=23` queue is **19 original native sprites plus 4 subtitle entries**. Unlike the VDC1 live SAT and VRAM SATB source, the native producer queue is reconstructed from `$2EA4` order and eight attribute arrays, all in work RAM. **These are different production stages and must not be conflated.** Previous v0.15 edits to final live/shadow SAT were transient and never blocked the native generator from recreating leaking elements.

### Exact pixie frame classifications

For the measured sample picture interval **Y=50–177 inclusive** only:

| Producer classification | Number |
|---|---:|
| Entirely above visible picture | 7 native |
| Intersect top boundary | 6 native |
| Fully inside | 6 native |
| Our text at Y184/204 | 4 protected |

A number of the above-picture sprites start at Y−3, Y13 or Y29, and can be rejected without discarding visible pixels in this *one measured frame*. Some partially visible sprites are 32/64px tall; Yuna-like height/pattern trimming can reduce their overlap, but may leave residual lines because **16px is the minimum height**.

**Do not generalize screenshot Y50/178 as Xak III's universal crop rule.** We must identify native scene crop values or derive the per-scene picture phase from its raster table (VDC1 CR updated by `$65A7`, table `$3E72,X`) and/or scene registers. Static raster-table bytes rotate as the line engine advances; raw $80/$C0 values alone are not exact Y boundaries. A new hook must be enabled only during the relevant subtitle-bearing cinematic and preserve native animation in all other scenes.

### Code patch planning: not yet tested

- Preserve proven **v0.10** disc baseline and preferred **v0.14 Slot4 / v0.16 Slot5** centered black-band text; v0.17 disc-native placement has **not** been confirmed in a fresh emulator run.
- A small native candidate filter may replace the `LDA $3444` instruction starting at **CPU `$84F0`** with a same-bank-safe jump to guarded free code, perform an early native-only reject/trim, then either execute the preserved instruction and continue at `$84F3` or take the original no-queue continuation at `$84FB`. **Branch and register semantics must be checked against the real HuC6280 control flow before writing a runnable patch.**
- The loaded frame has a consecutive zero block `$76E9–$77FF` observed in four genuine checkpoints; this is a **candidate cave**, not yet proven safe across all modules and disc source. Never place code there without verifying source bytes and runtime lifetime.
- This native generator lives on raw **Track 02 sector 742**, based on the already verified source bank mapping, with `$84F0` mapping near raw byte `0x1AA620`. Those addresses are a **candidate**, not a validated original-disc patch: the exact original BIN is on the user's PC.
- For full cropping, the hook must adjust SAT Y, pattern base and flags with Y-flip logic, preserve each original native sprite width, avoid the unavailable 48px height, protect text sprites and SAT limits, and coordinate with discrete raster subtitle-window states. Do not indiscriminately force sprites on in upper/lower blank bands or enable BG there (v0.11 leaked native pixels; v0.12 exposed hidden BG art).
- Work must be tested in **actual Geargrafx** from a clean scene and via a reproducible mid-scene pixie checkpoint, not treated as successful from offline hashes alone. Protect original BIN, CDDA, original states and save slots.

## Reproducible read-only analysis artifacts

The private conversation download `Xak_III_v18_Yuna2_Native_Producer_Research_Source_Only.zip` contains a source-only parser, **11 passing synthetic tests**, README and a 10.8KB JSON report produced from the user's legitimate checkpoint. No game/state bytes are included. The JSON includes sprite attributes and fingerprints for debugging; it is **not committed publicly**.

Command (optional, only if repeating locally):

```powershell
py -3 analyze_xak_iii_native_sprite_producer.py --state ".\Xak_III_English_SUB_TEST_v14_Pilot01.state1" --report ".\pixie_native_queue.json"
```

**Next milestone:** implement guarded producer interception and a scoped Yuna-inspired native cropper, *not* another saved SAT mask. Preserve original upper/cropped-picture/lower subtitle-window states and verify no pixie/hero/NPC/mouth leakage or text regression.

No third-party public comments or outreach without user's prior approval.
