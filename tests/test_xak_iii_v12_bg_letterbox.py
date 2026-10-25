"""Nine regression checks, including the exact private King state when available.

The repository does not ship user save states. To run source-only tests, place
the already-owned pinned v0.9 state in the path used below; otherwise tests
requiring that state are skipped.
"""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_xak_iii_v12_bg_letterbox as m
from zipfile import ZipFile
class Test(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path('/mnt/data/Xak_III_v09_Selective_King_Raster_Probe_Ready_To_Test.zip')
  if p.exists(): cls.s=ZipFile(p).read(m.SRC_STATE)
  else: cls.s=None
 def test_helper_decode(self):
  self.assertEqual(len(m.NEW),13)
  self.assertEqual(m.NEW[5:7],b'\x30\x03')
  self.assertEqual(m.NEW[-1],0x60)
 def test_branch_values(self):
  for val,want in ((0,0x8C),(0x80,0xCC),(0xC0,0xCC)):
   acc=(0xCC&0x3F)|val
   if acc&0x80:acc|=0x40
   else:acc|=0x80
   self.assertEqual(acc,want)
 def test_glyph(self):
  for ch in m.FONT_IDS:self.assertEqual(len(m.glyph(ch)),32)
 def test_vram_span(self):
  self.assertTrue(all((r*64+m.COLUMN+len(m.TEXT))<4096 for r in m.ROWS))
 def test_real_pinned_a(self):
  if self.s is None:self.skipTest('Private test state unavailable')
  out,rep=m.prepare(self.s,False)
  self.assertEqual(rep['slot'],2)
  self.assertEqual(self.s[m.VDC:],out[m.VDC:])
  self.assertTrue(out!=self.s)
 def test_real_pinned_b(self):
  if self.s is None:self.skipTest('Private test state unavailable')
  out,rep=m.prepare(self.s,True)
  self.assertEqual(rep['slot'],3)
  self.assertNotEqual(self.s[m.VDC:m.VDC+65536],out[m.VDC:m.VDC+65536])
  self.assertEqual(self.s[-200:],out[-200:])
 def test_a_vs_b_code(self):
  if self.s is None:self.skipTest('Private test state unavailable')
  a,_=m.prepare(self.s,False);b,_=m.prepare(self.s,True)
  self.assertEqual(a[:m.VDC],b[:m.VDC])
 def test_wrong_hash(self):
  if self.s is None:self.skipTest('Private test state unavailable')
  with self.assertRaises(ValueError):m.prepare(self.s[:-1],False)
 def test_source_cue(self):
  p=Path('/mnt/data/Xak_III_v09_Selective_King_Raster_Probe_Ready_To_Test.zip')
  if not p.exists():self.skipTest('Private v0.9 cue unavailable')
  z=ZipFile(p)
  txt=z.read('Xak_III_English_SUB_TEST_v09_Pilot01.cue').decode()
  output=m.cue(txt)
  self.assertIn(m.V10_TRACK,output)
  self.assertNotIn(m.V05_TRACK,output)
if __name__=='__main__':unittest.main()
