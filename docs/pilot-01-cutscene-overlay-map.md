# Pilot 01: first voiced scene overlay located in Track 02

**Verified 2026-10-20, offline binary comparison only.** The user's Geargrafx 1.8.4 v44 save state inside the King Wavis royal-audience cutscene contains an entire **196,608-byte (192 KiB)** CD card-RAM region identical to a contiguous sequence of **96 indexed 2048-byte user-data sectors** from the reconstructed English game data track.

| Field | Confirmed value |
|---|---|
| Raw Track 02 start sector (2352-byte sector numbering) | **766** |
| Indexed sector (after 225-sector pregap) | **541** |
| Raw Track 02 byte offset | **0x1B7DB0** |
| Indexed ISO user-data offset | **0x10E800** |
| Number of indexed sectors | **96** |
| Card RAM bytes | **196,608** |
| RAM and disc-range SHA-256, identical | `e8d9b2e8ae5044824999e3aa84ee9d41647751b4d116b539aa8b8b5452782867` |
| Bytes different between Japanese and existing English source in these 96 sectors | **0** |

The state serializer shows card RAM begins at state byte offset 0x1801D. Its 196,608 bytes exactly match the disc source range (when raw sector framing/EDC/ECC is omitted). The exact match holds across **all 96 sectors**, not just one short fingerprint.

### Control comparison: camp checkpoint

The earlier camp state points to a different Track 02 region at raw sector 2942 / indexed sector 2717 / ISO offset 0x54E800. Its first 25,088 card-RAM bytes match the disc copy, with differences thereafter. That region contains translated normal-game dialogue. By contrast, the audience card RAM is a complete, untouched disc image of the cinematic memory bank and has almost no readable dialogue strings.

### Implications for the subtitle project

- The existing English patch **does not modify the audience's 96-sector data region**, so this is a good isolated target for examination.
- The two loaded card-RAM regions are demonstrably different. This supports, but does not prove, a scene-specific overlay mechanism.
- It **does not prove all 96 sectors are code**: the region can include graphics, tables and resources. A CD-to-RAM copy identifies provenance, not executed instructions or a safe patch offset.
- Inspect loaded bytes, CPU code entry and VDC writes with Geargrafx before adding any subtitle routine. Preserve the original Japanese CD Track 28 (confirmed in [audio-track analysis](pilot-01-track28-confirmed.md)).
- Disc rebuilding must update MODE1 sector integrity fields as needed; never overwrite arbitrary compressed or packed data, or publish source BINs.

Research performed against user-provided files retained privately. No copyrighted ROM image, memory dump, game data or screenshot has been included in this public repository.
