"""Synthetic-only v0.10 tests: no copyrighted disc tracks committed."""
import hashlib
import struct
import unittest

import build_xak_iii_v10_disc_raster as v
import build_xak_iii_v03_visibility_probe as core


def dummy_sector():
    b=bytearray(core.SECTOR_SIZE)
    b[:12]=core.SYNC
    b[15]=1
    return core.restore_mode1_sector(bytes(b))


def sample():
    buf=bytearray(v.EXPECTED_LENGTH)
    for sec in v.EXPECTED_SECTORS:
        buf[sec*2352:(sec+1)*2352]=dummy_sector()
    def code(addr, val):
        off=v.disc_byte_offset(addr)
        buf[off:off+len(val)]=val
    code(v.CALLSITE-3,v.CALLSITE_CONTEXT)
    code(0x9C00,bytes.fromhex('48 DA 5A AD 99 9C C9 FF D0 41'))
    code(0x9C99,b'\xff')
    code(0x9CAA,bytes((118,112,114,116)))
    buf[0x1AB145:0x1AB148]=bytes.fromhex('20 00 9C')
    for sec in v.EXPECTED_SECTORS:
        i=sec*2352
        buf[i:i+2352]=core.restore_mode1_sector(bytes(buf[i:i+2352]))
    return bytes(buf)


class TestDiscRaster(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=sample()
        cls.digest=hashlib.sha256(cls.original).hexdigest()
        cls.new=v.patch_track(cls.original,cls.digest)

    def test_provenance(self):
        self.assertEqual(v.disc_byte_offset(0x65AA),0x1A821A)
        self.assertEqual(v.disc_byte_offset(0x76DF),0x1A95AF)
        self.assertEqual(v.disc_byte_offset(0x9C00),core.HOOK_RAW)
        self.assertEqual(v.disc_byte_offset(0x8EE5),0x1AB145)

    def test_two_sector_patch(self):
        dirty={i for i in range(len(self.original)//2352)
               if self.original[i*2352:i*2352+2352]!=self.new[i*2352:i*2352+2352]}
        self.assertEqual(dirty,{738,740})

    def test_exact_hook(self):
        self.assertEqual(v.read_code(self.new,v.CALLSITE,5),v.NEW)
        self.assertEqual(v.read_code(self.new,v.CAVE,10),v.HELPER)
        self.assertEqual(v.read_code(self.new,0x9CAA,4),bytes((118,112,114,116)))

    def test_mode1(self):
        for sec in v.EXPECTED_SECTORS:
            data=self.new[sec*2352:(sec+1)*2352]
            self.assertTrue(core.verify_mode1_sector(data))

    def test_ips_roundtrip(self):
        patch=core.create_ips(self.original,self.new)
        self.assertEqual(core.apply_ips(self.original,patch),self.new)
        self.assertLess(len(patch),2000)

    def test_wrong_hash_rejected(self):
        with self.assertRaisesRegex(ValueError,'Wrong Track02'):
            v.check_track(self.original)

    def test_cave_not_empty_rejected(self):
        b=bytearray(self.original)
        b[v.disc_byte_offset(v.CAVE)]=1
        off=740*2352
        b[off:off+2352]=core.restore_mode1_sector(bytes(b[off:off+2352]))
        bad=bytes(b)
        with self.assertRaisesRegex(ValueError,'code cave'):
            v.check_track(bad,hashlib.sha256(bad).hexdigest())

    def test_source_code_mismatch(self):
        b=bytearray(self.original)
        b[v.disc_byte_offset(v.CALLSITE-3)]=0
        off=738*2352
        b[off:off+2352]=core.restore_mode1_sector(bytes(b[off:off+2352]))
        bad=bytes(b)
        with self.assertRaisesRegex(ValueError,'raster code'):
            v.check_track(bad,hashlib.sha256(bad).hexdigest())

    def test_safe_cue(self):
        cue='FILE "'+v.INPUT_TRACK+'" BINARY\n'+''.join(
            f'TRACK {n:02d} '+('MODE1/2352' if n==2 else 'AUDIO')+'\n'
            for n in range(1,36))
        self.assertIn(v.OUTPUT_TRACK,v.make_cue(cue))
        with self.assertRaises(ValueError):
            v.make_cue(cue.replace('TRACK 28 AUDIO','TRACK 28 MODE1/2352'))

    def test_no_foreign_cpu(self):
        with self.assertRaises(ValueError):
            v.disc_byte_offset(0xC000)

    def test_camp_hash(self):
        state=bytearray(749238)
        struct.pack_into('<III',state,749238-200,0x82190619,44,749238)
        with self.assertRaises(ValueError):
            v.check_camp(bytes(state))

    def test_raster_truth_table(self):
        for table,want in ((0,0x0C),(0x80,0xCC),(0xC0,0xCC)):
            acc=(0xCC&0x3F)|table
            if acc&0x80: acc|=0x40
            self.assertEqual(acc,want)


if __name__=='__main__':
    unittest.main()
