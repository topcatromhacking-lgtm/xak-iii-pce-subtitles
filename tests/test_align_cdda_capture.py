"""Synthetic timebase test; no copyrighted audio required."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "tools"))
from align_cdda_capture import fit_alignment

class TestAlignment(unittest.TestCase):
    def test_offset_and_drift(self):
        sr=8000
        rng=np.random.default_rng(1429)
        source=rng.normal(0,.12,65*sr).astype(np.float32)
        audio=source*np.sin(np.arange(len(source))*2*np.pi*440/sr)
        offset,slope=3.5,1.0002
        t=np.arange(75*sr)/sr
        recording=np.interp((t-offset)/slope,np.arange(len(audio))/sr,audio,left=0,right=0).astype(np.float32)
        result=fit_alignment(audio,recording,start_guess=offset,rate_guess=slope,rate=sr,
                             step_seconds=5,window_seconds=5,search_seconds=.5)
        self.assertAlmostEqual(result["intercept_seconds"],offset,delta=.02)
        self.assertAlmostEqual(result["capture_seconds_per_track_second"],slope,delta=.001)
        self.assertGreater(result["r_squared"],.999)

if __name__ == "__main__":
    unittest.main()
