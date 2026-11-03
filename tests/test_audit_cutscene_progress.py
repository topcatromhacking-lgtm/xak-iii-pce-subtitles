"""Public-script completeness audit tests with a synthetic scenario."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest
TOOL = Path(__file__).resolve().parents[1] / 'tools/audit_cutscene_progress.py'
spec=importlib.util.spec_from_file_location('audit_cutscene_progress',TOOL)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class Audit(unittest.TestCase):
    def test_coverage_and_placeholders(self):
        with tempfile.TemporaryDirectory() as td:
            tsv=Path(td)/'script.tsv'
            fields=['cue_id','scene_id','cd_track','en_subtitle','start','end','status']
            rows=[
                dict(cue_id='VS1-001',scene_id='VS1',cd_track='28',en_subtitle='Hello.',start='1',end='3',status='DRAFT'),
                dict(cue_id='VS1-002',scene_id='VS1',cd_track='28',en_subtitle='???',start='3',end='5',status='DRAFT'),
                dict(cue_id='VS1-003',scene_id='VS1',cd_track='28',en_subtitle='',start='',end='',status='SKIP-system-text'),
                dict(cue_id='VS2-001',scene_id='VS2',cd_track='31',en_subtitle='Goodbye.',start='1',end='2',status='REVIEWED')]
            with tsv.open('w',encoding='utf8',newline='') as f:
                w=csv.DictWriter(f,fieldnames=fields,delimiter='\t');w.writeheader();w.writerows(rows)
            x=a.audit(tsv)
            self.assertEqual(x['total_timed_cues'],3)
            self.assertEqual(x['scenes']['VS1']['playable_cues'],2)
            self.assertEqual(x['scenes']['VS1']['placeholder_cue_ids'],['VS1-002'])
            self.assertEqual(x['ready_scenes'],['VS2'])

    def test_missing_timing(self):
        with tempfile.TemporaryDirectory() as td:
            tsv=Path(td)/'s.tsv'
            tsv.write_text('cue_id\tscene_id\tcd_track\ten_subtitle\tstart\tend\tstatus\nVS3-001\tVS3\t32\tHello.\t\t\tDRAFT\n')
            x=a.audit(tsv)
            self.assertEqual(x['scenes']['VS3']['untimed_cue_ids'],['VS3-001'])

    def test_bad_input(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.tsv';p.write_text('bad\n')
            with self.assertRaises(ValueError):a.audit(p)

if __name__=='__main__':unittest.main()
