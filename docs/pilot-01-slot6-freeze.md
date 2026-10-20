# Pilot 01: slot 6 freezes, no subtitle visible

**Runtime feedback received 2026-10-20. Status: failed test.**

The user loaded the experimental slot-6 Geargrafx state and reported that the King Wavis cinematic **froze on a close-up of Latok**. Their screenshot shows the cinematic portrait occupying the central image area, with the lower black region empty: the requested `ENGLISH SUBTITLE` marker **did not appear**. The test is not evidence of a working subtitle renderer.

## Changes responsible for the risk

Slot 6 was deliberately not a normal gameplay-safe snapshot. It changed the saved CPU PC from `$8590` to `$8516` (restart in the middle of a time-sensitive VDC sprite update) and replaced a native cleanup instruction at `$8593`:

- Original: `9C 44 34` = `STZ $3444` (clears the transient active sprite count).
- Experimental: `EA EA EA` (three NOPs).

The static instruction-level test verified that the rewritten routine *could produce* a 512-byte sprite table, but it **did not emulate the full CPU/VDC scheduling, interrupts, caller frame state, return stack, or game-loop behavior**. Rewinding execution into a VDC update routine and inhibiting its cleanup may disrupt gameplay. This is a plausible explanation for the freeze, **not an established cause without a real execution trace**.

Offline reinspection of the shipped slot-6 state confirms the four-byte modification, its hash `65cd995a37490f80208a52bcdee1c381927e3066aded4534ff4a32e395087c76`, saved PC `$8516`, and replacement NOP instruction bytes. The user should **not** use that state for normal play or save over the original.

## Next requirement: observe, don't speculate

**Stop producing further patched-state variants** until the live program state is known.

Preferred live diagnosis in Geargrafx:
1. Load the original English Xak III split-track disc and the experimental **slot 6** only for debugging.
2. Once the screen freezes, open Geargrafx's debugger and inspect the **HuC6280 CPU PC, registers, and disassembly**. Capture a screenshot (or export a short CPU/VDC trace if already familiar).
3. Determine whether audio continues while the image is frozen; this distinguishes a stalled renderer from a full game-loop stall.
4. If it is possible to save at the frozen point, save a *new* slot without overwriting slots 1, 4, 5 or 6, and keep the file local for private comparison.

The original slot 1 and clean disc remain approved rollback. For the actual subtitle implementation, hook a routine on the frame boundary with normal lifecycle management and a track-28-driven cue timer; do **not** bypass native sprite-list cleanup permanently. All copyrighted game/audio and user save-state files remain uncommitted.

Prior diagnostic context: [slot 5 mid-loop failure](pilot-01-slot5-reentry-diagnosis.md).
