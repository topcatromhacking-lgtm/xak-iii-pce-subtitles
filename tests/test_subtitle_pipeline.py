"""Synthetic tests for the subtitle pipeline: no game bytes, disc images or BIOS."""
import csv, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
from font_build import Font, MAX_LINE_PX, to_sprites  # noqa: E402

COLS = ["cue_id", "scene_id", "cd_track", "speaker", "ja_text", "ja_source", "en_subtitle",
        "en_reference", "start", "end", "status", "notes"]


def row(cid, en, start="", end="", status="DRAFT", src="NW-Jap2EngScript@1#0", scene="VS9"):
    return dict(cue_id=cid, scene_id=scene, cd_track="28", speaker="", ja_text="", ja_source=src,
                en_subtitle=en, en_reference="", start=start, end=end, status=status, notes="")


def write_tsv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter="\t", lineterminator="\n",
                           quoting=csv.QUOTE_NONE, quotechar=None)
        w.writeheader(); w.writerows(rows)


def read_tsv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def lint(path, *extra):
    p = subprocess.run([sys.executable, str(TOOLS / "lint_script.py"), str(path), *extra],
                       capture_output=True, text=True)
    return p.returncode, p.stdout


class LintTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.p = Path(self.d.name) / "t.tsv"

    def tearDown(self):
        self.d.cleanup()

    def check(self, rows, expect_rc, needle=None, *extra):
        write_tsv(self.p, rows)
        rc, out = lint(self.p, *extra)
        self.assertEqual(rc, expect_rc, out)
        if needle:
            self.assertIn(needle, out)

    def test_repo_script_is_clean(self):
        rc, out = lint(ROOT / "script/xak3_cutscenes.tsv")
        self.assertEqual(rc, 0, out)

    def test_ok(self):
        self.check([row("A-1", "Hello, Ratok.|Welcome home.", "1.0", "3.0")], 0)

    def test_three_lines(self):
        self.check([row("A-1", "a|b|c")], 1, "3 lines")

    def test_too_wide(self):
        self.check([row("A-1", "W" * 50)], 1, "px >")

    def test_missing_glyph(self):
        self.check([row("A-1", "caf\u00e9")], 1, "glyphs not in font")

    def test_avoid_name(self):
        self.check([row("A-1", "Latok, come here.")], 1, "NightWolve spelling")

    def test_draft_needs_source(self):
        self.check([row("A-1", "Hi.", src="")], 1, "needs ja_source")

    def test_duplicate_and_overlap(self):
        self.check([row("A-1", "One.", "1", "3"), row("A-1", "Two.", "2", "4")], 1, "duplicate")
        self.check([row("A-1", "One.", "1", "3"), row("A-2", "Two.", "2", "4")], 1, "overlaps")

    def test_end_before_start(self):
        self.check([row("A-1", "One.", "3", "1")], 1, "end <= start")

    def test_strict_warns(self):
        r = [row("A-1", "This line is quite a lot longer.", "1.0", "1.3")]
        self.check(r, 0, "WARN")
        self.check(r, 1, None, "--strict")


class FontTests(unittest.TestCase):
    def test_sprite_split_centres(self):
        f = Font()
        text = "You have done well, Ratok."
        w = f.width(text)
        pats, x_left = to_sprites(f.render(text))
        n = (w + 15) // 16
        self.assertEqual(len(pats), n)
        self.assertTrue(all(len(p) == 128 for p in pats))
        self.assertEqual(x_left, (256 - 16 * n) // 2)
        self.assertLessEqual(16 * n, MAX_LINE_PX)

    def test_planes_2_3_empty(self):
        pats, _ = to_sprites(Font().render("Splendid work in Farland!"))
        for p in pats:
            self.assertEqual(bytes(p[64:]), bytes(64))  # only planes 0/1 (text + shadow) used


class TimingTests(unittest.TestCase):
    def test_synthetic_selftest(self):
        p = subprocess.run([sys.executable, str(TOOLS / "timing/selftest_synth.py")],
                           capture_output=True, text=True, timeout=300)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_labels_write_and_fit(self):
        import vad_cues_shim as v  # noqa
        with tempfile.TemporaryDirectory() as d:
            tsv = Path(d) / "t.tsv"; lab = Path(d) / "l.txt"
            write_tsv(tsv, [row("S-1", "One."), row("S-2", "Two."),
                            row("S-3", "", status="SKIP-system-text", src=""),
                            row("S-4", "Three.")])
            lab.write_text("1.000\t2.500\ta\n3.000\t4.000\tb\n5.000\t6.250\tc\n")
            p = subprocess.run([sys.executable, str(TOOLS / "timing/vad_cues.py"), "--from-labels",
                                str(lab), "--scene", "VS9", "--tsv", str(tsv), "--write"],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            got = {r["cue_id"]: (r["start"], r["end"]) for r in read_tsv(tsv)}
            self.assertEqual(float(got["S-1"][0]), 1.0)
            self.assertEqual(float(got["S-2"][1]), 4.0)
            self.assertEqual(got["S-3"], ("", ""))
            self.assertEqual(float(got["S-4"][0]), 5.0)

    def test_fit_merges_and_splits(self):
        import vad_cues_shim as v  # noqa
        segs = [(0, 1), (1.2, 2), (5, 6)]
        self.assertEqual(len(v.fit(list(segs), 2)), 2)
        self.assertEqual(list(v.fit(list(segs), 2)[0]), [0, 2])
        self.assertEqual(len(v.fit(list(segs), 5)), 5)


sys.path.insert(0, str(TOOLS / "timing"))
import importlib  # noqa: E402
sys.modules["vad_cues_shim"] = importlib.import_module("vad_cues")

if __name__ == "__main__":
    unittest.main()
