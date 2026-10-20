"""Synthetic native SAT reproduction; does not require game binaries."""
import struct
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_native_sprite_feed_v1 import (simulate_sat_copy, expected_sat,
    sprite_entries, wram_address, BYTE_FIELDS, SELECTOR_ADDR, COUNT_ADDR)

class TestSAT(unittest.TestCase):
    def test_sprites_then_zero_fill(self):
        data = bytearray(0x8000+21)
        data[wram_address(COUNT_ADDR)] = 8
        for index, entry in enumerate(sprite_entries()):
            data[wram_address(SELECTOR_ADDR+index)] = index
            for base, value in zip(BYTE_FIELDS, struct.pack("<4H", *entry)):
                data[wram_address(base+index)] = value
        self.assertEqual(simulate_sat_copy(data), expected_sat()+bytes(448))
        self.assertEqual(expected_sat()[:8],struct.pack("<4H",0x10F,0x60,0x3F0,0x8F))
    def test_zero_count(self):
        self.assertEqual(simulate_sat_copy(bytearray(0x8000+21)),bytes(512))
    def test_wram_bounds(self):
        for x in (0x1FFF,0x4000):
            with self.assertRaises(ValueError):
                wram_address(x)

if __name__ == "__main__":
    unittest.main()
