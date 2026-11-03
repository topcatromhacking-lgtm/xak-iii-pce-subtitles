#!/usr/bin/env python3
"""Lint script/xak3_cutscenes.tsv against the subtitle renderer's real limits.

Hard limits (ERROR) come from the renderer, see docs/renderer-design.md:
  * at most 2 lines per cue ('|' = line break)
  * each line <= MAX_LINE_PX (240 px) measured with the real proportional font
    = 15 x 16 px sprites per scanline (hardware max 16; 1 kept spare for native
    sprites crossing the band), and the 8 px CRT overscan margin on each side
  * every character must exist in font/xak3_subfont.png
  * names must use NightWolve spellings (avoid-list parsed from script/glossary.md)
  * start/end, when filled, must be increasing and must not overlap within a scene
Soft limits (WARN): > SOFT_CHARS (28) characters per line (style target: an 8 px
fixed-width font would fit 30), reading speed > 17 chars/s, cue < 0.8 s or > 7 s.

Usage: python3 tools/lint_script.py [script/xak3_cutscenes.tsv] [--strict]
"""
import argparse, csv, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from font_build import Font, MAX_LINE_PX, MAX_LINES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOFT_CHARS = 28
MAX_CPS = 17.0
STATUSES = {"DRAFT", "DRAFT-verify-audio", "TODO-needs-audio", "SKIP-system-text", "FINAL"}
REQUIRED = ["cue_id", "scene_id", "cd_track", "speaker", "ja_text", "ja_source",
            "en_subtitle", "start", "end", "status"]

def parse_time(s):
    s = s.strip()
    if not s:
        return None
    if ":" in s:
        m, sec = s.split(":", 1)
        return int(m) * 60 + float(sec)
    return float(s)

def load_avoid(path):
    avoid = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            m = re.match(r"\s*avoid:\s*(.+?)\s*->\s*(.+?)\s*$", line)
            if m:
                avoid.append((m.group(1), m.group(2)))
    return avoid

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv", nargs="?", default=os.path.join(ROOT, "script/xak3_cutscenes.tsv"))
    ap.add_argument("--glossary", default=os.path.join(ROOT, "script/glossary.md"))
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    a = ap.parse_args()
    font = Font()
    avoid = load_avoid(a.glossary)
    errs, warns = [], []
    with open(a.tsv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    missing = [c for c in REQUIRED if c not in (rows[0].keys() if rows else [])]
    if missing:
        print("ERROR missing columns:", missing); return 2
    seen, last_end = set(), {}
    widest = (0, "")
    for r in rows:
        cid = r["cue_id"]
        E = lambda m: errs.append(f"{cid}: {m}")
        W = lambda m: warns.append(f"{cid}: {m}")
        if cid in seen: E("duplicate cue_id")
        seen.add(cid)
        st = r["status"]
        if st not in STATUSES: E(f"unknown status {st!r}")
        en = r["en_subtitle"]
        if st in ("DRAFT", "DRAFT-verify-audio", "FINAL"):
            # ja_text may be empty in the public (--public) TSV; the pointer is mandatory
            if not r["ja_source"] or r["ja_source"] == "none":
                E("status needs ja_source (use TODO-needs-audio otherwise)")
            if not en: E("empty en_subtitle")
        if st == "SKIP-system-text" and en: W("SKIP row has a subtitle")
        if en:
            lines = en.split("|")
            if len(lines) > MAX_LINES: E(f"{len(lines)} lines > {MAX_LINES}")
            for ln in lines:
                bad = sorted({c for c in ln if not font.supports(c)})
                if bad: E(f"glyphs not in font: {bad}"); continue
                px = font.width(ln)
                widest = max(widest, (px, ln))
                if px > MAX_LINE_PX: E(f"line {ln!r} is {px} px > {MAX_LINE_PX}")
                if len(ln) > SOFT_CHARS: W(f"line {ln!r} has {len(ln)} chars > {SOFT_CHARS}")
                if ln != ln.strip(): W(f"leading/trailing space in {ln!r}")
            for bad, good in avoid:
                if re.search(r"\b" + re.escape(bad) + r"\b", en):
                    E(f"uses {bad!r}; NightWolve spelling is {good!r}")
        t0, t1 = parse_time(r["start"]), parse_time(r["end"])
        if (t0 is None) != (t1 is None): E("only one of start/end set")
        if t0 is not None and t1 is not None:
            if t1 <= t0: E("end <= start")
            d = t1 - t0
            if d < 0.8: W(f"cue only {d:.2f}s")
            if d > 7.0: W(f"cue {d:.2f}s long")
            n = len(en.replace("|", " "))
            if d > 0 and n / d > MAX_CPS: W(f"reading speed {n/d:.1f} cps > {MAX_CPS}")
            key = (r["scene_id"], r["cd_track"])
            if key in last_end and t0 < last_end[key] - 1e-6: E(f"overlaps previous cue (starts {t0} < {last_end[key]})")
            last_end[key] = t1
    for w in warns: print("WARN ", w)
    for e in errs: print("ERROR", e)
    from collections import Counter
    c = Counter(r["status"] for r in rows)
    timed = sum(1 for r in rows if r["start"].strip())
    print(f"{len(rows)} cues, {len({r['scene_id'] for r in rows})} scenes, {timed} timed; "
          + ", ".join(f"{k}={v}" for k, v in sorted(c.items()))
          + f"; widest line {widest[0]}/{MAX_LINE_PX} px {widest[1]!r}; {len(errs)} errors, {len(warns)} warnings")
    return 1 if errs or (a.strict and warns) else 0

if __name__ == "__main__":
    sys.exit(main())
