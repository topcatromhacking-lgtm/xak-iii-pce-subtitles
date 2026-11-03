"""No copyrighted game data needed; independent v0.30 VCDIFF metadata tests."""
from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / 'tools' / 'verify_v030_release.py'
spec = importlib.util.spec_from_file_location('vs1_release_verify', TOOL)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

def vi(n):
    if n < 0:
        raise ValueError
    data = [n & 127]
    n >>= 7
    while n:
        data.insert(0, (n & 127) | 128)
        n >>= 7
    return bytes(data)

def sample(app=b'Xak III - The Eternal Recurrence (Japan) (Track 02).bin',
           source_size=128, target_size=256, has_adler=True):
    raw = bytearray(v.MAGIC + b'\x05\x02' + vi(len(app)) + app)
    header = vi(target_size) + b'\x00' + vi(2) + vi(2) + vi(1)
    if has_adler:
        header += b'\x12\x34\x56\x78'
    body = b'AB' + b'CD' + b'Z'
    raw += bytes([5 if has_adler else 1])
    raw += vi(source_size) + vi(0)
    raw += vi(len(header) + len(body))
    raw += header + body
    return bytes(raw)

class Metadata(unittest.TestCase):
    def test_parse_sample(self):
        r = v.parse_vcdiff(sample())
        self.assertEqual(r['target_bytes'], 256)
        self.assertEqual(r['window_count'], 1)
        self.assertEqual(r['secondary_compressor'], 2)
        self.assertEqual(r['windows'][0]['source_bytes'], 128)
        self.assertEqual(r['windows'][0]['adler32'], '12345678')

    def test_raw_no_checksum(self):
        r = v.parse_vcdiff(sample(has_adler=False))
        self.assertIsNone(r['windows'][0]['adler32'])

    def test_invalid_magic(self):
        with self.assertRaisesRegex(ValueError, 'Not a VCDIFF'):
            v.parse_vcdiff(b'FFFF')

    def test_truncation(self):
        for n in (1, 4, 8, 12):
            with self.subTest(n=n), self.assertRaises(ValueError):
                v.parse_vcdiff(sample()[:-n])

    def test_payload_boundary(self):
        with self.assertRaisesRegex(ValueError, 'Truncated'):
            v.parse_vcdiff(sample()[:-1])

    def test_source_segment_bounds(self):
        with self.assertRaisesRegex(ValueError, 'source exceeds'):
            v.parse_vcdiff(sample(source_size=v.RAW_BYTES + 1))

    def test_delta_length_tamper(self):
        b = bytearray(sample(app=b'T'))
        idx = 4 + 1 + 1 + 1 + 1 + 1 + 2 + 1
        b[idx] -= 1
        with self.assertRaisesRegex(ValueError, 'delta-length'):
            v.parse_vcdiff(bytes(b))

    def test_invalid_win_indicator(self):
        b = bytearray(sample(app=b'T'))
        b[8] = 0xFF
        with self.assertRaisesRegex(ValueError, 'window indicator'):
            v.parse_vcdiff(bytes(b))

    def test_reject_changed_patch_sha(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'wrong.xdelta'
            p.write_bytes(sample())
            with self.assertRaisesRegex(ValueError, 'size mismatch'):
                v.inspect_patch(p)

    def test_wrong_source_rejected_without_xdelta3(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'wrong.bin'
            p.write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError, 'size'):
                v.full_verify(Path(d) / 'fake.xdelta', p, {})

    def test_full_release_patch_if_available(self):
        filename = os.getenv('XAK_V030_PATCH')
        if not filename:
            self.skipTest('Set XAK_V030_PATCH to the user-owned v0.30 xdelta')
        report = v.inspect_patch(Path(filename))
        self.assertEqual(report['window_count'], v.EXPECTED_WINDOWS)
        self.assertEqual(report['target_bytes'], v.RAW_BYTES)
        self.assertEqual(report['patch_sha256'], v.PATCH_SHA256)

if __name__ == '__main__':
    unittest.main()
