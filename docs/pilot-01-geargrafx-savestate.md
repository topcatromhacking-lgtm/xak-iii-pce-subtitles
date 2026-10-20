# Pilot 01: Geargrafx save-state inspection

**Date:** 2026-10-20. Status: source save-state parsed successfully, subtitle insertion still unimplemented.

An independently supplied Geargrafx **1.8.4** save-state file was inspected **read-only**, without modifying the original or publishing its copyrighted screenshot, memory, or full binary. Source format was cross-checked against the [Geargrafx state serializer](https://github.com/drhelius/Geargrafx/blob/main/src/geargrafx_core.cpp), [memory serializer](https://github.com/drhelius/Geargrafx/blob/main/src/memory.cpp), and [CD audio serializer](https://github.com/drhelius/Geargrafx/blob/main/src/cdrom_audio.cpp).

## Verified state metadata

| Field | Value |
| --- | --- |
| Format magic | `0x82190619` |
| Format version | `44` |
| Emulator | Geargrafx `1.8.4` |
| Total bytes | `749,238` |
| Source SHA-256 | `8c8f89e94bb7b89c4d76183f562ba7e2742eb385759eda840b1f976fe50183ba` |
| Disc | English v1.0 split-track CUE |
| Disc CRC ID | `EDFD65CB` (agrees with state header and payload) |
| Main WRAM | 32 KiB |
| CD RAM | 64 KiB |
| Additional card RAM | 192 KiB |
| Memory page registers | FF F8 80 81 82 83 84 00 |
| Embedded screenshot | RGBA8888, 256x240, no compression |

The screenshot depicts a **military camp with soldiers and tents**, not the royal-audience cinematic. This appears to be a useful earlier checkpoint, but the save alone does not prove that advancing immediately triggers the cutscene.

The 192 KiB card memory contains multiple speaker-prefixed English dialogue strings including **Ratok, Beluga and Pixie**. Representative portions match the reconstructed English data track byte-for-byte, confirming that translated script data is loaded in memory. This is **not evidence that those particular dialogue strings are spoken in the cinematic**.

## Saved CD-DA playback

At the saved instant Geargrafx's CD audio serializer records:

| Field | Value |
| --- | --- |
| State | Playing (enum `0`) |
| Start LBA | 55,093 |
| Stop LBA | 61,725 |
| Current LBA | **56,407** |
| Seek/start LBA | 55,093 |
| Stop event | Loop (enum `1`) |
| Sector sample offset | 138 |
| Pending seek/playback-delay cycles | 0 / 0 |

These values are consistent with an active looping CD-DA segment. It **may be ambient or background music**: there is no basis yet for calling it the cutscene voice track. Mapping an LBA to a physical audio track requires the actual full disc TOC or all 35 track lengths; the split-track CUE alone does not contain those lengths.

## Engineering implications and next checkpoint

1. Retain this original save as a safe rollback.
2. In Geargrafx, load the save and approach the royal-audience event.
3. Save a **second state immediately before the scene transition** and optionally another state during the first Japanese spoken line.
4. Log CD-ROM/SCSI and ADPCM events across scene entry. Compare **start/stop/current LBA before and during speech** to distinguish music from voiced dialogue.
5. Once audio triggers are identified, trace active CPU/VDC instructions during cinematic frame updates. Only then attempt the first timestamped English subtitle.

No runtime cutscene hook, font reuse, buffer location, or subtitle patch has yet been verified. Do not patch one of the previously recorded static BIOS-call signatures without confirming its execution.

The read-only Python v44 save-state inspection script has been tested locally with both a synthetic fixture and the provided state; the *state and derived screenshot are not published here*.
