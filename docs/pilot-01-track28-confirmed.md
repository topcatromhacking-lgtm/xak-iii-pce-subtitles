# Pilot 01: King Wavis cutscene audio track confirmed

**October 20, 2026.** Read-only comparison of two Geargrafx v44 save states and the English v1.0 *single-BIN* CUE. Neither save state, screenshot nor proprietary audio has been committed here.

## Independent audio mapping

| Field | Military-camp save | Royal-audience save |
|---|---:|---:|
| CD-DA playback | Playing | Playing |
| Start LBA | 55,093 | **164,129** |
| Current LBA | 56,407 | **164,165** |
| Stop LBA | 61,725 | **178,493** |
| Stop mode | Loop | Interrupt |
| Time since audio start | 17.5231 seconds | **0.4901 seconds** |
| **Physical CD track** | **06** | **28** |
| Track length | 88.4267 seconds | **191.52 seconds** |

The single-BIN CUE lists Track 06 at `12:09:43` = LBA 54,718 and Track 28 at `36:23:29` = LBA 163,754. **Both saved CD start LBAs are exactly 375 sectors after those CUE positions**, and both saved CD stop LBAs exactly match the corresponding *next* track index plus 375 sectors.

Thus this is not just an inference from soundtrack numbering: the King Wavis audience **plays physical disc Track 28**, 3:11.52 long. The save was taken approximately 0.49 seconds after audio playback began. This is a reproducible synchronization anchor, not yet a tested subtitle timing implementation.

The two states have matching disc CRC `EDFD65CB`, MPRs and Geargrafx emulator version 1.8.4. The earlier state shows the military camp. The new state's embedded screenshot shows King Wavis's royal throne room.

## Scene memory change

The camp save contains 192 KiB of card RAM with many readable English dialogue strings, including speaker labels. The audience state's card RAM is largely replaced with other data and almost none of those strings remain; its appearance suggests a separate cinematic overlay loaded over the ordinary dialogue resources. **This is a memory observation, not yet proof of the rendering/control-flow mechanism.**

## Next steps

- Use the confirmed **Track 28 start** as the scene audio timing origin. Align the existing English transcript to actual Japanese voice timings using Track 28 audio or the user's 3m36s recorded cinematic.
- Trace the executing cinematic update/render code with the user's second Geargrafx save state; the standalone CD BIOS byte signatures in the data track are not validated call sites.
- Locate a safe text- or sprite-rendering hook, confirm memory budgets, and test a **single English subtitle with the original Japanese voice**.
- Keep the original split-track disc, source saves and all original audio outside the public repository; publish only research, tool sources and redistributable patches.

**Status:** physical voice-track mapping **confirmed**, game-native English subtitle renderer **not built or runtime-tested**.
