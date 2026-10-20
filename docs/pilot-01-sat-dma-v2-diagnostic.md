# Pilot 01: Sprite proof v1 failed; corrected DMA-safe slot 3

**2026-10-20.** The user confirmed the original slot-2 marker was **not visible immediately** after loading in Geargrafx. Therefore v1 is a **failed runtime experiment**, not a validated subtitle technique. The screenshot, game images and experimental private save files are not committed here.

## Identified root cause from Geargrafx VDC implementation

The King Wavis cutscene snapshot has:
- VDC1 CR = 0x00CC, sprite rendering enabled.
- VDC1 DCR = **0x0010**, automatic sprite attribute table (SAT) DMA on VBlank.
- VDC1 DVSSR = **0x0C00**, providing a **512-byte SAT shadow** inside VDC video RAM, at word addresses 0x0C00–0x0CFF.
- Both the live SAT and its shadow originally all zero.

The first diagnostic wrote **only** the live SAT. It also placed four of its font sprite patterns in sprite-pattern indexes **48–51**, which are *exactly the same video-RAM words as that SAT DMA shadow*: pattern 48 begins at word 48×64 = 0x0C00. Thus the next automatic SAT transfer could overwrite the live sprites with **font plane bytes misinterpreted as sprite coordinates and flags**. Its priority flag was also background-priority, potentially hiding sprites behind the black BG area.

**Consequently:** this test was invalidated by its own resource collision. It did not rule out sprite subtitles.

## Corrected save-state diagnostic (slot 3)

The revised diagnostic, maintained in the private test package, uses:
- Text **ENGLISH SUBTITLE**, eight 16×16 sprites at approximate screen (64,207).
- Blank VDC sprite patterns **504, 505, 506, 507, 30, 31, 43, 56**, disjoint from the SAT shadow **and not referenced by background tiles visible in the saved frame**.
- **Foreground** sprite flags 0x008F (white palette #15).
- Both live SAT and the entire 512-byte DVSSR source mirror containing exactly the same sprite entries, so the automatic VBlank SAT DMA now reloads the intended sprites.
- Original DCR, CR, DVSSR, all CPU/WRAM/CD/ADPCM, disc/voice tracks, emulator screenshot thumbnail **unchanged**.

Verification against the original **Geargrafx 1.8.4, v44** cutscene save:
- Original SHA-256: `d91527353864d7ac1d5aa3b51239582a68ee642fd9b65a5cc58817075a8dbc6b`
- New diagnostic SHA-256: `0abf78b8bbc7f338b29f51e47d4cfc769d2465a985fc9e7953af9f4ef9defc05`
- Exactly **508 bytes** changed, restricted to VDC1 VRAM + live SAT.
- Six synthetic QA tests passed, plus checks against the actual original state.

**Runtime validation pending.** Place private test state in slot 3 alongside the original user-owned slot 1, load in Geargrafx, and look for white marker text in the running game, not in the save-state thumbnail. If this still fails, obtain a screenshot or trace the actual VDC writes instead of cycling through further speculative save-state variants.

## References

- Geargrafx VBlank automatic SAT transfer and source: https://github.com/drhelius/Geargrafx/blob/main/src/huc6270.cpp
- Earlier erroneous sprite state test: [CPU and sprite pilot](pilot-01-cpu-sprite-probe.md)
- Normal voice: physical CD Track 28; this experiment never modifies it.

This is **not** a completed subtitle renderer and does not provide English timed subtitles yet.
