"""Synthetic-only regression tests. No copyrighted reference disc material."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from analyze_xak_i_ii_reference_xdelta import parse_vcdiff, changed_raw_sectors, FormatError

def varint(n):
    vals = [n & 127]
    n >>= 7
    while n:
        vals.insert(0, (n & 127) | 128)
        n >>= 7
    return bytes(vals)

def mock_delta(blob=b"HELLO"):
    # VCDIFF secondary ID=2 (LZMA), mocked uncompressed section payload.
    body = varint(len(blob)) + b"\x00" + varint(len(blob)) + b"\x00\x00" + b"\0"*4 + blob
    return bytes.fromhex("d6c3c400") + b"\x05\x02" + varint(6) + b"header" + (
        b"\x05" + varint(5) + varint(0) + varint(len(body)) + body)

class TestReferenceDelta(unittest.TestCase):
    def test_window(self):
        d = parse_vcdiff(mock_delta())
        self.assertEqual(d["compressor"], "LZMA")
        self.assertEqual(d["application_header"], "header")
        self.assertEqual(d["target_bytes"], 5)
        self.assertEqual(len(d["windows"]), 1)

    def test_bad_magic(self):
        with self.assertRaises(FormatError):
            parse_vcdiff(b"not vcdiff")

    def test_truncated(self):
        with self.assertRaises(FormatError):
            parse_vcdiff(mock_delta()[:-1])

    def test_invalid_header_bits(self):
        b = bytearray(mock_delta())
        b[4] = 0x85
        with self.assertRaises(FormatError):
            parse_vcdiff(bytes(b))

    def test_changed_sectors(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "a", Path(folder) / "b"
            before = bytearray(2352 * 4)
            after = bytearray(before)
            after[2352 + 10] = 1
            after[2352 * 2 + 20] = 2
            a.write_bytes(before)
            b.write_bytes(after)
            result = changed_raw_sectors(a, b)
            self.assertEqual(result["changed_sectors"], 2)
            self.assertEqual(result["changed_bytes"], 2)
            self.assertEqual(result["raw_sector_spans"][0]["first"], 1)

    def test_reject_non_sector_aligned(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b = Path(folder)/"a",Path(folder)/"b"
            a.write_bytes(b"abc")
            b.write_bytes(b"abc")
            with self.assertRaises(ValueError):
                changed_raw_sectors(a,b)

if __name__ == "__main__":
    unittest.main()
