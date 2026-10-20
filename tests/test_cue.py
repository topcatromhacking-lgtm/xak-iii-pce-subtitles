"""Synthetic tests: no proprietary game bytes or disc images are required."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from make_split_cue import convert


class CueTests(unittest.TestCase):
    def test_replace_only_track02(self):
        src = ''.join(
            f'FILE "Game (Track {i:02d}).bin" BINARY\n'
            f'  TRACK {i:02d} {"MODE1/2352" if i == 2 else "AUDIO"}\n'
            for i in range(1, 36)
        )
        out = convert(src, 'English02.bin')
        self.assertEqual(out.count('FILE "English02.bin"'), 1)
        self.assertNotIn('Game (Track 02).bin', out)
        self.assertIn('Game (Track 03).bin', out)
        self.assertEqual(out.count('TRACK '), 35)

    def test_reject_unsafe_filename(self):
        src = ''.join(
            f'FILE "Game (Track {i:02d}).bin" BINARY\n  TRACK {i:02d} AUDIO\n'
            for i in range(1, 36)
        )
        with self.assertRaises(ValueError):
            convert(src, '"malformed.bin')


if __name__ == '__main__':
    unittest.main()
