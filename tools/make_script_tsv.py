#!/usr/bin/env python3
"""Build script/xak3_cutscenes.tsv from the cue list below.

Japanese text is pulled verbatim from NightWolve's public
XakIII-Jap2EngScript.html (zip kept in private/nightwolve/script/) by ISO
offset + <\\p> segment index, so ja_text is never hand-typed.  English
subtitles are our own concise re-translation; NightWolve's original English is
kept in en_reference for comparison.

Usage: python3 tools/make_script_tsv.py [--nw-zip PATH] [-o script/xak3_cutscenes.tsv]

Re-running preserves any start/end timings already present in the output TSV
(matched by cue_id).
"""
import argparse, csv, html, io, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_ZIP = os.path.join(ROOT, "private/nightwolve/script/XakIII-Jap2EngScript.zip")
COLS = ["cue_id", "scene_id", "cd_track", "speaker", "ja_text", "ja_source",
        "en_subtitle", "en_reference", "start", "end", "status", "notes"]

SCENES = {
 "VS1": ("28", "Webis Castle throne room: audience with King Webis (NW stage 6a)"),
 "VS2": ("31", "Meeting Fray outside Webis Royal Palace"),
 "VS3": ("32", "Necromancer's demise / Ratok's father"),
 "VS4": ("29", "Admiral Leo, Sunkan, Fray, Ryun, Mesuron and Yunker"),
 "VS5": ("33", "Audience with fairy princess Lou Millie Pixie (Oceanity)"),
 "VS6": ("34", "Ratok's arrival: return to Fearless (ending)"),
 "VS7": ("30|35?", "Hoan Ashtar's forgotten myth (ending/epilogue)"),
}

