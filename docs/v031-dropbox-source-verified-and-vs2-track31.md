# v0.31: Dropbox source reacquired, VS1 release source pinned, VS2 evidence

Date: 2026-11-05. User authorized continuing Xak III development from the previously shared Dropbox folder **Temp-x3**. Read-only inventory of `/Temp-x3` and its **Xak III - The Eternal Recurrence (Japan) - Clean** and non-clean sibling folders completed using the connected Dropbox account. No source files, voice tracks or existing save states were changed.

## Authenticated private input identities

These hashes were computed on materialized original files in the private workspace. **Do not push disc/audio files to the public repository.**

| Source | Bytes | SHA-256 | Outcome |
|---|---:|---|---|
| Clean Japanese Track 02 (raw MODE1/2352) | 54,773,376 | `af04551ce4bf60d50397e99a6467c9e081b3091caa4eb95c67e7984578021733` | Exact match to `release/v030_vs1_manifest.json` input hash and `rebuild_english_track02.py` |
| v0.10 `Xak_III_English_Track02_SUB_TEST_v10.bin` | 54,773,376 | `64ef0a47b2beeefc12e6a113a056964e01b67e5b71d201449c699ed5f0bb9e46` | Exact match to v0.30 builder's pinned prerequisite and original v0.10 report |
| Clean Japanese CDDA Track 31 (VS2) | 14,911,680 | `acc2117becf4bdb6d687621529b0be6a9c90961f846e1ca86c86d3ccdbc6ebfa` | PCM 44,100 Hz, signed 16-bit stereo: **84.533333 s**, exactly **6,340 raw CDDA sectors** |
| User's supplied v0.30 `.xdelta` | 210,217 | `9a36d3ca5d2adf2f388c7afbb271b9c36169e2f649407a0be0744810dda6246e` | Matches release manifest and previous structural VCDIFF check |

**Release status:** The **input identity gate** for v0.30 is now verified from actual original media. Full decoding/EDC-ECC postpatch verification is a separate gate; xdelta3 decoder is not installed in the current environment, so **do not mark output reproducibility verified yet**.

## Track identity and scope

The clean folder has the complete 35-track split disc. The original, nonclean sibling has the build chain (v0.02, v0.03, v0.041, v0.05, v0.06, v0.10), intermediate IPS patches, CUEs and old saves. Files are accessed read-only; duplicate media should not be re-downloaded unnecessarily.

The public TSV on `grokbot/subtitle-pipeline` identifies **VS2** as physical CDDA Track **31**. Track 31 is 84.53 seconds long. In the existing script, `VS2-001` through `VS2-009` are **untimed in-game text-box excerpts**, explicitly annotated by the previous collaborator as “not heard in T31,” with a recommended remap away from the voiced cutscene. **Do not blindly time or inject those nine cues into Track 31.** The only two currently timed voiced entries are:

- `VS2-010`: 74.27–76.80 s, draft English “Um... hello? You two?”
- `VS2-011`: 76.86–79.70 s, draft English “Stay out of this, Ratok!”

These timings/text are from the inherited ASR/hand-review notes, *not a new validated listening pass*. The remaining **0–74 s** of Track 31 must be rechecked before declaring the voiced scene fully subtitled. Duration alone is not proof of voice activity: music/ambient effects can fill a long cutscene. A source-specific near-VS2 gameplay state is still required to verify that the bank81 and bank83 injected code, sprite palettes, and width hooks safely persist in that cinematic.

Next concrete steps: confirm v0.30 output via independent xdelta3 decode; obtain the VS2 audio scene map and near-VS2 save state; check text against original voices; port the engine with per-scene resource checks. Do not conflate script rows with actual voiced cue count or claim VS2 patch ready before runtime validation.
