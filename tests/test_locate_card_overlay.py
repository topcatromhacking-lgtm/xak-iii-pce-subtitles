"""Synthetic tests for the CD-card overlay locator. No game files are needed."""
import sys
import random
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from locate_card_overlay import track_as_iso, locate


class TestOverlayLocation(unittest.TestCase):
    def test_exact_and_partial_match(self):
        rng = random.Random(12345)
        raw = bytearray()
        for i in range(12):
            payload = bytes(rng.randrange(256) for _ in range(2048))
            # Raw MODE1 sector: 12-byte sync, 3-byte MSF, mode, data, EDC/ECC.
            raw.extend(bytes([0] + [255] * 10 + [0, i, i, i, 1])
                       + payload + bytes(288))
        iso = track_as_iso(bytes(raw), pregap=1)
        original = iso[2 * 2048:5 * 2048]
        result = locate(original, iso, pregap=1)[0]
        self.assertEqual(result['raw_track_sector'], 3)
        self.assertEqual(result['matching_prefix_bytes'], len(original))
        self.assertTrue(result['full_card_ram_match'])
        modified = bytearray(original)
        modified[1337] ^= 0x80
        partial = locate(bytes(modified), iso, pregap=1)[0]
        self.assertEqual(partial['matching_prefix_bytes'], 1337)
        self.assertFalse(partial['full_card_ram_match'])


if __name__ == '__main__':
    unittest.main()