# (cue_id, scene, nw_offset, segment_index or None, speaker, en_subtitle, status, notes, ja_override)
#   '|' in en_subtitle = line break.  ja_override: verbatim slice of the NW segment
#   when one NW box is split across several cues.
D, V, T, S = "DRAFT", "DRAFT-verify-audio", "TODO-needs-audio", "SKIP-system-text"
CUES = [
 # ---- VS1 / Track 28: full Japanese preserved in the ISO (only cinema whose text is on disc)
 ("VS1-001","VS1",9704325,0,"King Webis","You have done well, Ratok.|Splendid work in Farland!",D,"Repo cue plan used NW wording 'That was quite a ceremony'; 大儀であった = 'well done'.",None),
 ("VS1-002","VS1",9704422,0,"Ratok","Y-Your Majesty, I hope you|are well... er... um...",D,"",None),
 ("VS1-003","VS1",9704478,0,"King Webis","Now, now. Let's dispense|with the formalities.",D,"",None),
 ("VS1-004","VS1",9704478,1,"King Webis","More importantly, there's a|lady who wishes to see you.",D,"",None),
 ("VS1-005","VS1",9704584,0,"Ratok","???",D,"",None),
 ("VS1-006","VS1",9704602,0,"Ratok","Pixie?!",D,"",None),
 ("VS1-007","VS1",9704626,0,"Pixie","You weren't planning to|leave me behind, were you?",D,"",None),
 ("VS1-008","VS1",9704700,0,"Ratok","You've shrunk again?",D,"",None),
 ("VS1-009","VS1",9704736,0,"Pixie","Since the demons invaded,|my fairy power is weak here.",D,"妖精界 = fairy realm (NW had 'demon world').",None),
 ("VS1-010","VS1",9704736,1,"Pixie","So I couldn't keep human|size, and I shrank!",D,"",None),
 ("VS1-011","VS1",9704868,0,"General Beluga","I expect the demon attacks|to grow fiercer from now on.",D,"",None),
 ("VS1-012","VS1",9704868,1,"General Beluga","My lords, I urge you all:|never neglect your defenses.",D,"",None),
 ("VS1-013","VS1",9704994,0,"King Webis","Indeed. Webis is making|preparations as well.",D,"",None),
 ("VS1-014","VS1",9704994,1,"King Webis","It burdens our people, but|this matter is urgent.",D,"",None),
 ("VS1-015","VS1",9705106,0,"Ratok","Have you learned anything|about the \"Gate\"?",D,"",None),
 ("VS1-016","VS1",9705158,0,"King Webis","We have.",D,"",None),
 ("VS1-017","VS1",9705180,0,"Magician","Allow me to explain that.",D,"",None),
 ("VS1-018","VS1",9705232,0,"Magician","The Gate's origins go back|to the War of Sealing.",D,"",None),
 ("VS1-019","VS1",9705302,0,"Ratok","The War of Sealing...",D,"",None),
 ("VS1-020","VS1",9705328,0,"Magician","Yes. The war the gods fought|to seal away the demons.",D,"",None),
 ("VS1-021","VS1",9705328,1,"Magician","We've learned the Gate is a|magic device from that war.",D,"",None),
 ("VS1-022","VS1",9705468,0,"Pixie","So what does this|\"Gate\" thing do?",D,"",None),
 ("VS1-023","VS1",9705518,0,"Magician","It seems to be large-scale|teleportation magic.",D,"",None),
 ("VS1-024","VS1",9705518,1,"Magician","...Beyond that, I can't say.",D,"",None),
 ("VS1-025","VS1",9705598,0,"General Beluga","Strategically, that's a|most intriguing story.",D,"",None),
 ("VS1-026","VS1",9705658,0,"Ratok","So where is this \"Gate\"?",D,"",None),
 ("VS1-027","VS1",9705712,0,"Magician","To be honest, that much|I do not know.",D,"",None),
 ("VS1-028","VS1",9705766,0,"Ratok","No leads, then...",D,"",None),
 ("VS1-029","VS1",9705804,0,"Magician","Oh yes, there is one|more thing we learned.",D,"",None),
 ("VS1-030","VS1",9705804,1,"Magician","A sorcerer, Gafuh, lives in|a tower atop Mt. Fuji.",D,"ギンガヌール山 = Mt. Fuji in NightWolve's patch (literally Mt. Ginganul).",None),
 ("VS1-031","VS1",9705804,2,"Magician","He seems to know a great|deal about magic devices.",D,"",None),
 ("VS1-032","VS1",9705984,0,"King Webis","Gafuh? I hear he's quite|the eccentric...",D,"",None),
 ("VS1-033","VS1",9705984,1,"Magician","Yes. He shuns people and|devotes himself to research.",D,"NW box holds two speakers; split here.",None),
 ("VS1-034","VS1",9706137,0,"Ratok","Anyway, I'll go ask Gafuh.|Mt. Fuji, right?",D,"",None),
 ("VS1-035","VS1",9706218,0,"Magician","That's right.",D,"",None),
 ("VS1-036","VS1",9706238,0,"Ratok","Could someone who knows the|way to Mt. Fuji guide me?",D,"",None),
 ("VS1-037","VS1",9706324,0,"Pixie","Then I know the way!",D,"",None),
 ("VS1-038","VS1",9706324,1,"Pixie","In case you forgot, I was|a palace messenger.",D,"NW misread 忘れてるかもしれないけど ('you may have forgotten').","忘れてるかもしれないけど、王宮のメッセンジャーをやってたのよ、"),
 ("VS1-039","VS1",9706324,1,"Pixie","I know my way around|all of Webis.",D,"","ウェービス国内の地理ならだいたいわかるわ"),
 ("VS1-040","VS1",9706468,0,"Ratok","All right, let's head out!",D,"",None),
 ("VS1-041","VS1",9706496,0,"King Webis","In times like these I can't|offer much, but take this.",D,"",None),
 ("VS1-042","VS1",9706496,1,"(system)","",S,"Item-get message (Gemil Potion + 1000 Gold); not voiced, no subtitle.",None),
 ("VS1-043","VS1",9706630,0,"King Webis","This Gate is a grave threat|to us all.",D,"",None),
 ("VS1-044","VS1",9706630,1,"King Webis","Ratok, I leave the matter|of the Gate to you.",D,"",None),
 ("VS1-045","VS1",9706726,0,"Ratok","Yes. I won't fail...",D,"",None),
 ("VS1-046","VS1",9706754,0,"Ratok","Pixie?",D,"",None),
 ("VS1-047","VS1",9706754,1,"Ratok","What's wrong?",D,"",None),
 ("VS1-048","VS1",9706794,0,"Pixie","Your shoulder really is the|comfiest spot, Ratok.",D,"",None),
 ("VS1-049","VS1",9706846,0,"Ratok","You won't get off even if I|ask, will you?",D,"",None),
 ("VS1-050","VS1",9706890,0,"Pixie","Of course not!",D,"",None),
 ("VS1-051","VS1",9706922,0,"Ratok","...Good grief.",D,"",None),
 ("VS1-052","VS1",9706948,0,"Pixie","But if you don't like it...",D,"",None),
 ("VS1-053","VS1",9706988,0,"Ratok","H-Hey, Pixie! That tickles!",D,"",None),
 ("VS1-054","VS1",9706988,1,"Ratok","I thought you liked my|shoulder better!",D,"",None),
 ("VS1-055","VS1",9707060,0,"Pixie","But your chest is nice|and warm, too.",D,"",None),
 ("VS1-056","VS1",9707094,0,"Ratok","...",D,"",None),
 # ---- VS2 / Track 31: SkyeWelse matched these to in-game text boxes (NW stage 6c)
 ("VS2-001","VS2",5566330,0,"Fray","Huh?",V,"JP is the in-game text box that SkyeWelse (2006) matched to this cinema; confirm against Track 31.",None),
 ("VS2-002","VS2",5566348,0,"Pixie","Don't \"huh\" me! I asked|what we should do next!",V,"",None),
 ("VS2-003","VS2",5566348,1,"Pixie","Spacing out, as always!",V,"",None),
 ("VS2-004","VS2",5566462,0,"Fray","Excuse me? I was not|spacing out!",V,"",None),
 ("VS2-005","VS2",5566518,0,"Pixie","Oh, really?",V,"",None),
 ("VS2-006","VS2",5566518,1,"Pixie","Then tell me where|we're going next.",V,"",None),
 ("VS2-007","VS2",5566596,0,"Fray","Uh... well...",V,"",None),
 ("VS2-008","VS2",5566630,0,"Pixie","See? You can't answer.",V,"",None),
 ("VS2-009","VS2",5566630,1,"Pixie","Listen up. We're off to see|Gafuh, on Mt. Fuji.",V,"",None),
 ("VS2-010","VS2",None,None,"Ratok","Oh, I see.",T,"Only in the 2006 transcript (English, from listening); no Japanese source.",None),
 ("VS2-011","VS2",None,None,"Pixie","...",T,"Only in the 2006 transcript.",None),
 # ---- VS3 / Track 32: matched to NW stage 22-8 text boxes; father dialogue never transcribed
 ("VS3-001","VS3",None,None,"?","",T,"Necromancer's demise + dialogue with Ratok's father: not in any public script; transcribe from Track 32.",None),
 ("VS3-002","VS3",5576399,0,"Xak Sword","Ratok!",V,"JP from in-game box matched by SkyeWelse; confirm against Track 32.",None),
 ("VS3-003","VS3",5576399,1,"Xak Sword","Heir of the raging|Thunder God!",V,"",None),
 ("VS3-004","VS3",5576399,2,"Xak Sword","The time has come!!",V,"",None),
 ("VS3-005","VS3",5576464,0,"Ratok","...That's right, Xak Sword!",V,"",None),
 ("VS3-006","VS3",5576464,1,"Ratok","I'll put an end to it all!",V,"",None),
 ("VS3-007","VS3",5576538,0,"Xak Sword","Spoken like a Duel Knight!",V,"",None),
 ("VS3-008","VS3",5576584,0,"Ratok","Father... I will carry on|your will.",V,"",None),
 ("VS3-009","VS3",5576584,1,"Ratok","Please, watch over me...",V,"",None),
 ("VS3-010","VS3",5576666,0,"Ratok","Let's go, Xak Sword!",V,"",None),
 ("VS3-011","VS3",5576666,1,"Ratok","To defeat Zekishis!",V,"",None),
 ("VS3-012","VS3",5576713,0,"Xak Sword","Yes!",V,"",None),
 # ---- VS4-VS7: no Japanese or English text exists publicly
 ("VS4-001","VS4",None,None,"?","",T,"No public transcript. Whole scene must be transcribed from Track 29.",None),
 ("VS5-001","VS5",None,None,"?","",T,"No public transcript. Whole scene must be transcribed from Track 33.",None),
 ("VS6-001","VS6",None,None,"?","",T,"Ending. No public transcript. Transcribe from Track 34.",None),
 ("VS7-001","VS7",None,None,"?","",T,"Ending/epilogue. Track unconfirmed (30 or 35); identify by listening.",None),
]


