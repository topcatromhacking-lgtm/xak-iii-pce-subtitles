#!/usr/bin/env python3
"""Build a Xak III Track 02 with the runtime subtitle engine for one cinematic scene.

  python3 tools/engine/build_subs.py --tsv PRIVATE.tsv --scene VS1 \
      --track02 Xak_III_English_Track02_SUB_TEST_v10.bin -o build/T02_subs.bin

Input Track 02 must be the user's own v0.10 SUB TEST build (SHA-256 pinned below); its
$8EE5 -> JSR $9C00 scene hook and $65AA -> JSR $76DF raster call are reused. Changes:
  bank $81 $76DF-$76FB  raster helper: sprites on in the lower band while a cue shows
  bank $81 $65D3        raster routine tail -> JMP $7700; $76FC-$76FE flags
  bank $81 $7700-       tail: full 256-px width for the subtitle band during the game's
                        128-px shots (and back for the next band)
  bank $82 $8D44/$8D59  width routines: JSR setn/setf so the helper knows the width
  bank $82 $9C00-$9C13  stub: map bank $83 at $A000, JSR $A000
  bank $83 (8 KiB)      engine + font + this scene's cues (engine.s), was all $FF
Every touched MODE1 sector gets new EDC/ECC. Nothing else changes; no audio track.

Cue times in the TSV are seconds from the cue's CD track INDEX 01. They become frame
numbers counted from the engine's first call: frame = (t - offset) * fps, where offset is
the track time at that first call and fps is the engine clock rate per CD second
(Mednafen 1.32, King Webis T28: 0.228 s and 59.717, see docs/engine-runtime.md). Writes build products only; never commit them (game data).
"""
import argparse, csv, hashlib, json, os, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import xak_iii_disc_utils as core          # noqa: E402
from font_build import Font                # noqa: E402

V10_SHA = '64ef0a47b2beeefc12e6a113a056964e01b67e5b71d201449c699ed5f0bb9e46'
CDRAM_USER = 0xFE800
PREGAP = 225
FPS = 59.8261
# Engine frame clock vs CD audio, fitted from a Mednafen recording of the King Webis scene
# with the engine running (55 cue onsets): the VBlank counter at $2338 runs 0.183% slow
# against the CD clock, and the first engine call is at Track 28 t = 0.228 s.
CLOCK_FPS = 59.7168
CLOCK_OFFSET = 0.228
PALS = (6, 7, 13, 14)                      # sprite palettes unused by the King scene
WHITE = 0x1FF

