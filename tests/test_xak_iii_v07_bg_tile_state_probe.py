"""Synthetic-only BG tile state test; does not commit the user's state data."""
import struct,tempfile,unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_xak_iii_v07_bg_tile_state_probe as m

class Test(unittest.TestCase):
 def synth(self):
  b=bytearray(m.SIZE)
  struct.pack_into('<III',b,len(b)-m.HEADER,0x82190619,44,len(b))
  for reg,val in [(5,0xcc),(9,m.MWR),(11,0x041f)]:struct.pack_into('<H',b,m.VDC1+65536+4+2*reg,val)
  struct.pack_into('<H',b,m.VCE+11+2*(7*16+15),0x01ff)
  return bytes(b)
 def test_positive(self):
  src=self.synth();out,rep=m.patch_state(src,require_pinned=False)
  self.assertEqual(src[:m.VDC1],out[:m.VDC1])
  self.assertEqual(src[m.VDC1+65536:],out[m.VDC1+65536:])
  self.assertEqual(src[-m.HEADER:],out[-m.HEADER:])
  for row in m.ROWS:
   for j,ch in enumerate(m.TEXT):
    if ch!=' ':
     actual=struct.unpack_from('<H',out,m.VDC1+2*(row*64+m.COL+j))[0]
     self.assertEqual(actual,0x7000|m.FONT_IDS[ch])
  self.assertGreater(rep['changed_bytes'],100)
 def test_wrong_hash(self):
  with self.assertRaises(ValueError):m.verify(self.synth())
 def test_tile_referenced(self):
  b=bytearray(self.synth());struct.pack_into('<H',b,m.VDC1+100,2025)
  with self.assertRaises(ValueError):m.patch_state(bytes(b),require_pinned=False)
 def test_palette_conflict(self):
  b=bytearray(self.synth());struct.pack_into('<H',b,m.VCE+11+2*(7*16+15),0)
  with self.assertRaises(ValueError):m.patch_state(bytes(b),require_pinned=False)
 def test_vdc_conflict(self):
  b=bytearray(self.synth());struct.pack_into('<H',b,m.VDC1+65536+4+2*5,0)
  with self.assertRaises(ValueError):m.patch_state(bytes(b),require_pinned=False)
 def test_font_plane_white(self):
  words=m.tile_words('S')
  self.assertEqual(len(words),16)
  self.assertEqual(words[:8],words[8:])

if __name__=='__main__':unittest.main()
