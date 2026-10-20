# Pilot 01: slot 7 frozen-state forensics (2026-10-20)

**Result: Slot 6 was an unsafe experiment. Do not continue normal gameplay from slot 6 or 7.** User-owned Geargrafx save states and game files were analyzed read-only, and are not published here.

## Comparison

| Observed field | Slot 6 starting snapshot | Slot 7 frozen-frame snapshot |
|---|---|---|
| Geargrafx native state | 1.8.4, v44 | 1.8.4, v44 |
| Saved CPU PC, bank $82 | $8516 | **$84F0** |
| Sprite count at WRAM $3444 | **8** | **247 ($F7)** |
| Cleanup at CPU $8593 | EA EA EA (NOPs) | **EA EA EA (NOPs)** |
| CD Track 28 position | 2.56 s | 24.43 s |
| Active and DMA-source sprite tables | Empty | Many entries, matching |
| Saved file SHA-256 | `65cd995a37490f80208a52bcdee1c381927e3066aded4534ff4a32e395087c76` | `87a3ce1b27f054cb82bc69f3ed25b6743e63e9b91ad8e858901cb4e9a40146dd` |

The CPU at **$84F0** lies inside the native sprite collector. Its exact saved bytes decode as:

```asm
$84F0 AD 44 34    LDA $3444
$84F3 42          SAY                ; swap A and Y
$84F4 99 A4 2E    STA $2EA4,Y
$84F7 42          SAY
$84F8 EE 44 34    INC $3444
```

The sprite selector table is **96 bytes** ($2EA4–$2F03; its initialization routine terminates at `CMP #$60`). From count 96 onward, registering more sprites corrupts adjacent WRAM, initially the next table at **$2F04**, and from count 192 the sprite position data beginning at **$2F64**. At saved count **247**, the next indexed selector write would target **$2F9B**. The previous overflow range is **$2F04–$2F9A**.

The normal sprite-table copier only displays a maximum of 64 records, and at **$8593: `9C 44 34` = `STZ $3444`**, it clears the transient count. Slot 6 deliberately replaced that instruction with three NOPs, allowing the count to accumulate across scene updates. This **directly explains the corrupted sprite state and strongly accounts for the apparent freeze**. A single snapshot does not show the exact moment the visible picture stopped updating, nor prove the CPU had completely halted.

We also identified the natural loop call site: **$8EE5: `20 16 85` = `JSR $8516`**. This address corrects an earlier preliminary note that said $8EE3. The normal loop includes other scene and frame calls, which must be traced before treating this as a safe subtitle insertion hook.

## Next engineering direction

1. Use the **clean slot 4** and preserve **$8593: STZ $3444**. Do not use or repair the corrupted slot 7 state for further gameplay.
2. Set a non-mutating Geargrafx execute breakpoint at **$8EE5**. Confirm repeated execution, CPU state and the normal zero/reset lifecycle of $3444.
3. Trace the collector at $84F0 and the writer at $8516, ensuring subtitle sprites can be added **before** the native table copy, with the original cleanup intact and respecting both the 64-entry draw cap and 96-byte selector capacity.
4. Then implement a reversible game-data patch synchronized to **physical CD Track 28**. No further speculative edited-save-state tests.

The raw save states, screenshot/video and copyrighted CD assets are intentionally omitted from this **public** repository. Offline analysis tools and full comparison report are retained separately in a private test package.
