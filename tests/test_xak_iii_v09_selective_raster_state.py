"""Synthetic-only v0.9 test cases, no copyrighted game content."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_xak_iii_v09_selective_raster_state as m

def fixture():
    b=bytearray(m.SIZE)
    struct.pack_into('<III',b,len(b)-200,0x82190619,44,len(b))
    b[13:21]=bytes.fromhex('FF F8 80 81 82 83 84 00')
    b[m.ram(m.CALLSITE-3):m.ram(m.CALLSITE-3)+len(m.ORIGINAL)]=m.ORIGINAL
    b[21+0x33D]=0xCC
    struct.pack_into('<H',b,0x48C67+65536+4+5*2,0xCC)
    return bytes(b)

class TestSelectiveRaster(unittest.TestCase):
    def test_hook_replacement(self):
        src=fixture();dst,report=m.build_state(src,pin=False)
        self.assertEqual(dst[m.ram(m.CALLSITE):m.ram(m.CALLSITE)+5],m.REDIRECT)
        self.assertEqual(dst[m.ram(m.CAVE):m.ram(m.CAVE)+10],m.HELPER)
        self.assertEqual(report['changed_bytes'],15)
        self.assertEqual(src[-200:],dst[-200:])
    def test_mismatch(self):
        with self.assertRaises(ValueError):m.build_state(fixture())
    def test_protect_code(self):
        b=bytearray(fixture());b[m.ram(m.CALLSITE)]=0
        with self.assertRaises(ValueError):m.build_state(bytes(b),pin=False)
    def test_protect_cave(self):
        b=bytearray(fixture());b[m.ram(m.CAVE)]=1
        with self.assertRaises(ValueError):m.build_state(bytes(b),pin=False)
    def test_protect_cr(self):
        b=bytearray(fixture());b[21+0x33D]=0
        with self.assertRaises(ValueError):m.build_state(bytes(b),pin=False)
    def test_truth_table(self):
        for table,expected in [(0x80,0xCC),(0x00,0x0C),(0xC0,0xCC),(0x40,0x4C)]:
            a=(0xCC&0x3F)|table
            if a&0x80:a|=0x40
            self.assertEqual(a,expected)
    def test_branch_ends_at_rts(self):
        self.assertEqual(m.HELPER[5:7],bytes.fromhex('10 02'))
        self.assertEqual(m.HELPER[9],0x60)
    def test_cue_validation(self):
        cue='FILE "'+m.TRACK02+'" BINARY\n'+'\n'.join('TRACK %02d %s'%(i,'MODE1/2352' if i==2 else 'AUDIO') for i in range(1,36))
        self.assertEqual(m.cue_validate(cue),cue)
    def test_bad_state_size(self):
        with self.assertRaises(ValueError):m.build_state(b'bad',pin=False)

if __name__=='__main__':unittest.main()
