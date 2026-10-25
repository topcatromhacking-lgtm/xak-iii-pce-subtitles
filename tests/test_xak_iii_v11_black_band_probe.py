"""Nine synthetic-only regressions for v0.11 sprite black-band diagnostic."""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_xak_iii_v11_black_band_probe as m

def fixture():
    b=bytearray(m.STATE_SIZE)
    struct.pack_into('<III',b,len(b)-200,0x82190619,44,len(b))
    b[m.offset(m.HELPER_CPU):m.offset(m.HELPER_CPU)+10]=m.OLD_HELPER
    b[m.offset(m.SAT_TABLE_CPU):m.offset(m.SAT_TABLE_CPU)+12]=m.OLD_TABLE
    b[m.offset(0x9CAA):m.offset(0x9CAE)]=bytes.fromhex('76 70 72 74')
    b[m.offset(0x65AA):m.offset(0x65AF)]=bytes.fromhex('20 DF 76 EA EA')
    b[m.offset(0x9C99)]=0
    return bytes(b)

class TestBlackBand(unittest.TestCase):
    def test_exact_change(self):
        s=fixture();patched,r=m.patch_state(s,require_pinned=False)
        self.assertEqual(r['changed_bytes'],12)
        self.assertEqual(sum(a!=b for a,b in zip(s,patched)),12)
        self.assertEqual(patched[:m.CDRAM],s[:m.CDRAM])
        self.assertEqual(patched[m.CDRAM+65536:],s[m.CDRAM+65536:])
    def test_helper(self):
        out,_=m.patch_state(fixture(),require_pinned=False)
        self.assertEqual(out[m.offset(0x76E4):m.offset(0x76E6)],b'\xea\xea')
    def test_y_and_x(self):
        out,_=m.patch_state(fixture(),require_pinned=False)
        self.assertEqual(out[m.offset(0x9C9A):m.offset(0x9CA6)],m.NEW_TABLE)
        ys=[m.NEW_TABLE[i]+(m.NEW_TABLE[4+i]<<8)-64 for i in range(4)]
        self.assertEqual(ys,[184,184,204,204])
        self.assertTrue(all(y+16<=224 for y in ys))
    def test_reject_wrong_pinned_source(self):
        with self.assertRaisesRegex(ValueError,'not exact'):
            m.patch_state(fixture())
    def test_reject_wrong_helper(self):
        s=bytearray(fixture());s[m.offset(m.HELPER_CPU)]=0
        with self.assertRaisesRegex(ValueError,'helper'):
            m.patch_state(bytes(s),require_pinned=False)
    def test_reject_corrupt_font_table(self):
        s=bytearray(fixture());s[m.offset(0x9CAA)]=0
        with self.assertRaisesRegex(ValueError,'glyph refs'):
            m.patch_state(bytes(s),require_pinned=False)
    def test_reject_invalid_state_size(self):
        with self.assertRaises(ValueError):m.patch_state(fixture()[:-1],require_pinned=False)
    def test_cue_stable(self):
        cue='FILE "'+m.V05_TRACK+'" BINARY\n'+ '\n'.join('TRACK %02d %s'%(n,'MODE1/2352' if n==2 else 'AUDIO') for n in range(1,36))+'\n'
        out=m.make_cue(cue)
        self.assertEqual(out.count('TRACK '),35)
        self.assertIn(m.V10_TRACK,out)
        self.assertNotIn(m.V05_TRACK,out)
        with self.assertRaises(ValueError):m.make_cue(cue.replace('TRACK 28 AUDIO','TRACK 28 MODE1/2352'))
    def test_cpu_range(self):
        with self.assertRaises(ValueError):m.offset(0x40000)

if __name__=='__main__':unittest.main()
