"""Synthetic-only tests for compare_xak_subtitle_stage_v07.py; no game bytes."""
import struct
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import compare_xak_subtitle_stage_v07 as inspector

def fake_state():
    b=bytearray(inspector.SIZE)
    tail=len(b)-inspector.HEADER
    struct.pack_into('<III',b,tail,0x82190619,44,len(b))
    struct.pack_into('<IHH',b,tail+156,256*240*4,256,240)
    struct.pack_into('<I',b,13+8+32768,65536)
    for r,v in [(5,0xCC),(6,0x40),(9,0x50),(11,0x41F),(19,0xC00)]:
        struct.pack_into('<H',b,inspector.REGS+2*r,v)
    struct.pack_into('<H',b,inspector.LATCHED_CR,0xCC)
    struct.pack_into('<H',b,inspector.VCE+11+511*2,0x1FF)
    for i,(x,sat2) in enumerate(zip((64,80,96,112),inspector.SAT2)):
        struct.pack_into('<4H',b,inspector.SAT+8*i,192,x,sat2,0x8F)
    for p in inspector.PATTERNS:
        b[inspector.VDC1+p*128+10]=p
    return b

class Tests(unittest.TestCase):
    def test_read(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'s.state5';p.write_bytes(fake_state())
            a=inspector.read(p)
        self.assertEqual(a['vdc1']['CR'],'00CC')
        self.assertEqual(a['vdc1']['latched_CR_at_save_instant'],'00CC')
        self.assertEqual(a['vdc1']['subtitle_sat_indices'],[[0],[1],[2],[3]])
        self.assertEqual(a['vce_sprite_palette_15_color_15'],'01FF')
    def test_compare(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.state5';q=Path(d)/'b.state3'
            data=fake_state();p.write_bytes(data)
            data[inspector.SAT:inspector.SAT+8]=b'\0'*8;q.write_bytes(data)
            z=inspector.compare(inspector.read(p),inspector.read(q))
        self.assertTrue(z['same_saved_CR'])
        self.assertNotEqual(z['early']['vdc1']['subtitle_sat_indices'][0],
                            z['later']['vdc1']['subtitle_sat_indices'][0])
    def test_wrong_size(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';p.write_bytes(b'bad')
            with self.assertRaises(ValueError):inspector.read(p)
    def test_wrong_magic(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x';b=fake_state();b[-inspector.HEADER]=0;p.write_bytes(b)
            with self.assertRaises(ValueError):inspector.read(p)

if __name__=='__main__':
    unittest.main()
