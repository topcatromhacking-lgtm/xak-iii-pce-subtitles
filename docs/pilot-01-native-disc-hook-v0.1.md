# Pilot 01 v0.1: disc-native subtitle sprite hook (offline-verified)

**2026-10-20. Status: experimental, NOT tested in Geargrafx.** This is the first prototype patching the reconstructed **English game data track**, not a save state. Do not publish complete copyrighted game BINs, CDDA tracks, screenshots or save states to this public repository.

## Intent

Show the small white marker **SUB TEST** in the black margin of the King Wavis royal-audience cutscene while original Japanese Track 28 plays. This checks the display mechanism. It is **not** yet line-timed English dialogue.

## Baseline

- Reconstructed English split raw Track 02 SHA-256: `c3aef214616309a6a87f9836bdc8062e57b3e2d5b492b089f72fd52848cd9b72`
- Experiment output SHA-256: `4024e7bbe27af906d9475a83f97cf3d4a82ddc9ed65b00041d8f84cc5f2e8c51`
- Delta IPS SHA-256: `fc32848b603f7e9e6b4bd4b1b8bcbbdbfa70100cc5eaaf44659aa1b6af8ad8dd`
- Raw size stays **54,773,376 bytes**.
- Only **raw sectors 743 and 745** (indexed data sectors 518 and 520) change; all other sectors, Japanese audio tracks and disc timing remain byte-for-byte unchanged.
- Original mode-1 EDC, ECC-P, ECC-Q regenerated for both sectors, verified against recomputed parity. IPS applies and reproduces target SHA-256.

## Specific changes

| CPU/ROM location | Baseline | Experiment |
| --- | --- | --- |
| Loaded bank $82, scene main-loop `$8EE5` | `20 16 85` (`JSR $8516`) | `20 00 9C` (`JSR $9C00`) |
| Raw Track 02 byte offset `0x1AB145` | old call | new call |
| Code padding `$9C00–$9FFF` | 1024 bytes of `FF` | 653-byte code/font payload beginning `$9C00` |
| Raw Track 02 byte offset `0x1AC0C0` | code cave start | new hook data |
| Native `$8593` | `9C 44 34` = `STZ $3444` | **UNMODIFIED** |

The code is mapped from indexed ISO region based on an exact loaded-CD-RAM/disc-image correspondence, checked against the clean Geargrafx royal-audience snapshot.

### Hook lifecycle

1. Save A, X, Y on the stack.
2. On first invocation only, use HuC6280 `ST0/ST1/ST2` and `TIA` to upload four independently generated 16×16 white sprite glyphs to VDC1 patterns **504–507**; flag is self-modified in the loaded CD RAM.
3. Inspect the native sprite queue at `$3444`. If count exceeds 60, do **not** inject.
4. Otherwise append four native sprite records using selector indices **92–95** and eight existing per-sprite data arrays. Position is approximately x=80, y=207.
5. Restore A, X, Y; call original `JSR $8516`; return to scene loop.
6. Crucially, original `STZ $3444` in the native writer resets the transient count **every frame**. We never NOP or bypass it.

The sprite patterns and high data-array indices were unused in the provided scene snapshot, but *possible reuse at other frames has not been ruled out*. The patch is therefore diagnostic rather than release-ready.

## Offline quality assurance

An independent minimal HuC6280 interpreter executes all instructions in the injected hook, models the actual native sprite writer, and verifies:

- Register preservation and original writer called exactly once per frame
- Four sprites added in correct 8-byte SAT word order
- Glyphs uploaded to correct VRAM address via 512-byte alternating-port `TIA`
- One-time initialization (no repeated graphics upload)
- Count reset after native rendering across repeated calls
- Existing sprite lists can coexist (counts 1, 59, 60)
- Saturation protection skips injection for counts 61, 64, 95
- MODE1 EDC/ECC reconstruction and IPS encode/decode roundtrip

**Eight synthetic tests pass**, as well as independent raw-BIN differential checks against the original user-provided English Track 02. These tests **do not emulate the whole game, frame scheduler, VBlank interrupts, scene transitions or original PCE VDC silicon.** No claim of successful real gameplay, visual output or audio synchronization is made.

## First runtime experiment

The **1,091-byte** delta patch is now available at [patches/Xak_III_Pilot01_SUB_TEST_Track02.ips](../patches/Xak_III_Pilot01_SUB_TEST_Track02.ips). Its published Git blob SHA-1 (`a1d43deb30f99d309e13ebfee5dce7de8fe5558d`) was independently matched against the original local binary's Git blob SHA-1, and its SHA-256 is pinned above. A source/QA archive and a separate ready-to-test **private** English raw Track 02/CUE archive were also prepared in the ChatGPT conversation; the full derived BIN is **not** included in this public repository. Use only an authorized personal copy.

1. Back up the approved English disc and original Geargrafx states.
2. Put the experimental English Track 02 and its dedicated split CUE in a **separate copy** of the existing game folder, alongside original Japanese audio Tracks 01 and 03–35.
3. Boot the **new CUE** in Geargrafx.
4. Start from the earlier military-camp **slot 1**, progress into the audience scene and look for white **SUB TEST** near the bottom. The already-in-scene slots 4–7 contain old resident code and are unsuitable for testing an on-disc change.
5. Verify normal Japanese voice, artwork and animation. If game behavior is abnormal, stop and restore the backup.

A successful marker is only the **first graphics proof**. Actual subtitles will need live timing against physical Track 28, text scripts, scene-skip handling and a tested cleanup lifecycle.


## Geargrafx save-state CRC compatibility verified

The [Geargrafx CUE/BIN implementation](https://github.com/drhelius/Geargrafx/blob/main/src/cdrom_cuebin_image.cpp) computes its disc identity CRC32 from **indexed data sectors 1–64** of the first MODE1 data track. Independently applying this exact algorithm to the original English Track 02 and the patched output yields **`EDFD65CB`**, which matches the `rom_crc` and serialized content CRC in the original Geargrafx slot-1 save state. The experimental patch changes only indexed sectors **518 and 520**, leaving this CRC source unchanged. Therefore the clean military-camp save should remain loadable after switching to the experimental English split-track CUE. This is a verified *format/identity check*, not a substitute for actual emulator playback testing.

## Prior results

- [Slot 7 sprite-counter overflow and reason to retain the original reset](pilot-01-slot7-sprite-overflow.md)
- [Track 28 confirmed](pilot-01-track28-confirmed.md)
- [192KB cinematic data overlay](pilot-01-cutscene-overlay-map.md)
