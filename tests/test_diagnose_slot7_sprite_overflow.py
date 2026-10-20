"""Synthetic Geargrafx v44 data only, never contains game assets."""
import struct
import unittest
from diagnose_slot7_sprite_overflow import (
    inspect, wram, CPU_OFFSET, CD_RAM_OFFSET, WRAM_OFFSET,
)

def fixture(count=8):
    b=bytearray(749238)
    b[0]=1
    b[13:21]=bytes.fromhex("FF F8 80 81 82 83 84 00")
    struct.pack_into("<H5B",b,CPU_OFFSET,0x8516,0,23,34,0xFD,0x80)
    struct.pack_into("<III",b,len(b)-200,0x82190619,44,len(b))
    audio=len(b)-200-256*240*4-65647
    struct.pack_into("<10Ihh",b,audio,0,0,164129,178493,164165,164129,0,2,0,0,0,0)
    b[CD_RAM_OFFSET+0x44F0:CD_RAM_OFFSET+0x44FB]=bytes.fromhex(
        "AD 44 34 42 99 A4 2E 42 EE 44 34")
    b[CD_RAM_OFFSET+0x4EE5:CD_RAM_OFFSET+0x4EE8]=bytes.fromhex("20 16 85")
    b[CD_RAM_OFFSET+0x4593:CD_RAM_OFFSET+0x4596]=b"\xEA"*3
    b[WRAM_OFFSET+0x3444-0x2000]=count
    return b

class StateTests(unittest.TestCase):
    def test_safe_count(self):
        r=inspect(fixture())
        self.assertEqual(r["sprite_count"],8)
        self.assertEqual(r["selector_overrun_entries"],0)
        self.assertEqual(r["pc"],"$8516")
        self.assertFalse(r["normal_counter_cleanup_enabled"])

    def test_overflow(self):
        r=inspect(fixture(247))
        self.assertEqual(r["selector_overrun_entries"],151)
        self.assertEqual(r["next_selector_write"],"$2F9B")
        self.assertEqual(r["cdda_track28_seconds"],0.48)

    def test_original_cleanup_opcode(self):
        b=fixture(0)
        b[CD_RAM_OFFSET+0x4593:CD_RAM_OFFSET+0x4596]=bytes.fromhex("9C 44 34")
        self.assertTrue(inspect(b)["normal_counter_cleanup_enabled"])

    def test_unknown_code_rejected(self):
        b=fixture()
        b[CD_RAM_OFFSET+0x44F0]=0
        with self.assertRaisesRegex(ValueError,"accumulator"):
            inspect(b)

    def test_Wram_bounds(self):
        with self.assertRaises(ValueError):wram(fixture(),0x1FFF)
        with self.assertRaises(ValueError):wram(fixture(),0x4000)

if __name__=="__main__":
    unittest.main()
