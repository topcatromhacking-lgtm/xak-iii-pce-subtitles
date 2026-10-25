"""Synthetic-only v0.15 tests. No user game data or saves are published."""
import unittest,sys,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_xak_iii_v15_native_sat_isolation as m

def fixture():
 b=bytearray(m.STATE_LEN)
 struct.pack_into('<III',b,m.STATE_LEN-200,0x82190619,44,m.STATE_LEN)
 b[m.cpu(0x65AA):m.cpu(0x65AA)+5]=bytes.fromhex('20 DF 76 EA EA')
 b[m.cpu(0x76DF):m.cpu(0x76DF)+10]=m.EXPECTED_HELPER
 b[m.cpu(0x9CA2):m.cpu(0x9CA2)+4]=m.EXPECTED_X
 b[m.cpu(0x9CAA):m.cpu(0x9CAA)+4]=m.EXPECTED_FONT
 struct.pack_into('<H',b,m.VDC_REGS+2*19,0x0C00)
 sprites=[(0,30,0x100,0x8f),(1,150,0x110,0x108f),(2,190,0x112,0x8f),
          (3,184,0x76,0x8f),(4,204,0x70,0x8f)]
 for i,y,pat,flags in sprites:
  for off in (m.VDC_SAT+8*i,m.VDC_VRAM+0x1800+8*i):
   struct.pack_into('<4H',b,off,y+64,144,pat,flags)
 return bytes(b)

class TestNativeSAT(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.source=fixture()
 def test_parse_and_bounds(self):
  self.assertEqual(len(m.sat(self.source)),5)
  self.assertEqual([x['index'] for x in m.sat(self.source) if x['subtitle']],[3,4])
 def test_four_variants(self):
  o,r=m.build_states(self.source)
  self.assertEqual(sorted(o),[2,3,4,5])
  self.assertEqual(o[2],self.source)
 def test_fully_outside(self):
  _,r=m.build_states(self.source)
  self.assertEqual(r['variants']['3']['masked_native_indices'],[0,2])
 def test_touching_both(self):
  _,r=m.build_states(self.source)
  self.assertEqual(r['variants']['4']['masked_native_indices'],[0,1,2])
 def test_touching_bottom(self):
  _,r=m.build_states(self.source)
  self.assertEqual(r['variants']['5']['masked_native_indices'],[1,2])
 def test_subtitle_not_modified(self):
  states,_=m.build_states(self.source)
  for b in states.values():
   for i in (3,4):
    off=m.VDC_SAT+8*i
    self.assertEqual(b[off:off+8],self.source[off:off+8])
 def test_native_program_unchanged(self):
  states,_=m.build_states(self.source)
  for b in states.values():self.assertEqual(b[:m.VDC_VRAM],self.source[:m.VDC_VRAM])
 def test_reject_wrong_slot4(self):
  b=bytearray(self.source);b[m.cpu(0x9CA2)]=0x90
  with self.assertRaises(ValueError):m.build_states(bytes(b))
 def test_reject_empty_native(self):
  b=bytearray(self.source)
  for i in (0,1,2):
   for off in (m.VDC_SAT+8*i,m.VDC_VRAM+0x1800+8*i):b[off:off+8]=b'\0'*8
  with self.assertRaisesRegex(ValueError,'No native SAT sprites'):m.build_states(bytes(b))
 def test_reject_wrong_satb(self):
  b=bytearray(self.source);struct.pack_into('<H',b,m.VDC_REGS+2*19,0)
  with self.assertRaises(ValueError):m.build_states(bytes(b))
 def test_cue(self):
  cue='FILE "'+m.TRACK+'" BINARY\n'+'\n'.join(
   f'TRACK {n:02d} '+('MODE1/2352' if n==2 else 'AUDIO') for n in range(1,36))+'\n'
  self.assertEqual(m.make_cue(cue),cue)
 def test_reject_bad_cue(self):
  with self.assertRaises(ValueError):m.make_cue('not a cue')

if __name__=='__main__':unittest.main()
