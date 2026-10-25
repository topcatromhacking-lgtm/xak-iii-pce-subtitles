"""Xak III v0.14 regressions. Synthetic tests use no user game files."""
import hashlib,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_xak_iii_v14_letterbox_geometry as m

def fixture():
 b=bytearray(m.SIZE)
 struct.pack_into('<III',b,len(b)-200,0x82190619,44,len(b))
 struct.pack_into('<H',b,m.VDC_REGS+9*2,0x50)
 struct.pack_into('<H',b,m.VDC_REGS+19*2,0x0C00)
 b[m.cpu(m.CALLSITE_CPU):m.cpu(m.CALLSITE_CPU)+5]=bytes.fromhex('20 df 76 ea ea')
 b[m.cpu(m.HELPER_CPU):m.cpu(m.HELPER_CPU)+10]=m.HELPER
 b[m.cpu(m.FONT_TABLE_CPU):m.cpu(m.FONT_TABLE_CPU)+8]=m.Y_TABLE
 b[m.cpu(m.X_TABLE_CPU):m.cpu(m.X_TABLE_CPU)+4]=m.BASE_X
 b[m.cpu(m.FONT_REF_CPU):m.cpu(m.FONT_REF_CPU)+4]=bytes.fromhex('76 70 72 74')
 for j,p in enumerate((0x76,0x70,0x72,0x74)):
  struct.pack_into('<4H',b,m.VDC_SAT+8*j,248 if j<2 else 268,144+16*(j%2),p,0x008f)
 return bytes(b)

class Test(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.src=fixture()
 def test_baseline(self):self.assertTrue(m.validate(self.src))
 def test_four_geometry_variants(self):
  s=m.make_variants(self.src)
  self.assertEqual([r[0] for r in s],[2,3,4,5])
  self.assertEqual([r[2]['shift_x'] for r in s],[0,-48,-64,-80])
 def test_delta_64(self):
  s=m.make_variants(self.src)[2]
  self.assertEqual(s[1][m.cpu(m.X_TABLE_CPU):m.cpu(m.X_TABLE_CPU)+4],bytes([80,96,80,96]))
 def test_v11_preserved(self):
  for _,data,_ in m.make_variants(self.src):
   self.assertEqual(data[m.cpu(m.HELPER_CPU):m.cpu(m.HELPER_CPU)+10],m.HELPER)
   self.assertEqual(data[m.cpu(m.FONT_TABLE_CPU):m.cpu(m.FONT_TABLE_CPU)+8],m.Y_TABLE)
 def test_only_four_bytes(self):
  for _,data,report in m.make_variants(self.src):
   self.assertEqual(report['changed_bytes'],0 if report['shift_x']==0 else 4)
   self.assertEqual(self.src[-200:],data[-200:])
 def test_native_sprite_isolation(self):
  _,_,r=m.make_variants(self.src,'sprite-isolation')[3]
  self.assertEqual(r['mask_type'],'touching')
 def test_cue(self):
  cue='FILE "'+m.V11_TRACK+'" BINARY\n'+'\n'.join(f'TRACK {i:02d} '+('MODE1/2352' if i==2 else 'AUDIO') for i in range(1,36))+'\n'
  self.assertEqual(m.make_cue(cue),cue)
 def test_bad_cue(self):
  with self.assertRaises(ValueError):m.make_cue('FILE "'+m.V11_TRACK+'" BINARY\nTRACK 28 MODE1/2352')
 def test_bad_helper(self):
  s=bytearray(self.src);s[m.cpu(m.HELPER_CPU)+6]=0x10
  with self.assertRaises(ValueError):m.validate(bytes(s))
 def test_wrong_x_table(self):
  s=bytearray(self.src);s[m.cpu(m.X_TABLE_CPU)]=0
  with self.assertRaises(ValueError):m.validate(bytes(s))
 def test_oversized_shift(self):
  with self.assertRaises(ValueError):m.shift_coordinates(self.src,-100)
 def test_sat_cull_does_not_touch_subtitle(self):
  b=bytearray(self.src)
  v=m.VDC_SAT;vram=m.VRAM+0x1800
  struct.pack_into('<4H',b,v,260,90,0x110,0x0085)
  struct.pack_into('<4H',b,vram,260,90,0x110,0x0085)
  struct.pack_into('<4H',b,v+8,248,144,0x76,0x008F)
  struct.pack_into('<4H',b,vram+8,248,144,0x76,0x008F)
  mask=m.native_masks(b,'outside')
  self.assertIn(0,mask)
  self.assertNotIn(1,mask)
  self.assertEqual(struct.unpack_from('<H',b,v+8)[0],248)
 def test_reject_short_state(self):
  with self.assertRaises(ValueError):m.validate(self.src[:-5])
 def test_sat_metadata(self):
  self.assertEqual(len([x for x in m.sat_info(self.src) if x['is_subtitle']]),4)
 def test_cue_wrong_track(self):
  with self.assertRaises(ValueError):m.make_cue('FILE "unknown.bin" BINARY\n'+'\n'.join(f'TRACK {i:02d} AUDIO' for i in range(1,36)))

if __name__=='__main__':unittest.main()
