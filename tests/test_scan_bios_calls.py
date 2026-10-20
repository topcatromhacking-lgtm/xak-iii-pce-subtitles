"""Synthetic test sectors only, no game assets."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from scan_bios_calls import user_data, find_calls, SECTOR


def sector(data):
    return bytes([0] + [255] * 10 + [0, 1, 2, 3, 1]) + data.ljust(2048, b"\x00") + bytes(288)


class CDScanTest(unittest.TestCase):
    def test_locations(self):
        raw = sector(b"ignored") + sector(b"abcd\x20\x12\xe0zz\x20\x33\xe0")
        decoded = user_data(raw, pregap=1)
        result = find_calls(decoded, pregap=1)
        self.assertEqual(result["CD_PLAY"][0]["raw_track_offset"], SECTOR + 16 + 4)
        self.assertEqual(result["AD_TRANS"][0]["user_data_sector_offset"], 9)
        self.assertFalse(result["AD_PLAY"])

    def test_bad_raw_size(self):
        with self.assertRaises(ValueError):
            user_data(b"123", pregap=0)

    def test_bad_mode1(self):
        with self.assertRaises(ValueError):
            user_data(b"\x00" * SECTOR, pregap=0)


if __name__ == "__main__":
    unittest.main()
