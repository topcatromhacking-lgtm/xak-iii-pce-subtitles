# Pilot 01 — slot 5 failure explained; slot 6 controlled native-routine re-entry

**20 October 2026.** Slot 5 was reported **invisible in Geargrafx**. It is **not** a working subtitle patch.

## Verified flaw in slot 5

The CPU saved in slot 5 resumes at **PC $8590, X=$17** (bank $82). The sprite-list copy section earlier in the Xak III routine already checked the count of active sprite records (WRAM **$3444**); at $8590 it is executing a loop that **zero-fills unused SAT entries**. On exiting this loop it executes **$8593: `9C 44 34` = `STZ $3444`**.

Consequently, slot 5's modification of `$3444` to **8** arrives *too late* to be consumed by the already-active invocation, then the original routine clears it before a subsequent invocation. The earlier static SAT-table simulation was correct in isolation but did not account for the saved PC and loop phase. This explains why the statically valid sprite queue didn't appear. The bug is in the test setup, not necessarily sprite capability.

This diagnosis was cross-checked with the actual saved CPU state and [Geargrafx HuC6280 opcode implementation](https://github.com/drhelius/Geargrafx/blob/main/src/huc6280_opcodes.cpp), not inferred merely from video.

## Slot 6 private diagnostic

A corrective state-only test, derived from the **verified slot 5** checkpoint, changes exactly **4 bytes**:

- Saved HuC6280 **PC $8590 → $8516** to restart the same sprite table writer from its entry. Only the low byte of the serialized PC changes.
- Three executable bytes in the saved **CD RAM** at bank $82, CPU **$8593**: `9C 44 34` (`STZ $3444`) → `EA EA EA` (three NOPs). This preserves the test's eight WRAM sprite records for subsequent calls.

**No CD disc, BIN/CUE, game file, audio, subtitle font sprites, WRAM records, VDC graphics, sprite tables, or original save state is changed.** This RAM code modification is for diagnostic use only; do not keep playing/saving from it once the test ends.

- Slot 5 baseline SHA-256: `6ed046b184df5f32ce4371ee81086cf09b3902ac99224db98ba10f4dab418bda`
- Slot 6 experimental SHA-256: `65cd995a37490f80208a52bcdee1c381927e3066aded4534ff4a32e395087c76`
- Changed state-file offsets: `0xC5AC`, `0xC5AD`, `0xC5AE`, `0x6A2C9`.

## Independent static verification

- Geargrafx save-state header, ROM CRC, card RAM, WRAM, VRAM, sprite source, screenshot and audio are unchanged.
- An instruction-level model of **the actual HuC6280 code at $8516–$8596** reads eight queued records and writes **512 VDC SAT bytes**: eight expected 8-byte entries and 56 empty slots.
- The modified routine leaves the count at 8 and reaches the normal RTS. Three independent local verification tests passed.
- **Emulator runtime is untested**. We do not yet know whether the game resets sprite records elsewhere or whether the marker renders.

## Test in Geargrafx

Keep all source saves untouched. Place the private `.state6` test snapshot alongside slots 1–5, load **slot 6**, and watch the running King Wavis scene for 2–3 seconds. Look for white **ENGLISH SUBTITLE** in the lower black region. Do not judge by the thumbnail. Report appearance, flash/persistence, and whether the scene advances.

If slot 6 still fails, stop speculative save-state tests and capture a live CPU/VDC trace around this routine. The final translation solution will need a proper code hook, timed cues bound to physical CD Track 28, and normal sprite-table coordination. No proprietary ROM, music, videos or private save states are committed to this repository.

Related work: [native sprite writer](pilot-01-slot4-native-sprite-writer.md) and [previous sprite test](pilot-01-sat-dma-v2-diagnostic.md).
