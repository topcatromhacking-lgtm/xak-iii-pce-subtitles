#!/usr/bin/env python3
"""Xak III v0.7 — test background-tile subtitles in the King Wavis scene.

A transient SAVESTATE-ONLY experimental overlay. Requires user's own pinned
v0.5 King-speaking state5; makes a separate state4 for same v0.5 CUE.
NEVER edits the game's BIN/CUE, audio or existing saved states.

This tests whether VDC1 background (BAT+8x8 tile) output can appear while our
v0.5 native SPRITES are invisible, without the repeated sprite-font writes
which caused v0.3 corruption.

WARNING: This is NOT a timed subtitle patch. The screenshot stored in the state
is intentionally not changed; only observe Geargrafx after loading and advancing
frames. Later gameplay may overwrite or retain our temporary BAT/tile writes.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path

SOURCE_HASH = '63a2ea5434314c0303b9c5fb5266962de76c0c260cd093d7f649a760036cc694'
SIZE=749238
HEADER=200
VDC1=0x48C67
VCE=VDC1-1059
VRAM_WORDS=32768
MWR=0x0050
SCREEN_WIDTH_TILES=64
ROWS=(18,21,24,27)
COL=12
TEXT='SUB TEST'
FONT_IDS={'S':2025,'U':2026,'B':2027,'T':2028,'E':2029}
# hand-defined 5x7 uppercase font; no external assets
FONT5={
 'S':('01110','10001','10000','01110','00001','10001','01110'),
 'U':('10001','10001','10001','10001','10001','10001','01110'),
 'B':('11110','10001','10001','11110','10001','10001','11110'),
 'T':('11111','00100','00100','00100','00100','00100','00100'),
 'E':('11111','10000','10000','11110','10000','10000','11111'),
}

def digest(b): return hashlib.sha256(b).hexdigest()

def tile_words(ch):
    # BG 8x8 pixels, 4 planes: 0-1 in words +0..7, 2-3 in +8..15.
    # Color 15 mapped to white via existing BG palette 7 color 15.
    out=[0]*16
    for j,row in enumerate(FONT5[ch]):
        mask=sum(1<<(6-i) for i,v in enumerate(row) if v=='1')
        v=mask|(mask<<8)
        out[j]=v
        out[j+8]=v
    return out

def verify(state:bytes, *, require_pinned=True):
    if len(state)!=SIZE or struct.unpack_from('<III',state,len(state)-HEADER)!=(0x82190619,44,len(state)):
        raise ValueError('Not the expected native Geargrafx 1.8.4 v44 state')
    if require_pinned and digest(state)!=SOURCE_HASH:
        raise ValueError('Wrong v0.5 early King state5; SHA-256 mismatch')
    regs=struct.unpack_from('<20H',state,VDC1+65536+4)
    if regs[5]!=0x00CC or regs[9]!=MWR or regs[11]!=0x041F:
        raise ValueError('Wrong VDC1 scene display configuration')
    palette=struct.unpack_from('<512H',state,VCE+11)
    if tuple(palette[7*16:7*16+16])!=tuple([0]*15+[0x01FF]):
        raise ValueError('BG palette7 is not expected black/white')
    if len(set(FONT_IDS.values()))!=len(FONT_IDS):
        raise AssertionError('Duplicate font tile ids')
    referenced={struct.unpack_from('<H',state,VDC1+2*i)[0]&0x7ff for i in range(4096)}
    for ch,tile in FONT_IDS.items():
        off=VDC1+tile*32
        if any(state[off:off+32]) or tile in referenced:
            raise ValueError(f'Reserved BG tile {tile} is not empty and unreferenced')
    if any((row*SCREEN_WIDTH_TILES+COL+len(TEXT))>4096 for row in ROWS):
        raise ValueError('Proposed BAT overlay exceeds table')
    return regs

def patch_state(state:bytes, *, require_pinned=True):
    verify(state,require_pinned=require_pinned)
    out=bytearray(state)
    changed=set()
    def write(off, bs):
        if off< VDC1 or off+len(bs)>VDC1+65536:
            raise AssertionError('VRAM-only patch violated')
        for i,v in enumerate(bs):
            if out[off+i]!=v: changed.add(off+i)
            out[off+i]=v
    for ch,t in FONT_IDS.items():
        write(VDC1+t*32,struct.pack('<16H',*tile_words(ch)))
    # Candidate BAT positions: four separate scanline bands; all y <= 223
    # are visible in a 224-line frame if scroll/background presentation maps
    # the BAT row directly. Raster BYR switching can change that mapping.
    for row in ROWS:
        for j,ch in enumerate(TEXT):
            old=struct.unpack_from('<H',state,VDC1+2*(row*SCREEN_WIDTH_TILES+COL+j))[0]
            if ch==' ':
                # Render a black space, do not change original tile contents.
                # Pixel background may not be black in every scene phase.
                continue
            new=0x7000|FONT_IDS[ch]
            if old!=new:
                write(VDC1+2*(row*SCREEN_WIDTH_TILES+COL+j),struct.pack('<H',new))
    result=bytes(out)
    diffs={i for i,(a,b) in enumerate(zip(state,result)) if a!=b}
    if diffs!=changed or not diffs:
        raise AssertionError('Changed-byte audit failed')
    if any(not (VDC1<=x<VDC1+65536) for x in diffs):
        raise AssertionError('Modified bytes outside VDC1 VRAM')
    if result[-HEADER:]!=state[-HEADER:]:
        raise AssertionError('Save header or stored screenshot changed')
    return result,{'source_sha256':digest(state),'target_sha256':digest(result),
        'changed_bytes':len(changed),'changed_range_min':min(changed),
        'changed_range_max':max(changed),'modified_region':'VDC1 VRAM ONLY',
        'candidate_BAT_rows':list(ROWS),'candidate_BAT_columns':[COL,COL+len(TEXT)-1],
        'background_palette':7,'tile_ids':FONT_IDS,
        'game_bin_modified':False,'cd_audio_modified':False,'existing_states_modified':False,
        'expected_behavior':'Temporary four-row SUB TEST BG probe; requires real Geargrafx test',
        'limitations':'Scroll/raster state may remap or hide BAT rows; original VRAM may be overwritten next frame'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state',type=Path,required=True,help='Original v0.5 Slot 5: first King speech')
    p.add_argument('--out',type=Path,help='New v0.5 Slot 4 file, must not already exist')
    p.add_argument('--report',type=Path,help='New JSON report, must not already exist')
    a=p.parse_args()
    out=a.out or a.state.with_name('Xak_III_English_SUB_TEST_v05_Pilot01.state4')
    rep=a.report or a.state.with_name('Xak_III_v07_BG_State_Probe_Report.json')
    if out.resolve()==a.state.resolve() or len({str(x.resolve()) for x in [a.state,out,rep]})!=3 or out.exists() or rep.exists():
        p.error('Refusing to overwrite source or existing state/report')
    result,report=patch_state(a.state.read_bytes())
    out.write_bytes(result)
    rep.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))
    print('Load under original v0.5 CUE: ',out)

if __name__=='__main__':main()
