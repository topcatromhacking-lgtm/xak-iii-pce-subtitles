# Verified Japanese/English disc comparison

**Research baseline: October 19, 2026.** Results verified against the user-supplied 35-track Japanese CUE, 54,773,376-byte raw Track 02, and the original NightWolve English translation PPF3 package. **No subtitle patch or emulator-tested reconstructed disc exists yet.**

## Disc layout

- Japanese CUE lists 35 individual BIN files. Track 02 is MODE1/2352 game data; all other entries are AUDIO.
- Raw Track 02 is 23,288 sectors × 2,352 bytes = 54,773,376 bytes. Its 225-sector INDEX 00 pregap leaves 23,063 indexed data sectors, each holding 2,048 user-data bytes.
- English release CUE uses one combined BIN. Rebase its PPF offsets against the separate data track by **7,385,280 bytes**, using the known Track 02 index origins.
- Preserve the original INDEX 00/INDEX 01 layout and all original CD-DA files. OST MP3 numbering is **not** proof of physical voice-track IDs.

## Cryptographic identities

| Input or output | SHA-256 |
| --- | --- |
| Japanese split Track 02 | af04551ce4bf60d50397e99a6467c9e081b3091caa4eb95c67e7984578021733 |
| English source BIN patch Xak3BINB.ppf | 45c6938e87d7baf334b2715b55ab1e9521343d43f8075ea239ed1b290e571fac |
| English source ISO patch Xak3ISOB.ppf | 4be6f96ae9a5fd1588ef308e5cfe732da83f5fbf77ae14da43242f2a2f7e0ee6 |
| Reconstructed English raw Track 02 | c3aef214616309a6a87f9836bdc8062e57b3e2d5b492b089f72fd52848cd9b72 |

## Independent binary verification

- BIN PPF: 8,537 edit records, 359,142 changed byte positions.
- ISO PPF: 5,882 edit records, 274,469 changed user-data byte positions.
- 365 of 23,063 indexed data sectors changed; 84,673 changes lie outside 2,048-byte user data (EDC/ECC).
- **Every indexed translated user-data sector agreed** with the separately ISO-PPF-patched result.
- Track 02 pregap and every raw sector header were preserved.
- Readable English speaker dialogue appears in translated data (example: Ratok: at raw offset 0x6997E3). This is not yet an identified runtime script or cutscene hook.

The rebuild and verification script is [tools/rebuild_english_track02.py](../tools/rebuild_english_track02.py). The original ROMs, proprietary audio and third-party PPF bytes are deliberately omitted from this source repository.

## Remaining uncertainties

- Actual cutscene-to-CD-DA/ADPCM voice mapping remains unconfirmed.
- No established free RAM, VRAM or cutscene update-loop hook.
- No proven emulator playback of the reconstructed split-disc combination.
- No synchronized English subtitle engine has yet been compiled or demonstrated.
