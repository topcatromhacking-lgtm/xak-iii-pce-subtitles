# Pilot 01: CPU state, code-copy resolution, and sprite subtitle diagnostic

**2026-10-20. Status: offline structural analysis and a Geargrafx save-state-only experimental test. Not a disc/ISO patch, not a functional subtitle engine, no emulator runtime test yet.** The source BINs, audio, save states, screenshots and diagnostic .state2 have not been committed here.

## Deriving the saved CPU state from Geargrafx source

The two original Geargrafx 1.8.4 native **v44** states have a 64-KiB CD RAM region and a separate 192-KiB Super CD card RAM region (mapped to physical banks **$68–$7F**). Their memory-page registers were `FF F8 80 81 82 83 84 00`, making CPU addresses `$8000-$9FFF` map to bank **$82** in CD RAM.

Using the Geargrafx source serialization order (32-KiB WRAM; 64-KiB CD RAM; 192-KiB card RAM; memory tail; HuC6202: 33 bytes; HuC6260: 1,059 bytes; two HuC6270 state blocks: 68,401 bytes each), CPU state begins at native file offset **0x6A2C9**. These offsets were verified against both states, with credible PC, registers and instruction bytes.

| CPU field | Military-camp save | King Wavis cutscene save |
|---|---|---|
| PC | **$8E8F** | **$8590** |
| A | $16 | $00 |
| X | $7F | $17 |
| Y | $18 | $2A |
| Stack pointer | $F8 | $FD |
| Processor flags | $00 | $80 |
| MPR4 | $82 | $82 |
| Mapped CD RAM offset | $4E8F | **$4590** |

The saved PC at $8590 corresponds to a valid HuC6280 instruction sequence in the currently mapped CD RAM; this **does not** prove it is a safe patch hook or called every cinematic frame.

## Identifying the correct disc code copy

A search for a 128-byte sequence at CD RAM offset `$4590` finds **10 copies** in English Track 02. It is unsafe to patch the first hit: the shared code is replicated for several scene groups.

We located independent snapshots of the same loaded CD RAM at offsets `$2000`, `$4000` and `$5000`. The first two code signatures each occur ten times; the `$5000` signature is unique. The **only common disc-to-RAM offset** across all three is **`0xFE800`**.

| Component | Disc indexed ISO user-data offset | Indexed sector |
|---|---|---|
| Loaded CD RAM $2000 code | `0x100800` | 513 |
| Loaded CD RAM $4000 code | `0x102800` | 517 |
| Active PC at $8590 / CD RAM $4590 | **`0x102D90`** | **517** |
| Unique loaded CD RAM $5000 anchor | `0x103800` | 519 |
| 192 KiB exact cinematic card-RAM block | `0x10E800` | 541 |

The scene's active code is thus associated with the **sector-513 group**, not the first shared-code copy at sector 385. Sector numbers above are indexed MODE1/2048 data sectors after Track 02's 225-sector pregap; for the actual raw 2352-byte Track 02 file add 225 sectors. The candidate instruction at PC maps to **raw Track 02 sector 742, byte offset 0x1AA6C0** (verify tool output before editing). This is source provenance, not a proven runtime patch point.

## Experimental sprite proof-of-concept

The audience checkpoint's saved first VDC state has:

- **64 empty sprite slots** in its sprite attribute table.
- Sprite rendering enabled (`CR=0x00CC`, sprite-enable bit set).
- Sprite palette **15**, index **15** equal to 9-bit white (`0x1FF`).
- Blank VDC VRAM sprite patterns at indices 48–51, 56–59, 504–507 (corresponding 8×8 BG tile regions 192–207, 224–239, 2016–2031), unused in the snapshot's active background tile table.
- A completely black lower image area covering the desired subtitle location around pixel **(40,207)** in the captured 256×240 screen.

A private, copy-only state patch writes the white marker **`ENGLISH SUBTITLE TEST`** to 11 custom 16×16 sprite patterns and the first eleven SAT entries. The sprite coordinates use PCE offsets +32 X/+64 Y. No video/voice/audio data or game BIN is altered, and Geargrafx's embedded screenshot and save header are unchanged.

**Statically verified:** only **590 bytes** changed, within the first VDC's 64-KiB VRAM and SAT. Original state SHA-256: `d91527353864d7ac1d5aa3b51239582a68ee642fd9b65a5cc58817075a8dbc6b`; experimental state SHA-256: `db13e5018f591526322ce36990bd498a46ebd0c4c9ff551fbb1b2dc3fe7156e6`. Six synthetic tests passed.

**Not yet verified:** whether loading the modified state displays the white text, whether it persists across frames, whether the game overwrites sprites, and whether the original Japanese Track 28 playback and animation remain unaffected during actual gameplay. An unsuccessful display test would not establish that sprite subtitles are impossible.

## Gameplay verification request

Use **Geargrafx state slot 2** for the private experimental .state2 and preserve the user’s original slot 1. Load the same split-track English CUE, then load slot 2 and allow the first frame to render. Look for `ENGLISH SUBTITLE TEST` in the lower black margin; note whether it persists during the scene or vanishes. **Never replace the original state with a diagnostic.**

## Engineering references

- [Geargrafx memory serialization](https://github.com/drhelius/Geargrafx/blob/main/src/memory.cpp)
- [HuC6280 register serialization](https://github.com/drhelius/Geargrafx/blob/main/src/huc6280.cpp)
- [VDC SAT and sprite rendering](https://github.com/drhelius/Geargrafx/blob/main/src/huc6270.cpp)
- [Previous disc/code/assets mapping](pilot-01-cutscene-overlay-map.md)

**Next:** use user-visible emulator feedback to validate the graphics proof; then trace an actual cinematic VBlank/update routine and design a reversible disc patch that draws and clears subtitles according to **physical CD Track 28 playback**. No new proprietary assets belong in public GitHub.