def load_nw(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        raw = z.read("XakIII-Jap2EngScript.html").decode("cp932", errors="replace")
    rows = {}
    pat = re.compile(r'<TD WIDTH=58[^>]*>(\d+)</TD><TD[^>]*><span>(.*?)</span><TD[^>]*><PRE>(.*?)</PRE>', re.S)
    for m in pat.finditer(raw):
        rows[int(m.group(1))] = (html.unescape(m.group(2)), html.unescape(m.group(3)))
    return rows

def segments(jp):
    """Split a NW box at <\\p>, dropping speaker-name lines (a line directly
    followed by a line opening with 「) and markup."""
    lines = jp.replace("<cls>", "").split("\n")
    keep = []
    for i, l in enumerate(lines):
        nxt = next((x.strip() for x in lines[i + 1:] if x.strip()), "")
        if l.strip() and "「" not in l and "<\\p>" not in l and nxt.startswith("「") and len(l.strip()) <= 12:
            continue
        keep.append(l)
    out = []
    for seg in "\n".join(keep).split("<\\p>"):
        t = "".join(x.strip() for x in seg.split("\n"))
        t = t.replace("　", "").replace("「", "").replace("」", "")
        t = re.sub(r"<[^>]+>(\[[0-9A-F]+\])?", "", t)
        if t:
            out.append(t)
    return out

def en_ref(en):
    t = re.sub(r"<scr>\[[0-9A-F]+\]|<posxy2>\[[0-9A-F]+\]|<cls>", "", en).replace("</p>", " ")
    return re.sub(r"\s+", " ", t).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nw-zip", default=DEFAULT_ZIP)
    ap.add_argument("-o", "--out", default=os.path.join(ROOT, "script/xak3_cutscenes.tsv"))
    ap.add_argument("--public", action="store_true",
                    help="leave ja_text and the NW English reference empty (keep only the "
                         "ja_source pointer) for the public repository; rerun without it "
                         "locally to fill them from your own copy of the NW script zip")
    a = ap.parse_args()
    nw = load_nw(a.nw_zip)
    old = {}
    if os.path.exists(a.out):
        with open(a.out, encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
                old[r["cue_id"]] = r
    out = []
    for cid, sc, off, seg, spk, en, st, note, jov in CUES:
        ja, src, ref = "", "", ""
        if off is not None:
            jp, nwen = nw[off]
            segs = segments(jp)
            ja = segs[seg]
            if jov:
                assert jov in ja, (cid, jov, ja)
                ja = jov
            src = f"NW-Jap2EngScript@{off}#{seg}"
            ref = "NW: " + en_ref(nwen)
        elif st == T and en:
            ref = "YsUtopia topic 205 (2006 listening transcript)"
        if a.public:
            ja = ""
            ref = "" if ref.startswith("NW: ") else ref
        r = dict(cue_id=cid, scene_id=sc, cd_track=SCENES[sc][0], speaker=spk, ja_text=ja,
                 ja_source=src or ("none" if st == T else ""), en_subtitle=en, en_reference=ref,
                 start=old.get(cid, {}).get("start", ""), end=old.get(cid, {}).get("end", ""),
                 status=st, notes=note)
        out.append(r)
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter="\t", lineterminator="\n",
                           quoting=csv.QUOTE_NONE, quotechar=None)
        w.writeheader(); w.writerows(out)
    from collections import Counter
    c = Counter(r["status"] for r in out)
    print(f"wrote {a.out}: {len(out)} cues in {len(SCENES)} scenes; " + ", ".join(f"{k}={v}" for k, v in sorted(c.items())))

if __name__ == "__main__":
    main()
