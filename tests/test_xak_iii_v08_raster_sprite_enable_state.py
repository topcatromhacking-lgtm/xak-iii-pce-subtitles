"""Synthetic regression tests for the v0.8 King opening raster visibility probe."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import build_xak_iii_v08_raster_sprite_enable_state as mod

def sample():
    b=bytearray(mod.STATE_SIZE)
    struct.pack_into("<III",b,len(b)-200,0x82190619,44,len(b))
    b[13:21]=bytes.fromhex("FF F8 80 81 82 83 84 00")
    b[mod.OFF-4:mod.OFF-4+len(mod.INSTRUCTION)]=mod.INSTRUCTION
    b[21+(0x233D-0x2000)]=0xCC
    struct.pack_into("<H",b,0x48C67+65536+4+5*2,0xCC)
    return bytes(b)

class TestV08(unittest.TestCase):
    def test_valid_synthetic(self):
        self.assertTrue(mod.verify(sample(),require_hash=False))

    def test_one_byte_only(self):
        a=sample()
        b,report=mod.patch_state(a,require_hash=False)
        self.assertEqual([i for i,(x,y) in enumerate(zip(a,b)) if x!=y],[mod.OFF])
        self.assertEqual(b[mod.OFF],0x7F)
        self.assertEqual(a[-200:],b[-200:])
        self.assertEqual(report["changed_bytes"],1)

    def test_reject_hash_mismatch(self):
        with self.assertRaises(ValueError):
            mod.verify(sample())

    def test_reject_code_mismatch(self):
        b=bytearray(sample());b[mod.OFF-1]=0x00
        with self.assertRaises(ValueError):
            mod.patch_state(bytes(b),require_hash=False)

    def test_reject_cr_shadow_mismatch(self):
        b=bytearray(sample());b[21+(0x233D-0x2000)]=0
        with self.assertRaises(ValueError):
            mod.verify(bytes(b),require_hash=False)

    def test_reject_mpr_mismatch(self):
        b=bytearray(sample());b[16]=0
        with self.assertRaises(ValueError):
            mod.verify(bytes(b),require_hash=False)

    def test_reject_truncation(self):
        with self.assertRaises(ValueError):
            mod.verify(sample()[:-1],require_hash=False)

    def test_cue_requirements(self):
        tracks=[]
        for n in range(1,36):
            typ="MODE1/2352" if n==2 else "AUDIO"
            tracks.append("TRACK %02d %s"%(n,typ))
        cue='FILE "'+mod.TRACK+'" BINARY\n'+'\n'.join(tracks)+'\n'
        self.assertEqual(mod.validate_cue(cue),cue)
        with self.assertRaises(ValueError):
            mod.validate_cue(cue.replace("TRACK 28 AUDIO","TRACK 28 MODE1/2352"))

if __name__=="__main__":
    unittest.main()
