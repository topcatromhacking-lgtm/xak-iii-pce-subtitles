# Pilot 01 — Slot 4 diagnosis and native sprite feed (2026-10-20)

**Status:** Static code/data diagnosis confirmed. Slot-5 native-RAM sprite-feed test built, **not yet runtime-tested**.

The user uploaded a native Geargrafx 1.8.4 state slot 4 about two seconds after resuming the failed slot-3 subtitle probe. Read-only byte-by-byte comparison found:

| Memory or control | Slot 3 | Slot 4 |
|---|---|---|
| Sprite font glyphs (8 patterns) | intact | **unchanged** |
| Live VDC1 SAT | 8 entries | **all zero** |
| VRAM SAT-DMA source, word $0C00 | same 8 entries | **all zero** |
| CR (sprite enable) | $00CC | $00CC |
| DCR (auto-SAT DMA) | $0010 | $0010 |
| DVSSR (SAT source address) | $0C00 | $0C00 |
| VDC1 VRAM differences outside SAT source | - | **zero** |
| CPU PC | $8590 | $8590 |
| CPU bank | $82 | $82 |

44 changed bytes in the 512-byte live SAT and 44 identical changes in the 512-byte VRAM source. The font graphics, VDC registers and game-data banks survived. The CD-DA audio advanced from LBA 164165 to 164321 (approximately 2.08 seconds).

## Actual native sprite-update routine discovered

Disassembly of loaded CD RAM around CPU **$8516–$8596** shows a routine that selects VDC register MAWR, writes the value at game RAM **$233F–$2340 = $0C00** as the VRAM destination, then selects the VWR port. It reads active sprite count at **$3444** (bounded to 64). For each active sprite X it reads an index Y from **$2EA4,X** and writes eight bytes from eight parallel byte arrays to the VDC data ports ($0002/$0003), representing four little-endian SAT words. For unused sprite entries it explicitly writes zeros via four STZ $0002 / STZ $0003 pairs. Both saved states have active sprite count **0**, explaining why the diagnostic sprites are removed.

Byte-array bases, in write order:
`$3264, $32C4, $3324, $3384, $30E4, $3144, $33E4, $3204`.

The physical source of the loaded CPU code was separately resolved to original Track 02 **indexed sector 517** (raw sector 742, PC $8590 at raw byte offset `0x1AA6C0`). The complete 192-KiB scene-data asset starts at indexed sector 541, distinct from active code. **Do not patch a repeated copy of this routine without provenance checks.**

## Native sprite-feed test (slot 5)

The new experimental checkpoint is built from the **user-provided slot 4** and changes **52 bytes exclusively inside CPU WRAM**:
- Count at $3444: zero to **8**.
- Selector table $2EA4,X: indices 0–7.
- Eight parallel sprite-data tables: entries for eight already-present white subtitle glyph sprites, arranged to display `ENGLISH SUBTITLE` near the lower black margin.
- All VDC VRAM, live SAT, PC, CD audio, native screenshot thumbnail and input files are unchanged.

SHA-256 source slot 4: `4cf4f8064b78de6059f5e8f58f6dcc1304e90ab26d4695918e318750a6783a1b`.

SHA-256 generated slot 5: `6ed046b184df5f32ce4371ee81086cf09b3902ac99224db98ba10f4dab418bda`.

**Independent complete 512-byte replay:** the game's native table-read/zero-fill procedure, applied to slot-5 WRAM, produces exactly the intended sprite attribute table from original slot 3. Three synthetic tests passed. This verifies construction, **not** whether the game overwrites WRAM before the next redraw.

### Runtime test

Place `Xak III - The Eternal Recurrence (English v1.0).state5` in the existing Geargrafx state folder. Load slot 5, run the cutscene 2–3 seconds and inspect whether white `ENGLISH SUBTITLE` appears. Preserve slots 1, 3, and 4. If absent, investigate whether $3444 and the sprite tables are cleared by game logic during frame update. No need to try a fourth arbitrary VRAM patch.

Source: `tools/build_native_sprite_feed_v1.py`, `tests/test_native_sprite_feed_v1.py`. Private saved game state and copyrighted graphics are deliberately not committed.
