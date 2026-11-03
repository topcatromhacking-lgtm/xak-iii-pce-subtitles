"""Guard against destructive Track02 rebuilds; run in the repository checkout."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ENGINE = Path(__file__).resolve().parents[1] / 'tools/engine/build_subs.py'

class BuildOutputSafety(unittest.TestCase):
    @unittest.skipUnless(ENGINE.exists(), 'Run from checkout with tools/engine/build_subs.py')
    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            original=root/'input.bin'
            original.write_bytes(b'not-real-game-data')
            target=root/'existing.bin'
            target.write_bytes(b'DO NOT CHANGE')
            r=subprocess.run([sys.executable,str(ENGINE),'--track02',str(original),
                '--tsv',str(root/'none.tsv'),'-o',str(target)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('Refusing to overwrite',r.stderr+r.stdout)
            self.assertEqual(target.read_bytes(),b'DO NOT CHANGE')

    @unittest.skipUnless(ENGINE.exists(), 'Run from checkout with tools/engine/build_subs.py')
    def test_input_path_cannot_be_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            original=root/'input.bin'
            original.write_bytes(b'DO NOT CHANGE')
            r=subprocess.run([sys.executable,str(ENGINE),'--track02',str(original),
                '--tsv',str(root/'none.tsv'),'-o',str(original)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('Refusing to overwrite',r.stderr+r.stdout)
            self.assertEqual(original.read_bytes(),b'DO NOT CHANGE')

if __name__=='__main__':
    unittest.main()