def raw_off(cdram):
    u = CDRAM_USER + cdram
    return (u // 2048 + PREGAP) * 2352 + 16 + u % 2048

def cpu_to_cdram(cpu):
    assert 0x4000 <= cpu < 0xC000
    return cpu - 0x4000

def put(track, cpu, data, touched):
    c = cpu_to_cdram(cpu)
    for i, b in enumerate(data):
        o = raw_off(c + i)
        track[o] = b
        touched.add(o // 2352)

def get(track, cpu, n):
    c = cpu_to_cdram(cpu)
    return bytes(track[raw_off(c + i)] for i in range(n))

def asm_str(s):
    out = []
    for ch in s:
        if not (0x20 <= ord(ch) < 0x80):
            ch = {'\u2026': '...', '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"', '\u2014': '-', '\u2013': '-'}.get(ch, '?')
        out.extend(ord(c) for c in ch)
    return out

def load_cues(tsv, scene, offset, fps, lead=0.0):
    cues = []
    for r in csv.DictReader(open(tsv, encoding='utf-8'), delimiter='\t'):
        if r['scene_id'] != scene or not r['start'].strip() or not r['end'].strip():
            continue
        t0, t1 = float(r['start']) - lead, float(r['end'])
        f0, f1 = max(0, round((t0 - offset) * fps)), max(1, round((t1 - offset) * fps))
        cues.append(dict(id=r['cue_id'], f0=f0, f1=f1, text=r['en_subtitle'].strip() or '...'))
    cues.sort(key=lambda c: c['f0'])
    for a, b in zip(cues, cues[1:]):            # no overlap: engine shows one cue at a time
        if a['f1'] > b['f0']:
            a['f1'] = max(a['f0'] + 1, b['f0'])
    return cues

def gen_inc(cues, font, blk_y, y1, y2):
    L = [f'NCUES = {len(cues)}', f'BLK_Y = {blk_y}', f'LINE1_Y = {y1}', f'LINE2_Y = {y2}',
         '        .segment "ENGINE"']
    L.append('cue_start: .word ' + ','.join(str(c['f0']) for c in cues) if cues else 'cue_start:')
    L.append('cue_end:   .word ' + ','.join(str(c['f1']) for c in cues) if cues else 'cue_end:')
    L.append('cue_text:  .word ' + ','.join(f'txt{i}' for i in range(len(cues))) if cues else 'cue_text:')
    for i, c in enumerate(cues):
        L.append(f'txt{i}: .byte ' + ','.join(str(b) for b in asm_str(c['text']) + [0]) + f' ; {c["id"]}')
    L.append('font_widths: .byte ' + ','.join(str(font.adv.get(chr(0x20 + i), 0)) for i in range(96)))
    L.append('glyph_lo: .byte ' + ','.join(f'<(font_rows+{i*12})' for i in range(96)))
    L.append('glyph_hi: .byte ' + ','.join(f'>(font_rows+{i*12})' for i in range(96)))
    L.append('font_rows:')
    for i in range(96):
        rows = font.bits.get(chr(0x20 + i), [[False] * 8] * 12)
        L.append('  .byte ' + ','.join(f'${sum(0x80 >> x for x in range(8) if r[x]):02X}' for r in rows))
    L.append('pal_ids: .byte ' + ','.join(str(p) for p in PALS))
    L.append('pal_data:')
    for k in range(4):
        cols = [WHITE if (c >> k) & 1 else 0 for c in range(16)]
        L.append('  .word ' + ','.join(f'${c:03X}' for c in cols))
    return '\n'.join(L) + '\n'

def build_bank83(inc, workdir):
    open(os.path.join(workdir, 'data.inc'), 'w').write(inc)
    subprocess.run(['ca65', '--cpu', 'huc6280', '-I', workdir, '-o', f'{workdir}/engine.o', f'{HERE}/engine.s'], check=True)
    subprocess.run(['ld65', '-C', f'{HERE}/engine.cfg', '-o', f'{workdir}/bank83.bin', '-m', f'{workdir}/engine.map',
                    '-Ln', f'{workdir}/engine.lbl', f'{workdir}/engine.o'], check=True)
    subprocess.run(['ca65', '--cpu', 'huc6280', '-o', f'{workdir}/hooks.o', f'{HERE}/hooks.s'], check=True)
    subprocess.run(['ld65', '-C', f'{HERE}/hooks.cfg', '-o', f'{workdir}/hooks', f'{workdir}/hooks.o'], check=True)
    b83 = open(f'{workdir}/bank83.bin', 'rb').read()
    assert len(b83) == 8192 and b83[3] == 0xFF, 'initf must be $FF'
    hooks = {0x76DF: 'helper', 0x65D3: 'tpatch', 0x7700: 'helper2', 0x8D44: 'npatch', 0x8D59: 'fpatch', 0x9C00: 'stub'}
    return b83, {a: open(f'{workdir}/hooks.{n}', 'rb').read() for a, n in hooks.items()}

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tsv', required=True)
    ap.add_argument('--scene', default='VS1')
    ap.add_argument('--track02', required=True)
    ap.add_argument('-o', required=True)
    ap.add_argument('--offset', type=float, default=CLOCK_OFFSET, help='track seconds at the first engine call')
    ap.add_argument('--fps', type=float, default=CLOCK_FPS, help='engine frame clock rate (frames per CD second)')
    ap.add_argument('--lead', type=float, default=0.0, help='show cues this many seconds early')
    ap.add_argument('--blk-y', type=int, default=176)
    ap.add_argument('--y1', type=int, default=184)
    ap.add_argument('--y2', type=int, default=204)
    ap.add_argument('--workdir')
    ns = ap.parse_args()
    track = bytearray(open(ns.track02, 'rb').read())
    sha = hashlib.sha256(track).hexdigest()
    if sha != V10_SHA:
        sys.exit(f'unexpected Track 02 {sha} (need the v0.10 SUB TEST build {V10_SHA})')
    # guards: the bytes we expect at every site
    assert get(track, 0x76DF, 10) == bytes.fromhex('293f1d723e1002094060'), 'raster helper'
    assert get(track, 0x76E9, 0x785F - 0x76E9) == bytes(0x785F - 0x76E9), 'bank $81 $76E9-$785E not free'
    assert get(track, 0x8D44, 4) == get(track, 0x8D59, 4) == bytes.fromhex('a90a85f7'), 'width routines'
    assert get(track, 0x9C00, 6) == bytes.fromhex('48da5aad999c'), 'v0.x hook'
    assert get(track, 0x8EE5, 3) == bytes.fromhex('20009c'), 'scene loop call'
    assert get(track, 0x65AA, 3) == bytes.fromhex('20df76'), 'raster call'
    assert get(track, 0x65D3, 5) == bytes.fromhex('8d030060a6'), 'raster routine tail'
    assert get(track, 0xA000, 8192) == b'\xff' * 8192, 'bank $83 not free'
    cues = load_cues(ns.tsv, ns.scene, ns.offset, ns.fps, ns.lead)
    font = Font()
    for c in cues:
        for line in c['text'].split('|'):
            w = font.width(''.join(chr(b) for b in asm_str(line)))
            if w > 240:
                print(f"WARN {c['id']}: line {line!r} is {w} px (> 240)")
    wd = ns.workdir or tempfile.mkdtemp(prefix='xak3eng_')
    os.makedirs(wd, exist_ok=True)
    b83, hooks = build_bank83(gen_inc(cues, font, ns.blk_y, ns.y1, ns.y2), wd)
    touched = set()
    for a, data in hooks.items():
        put(track, a, data, touched)
    put(track, 0xA000, b83, touched)
    for s in sorted(touched):
        track[s * 2352:(s + 1) * 2352] = core.restore_mode1_sector(bytes(track[s * 2352:(s + 1) * 2352]))
    open(ns.o, 'wb').write(track)
    rep = dict(output=ns.o, sha256=hashlib.sha256(track).hexdigest(), sectors=sorted(touched), cues=len(cues),
               first=cues[0] if cues else None, offset=ns.offset, fps=ns.fps, workdir=wd)
    json.dump(rep, open(ns.o + '.json', 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'first'}, indent=1))

if __name__ == '__main__':
    main()
