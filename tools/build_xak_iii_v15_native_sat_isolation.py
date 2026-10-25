#!/usr/bin/env python3
"""Xak III v0.15: reversible saved-state SAT sprite leakage isolation.

Uses one user-owned Geargrafx v44 saved state at an *actual* v0.14 Slot4
native-sprite glitch frame. Creates four new saves in a unique v0.15 namespace:
  Slot2 reference (unchanged)
  Slot3 suppress only native sprites wholly outside intended art y[50,178)
  Slot4 suppress any native sprite overlapping upper/lower letterbox
  Slot5 suppress native sprites extending into lower letterbox only

Both live SAT and its VDC VRAM shadow are changed, and *only* at selected
native SAT Y words. Subtitle glyph entries are protected. The game may
immediately rebuild SAT and undo this probe. No game BIN/audio changes.
Do NOT treat the aggressive Slot4 comparison as a production clipping fix.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

STATE_LEN = 749238
VDC_VRAM = 0x48C67
VDC_REGS = VDC_VRAM + 65536 + 4
VDC_SAT = VDC_REGS + 40
CPU_RAM = 13+8+32768+4
EXPECTED_HELPER = bytes.fromhex('29 3F 1D 72 3E EA EA 09 40 60')
EXPECTED_X = bytes.fromhex('50 60 50 60')
EXPECTED_FONT = bytes.fromhex('76 70 72 74')
TRACK = 'Xak_III_English_Track02_SUB_TEST_v10.bin'
CUE = 'Xak_III_English_SUB_TEST_v15_Pilot01.cue'
STEM = 'Xak_III_English_SUB_TEST_v15_Pilot01.state'
REPORT = 'Xak_III_v15_Native_SAT_Isolation_Report.json'
PICTURE_TOP = 50
PICTURE_BOTTOM = 178
HEIGHTS = (16,32,64,64)
WIDTHS = (16,32)
SUBTITLE_PATTERNS = {0x76,0x70,0x72,0x74}
SLOT_MODES = {2:'reference',3:'fully_outside',4:'touching_both',5:'touching_bottom'}

def sha(b):return hashlib.sha256(b).hexdigest()

def cpu(a):
    if not (0x4000<=a<0xC000):raise ValueError('CPU address outside mapped code RAM')
    return CPU_RAM+a-0x4000

def validate(b):
    if len(b)!=STATE_LEN or struct.unpack_from('<III',b,STATE_LEN-200)!=(0x82190619,44,STATE_LEN):
        raise ValueError('Expected 749238-byte Geargrafx 1.8.4 native v44 state')
    if b[cpu(0x65AA):cpu(0x65AA)+5]!=bytes.fromhex('20 DF 76 EA EA'):
        raise ValueError('Wrong source patch: missing v0.11/v0.14 native raster hook')
    if b[cpu(0x76DF):cpu(0x76DF)+10]!=EXPECTED_HELPER:
        raise ValueError('Wrong source patch: missing v0.11/v0.14 black-band raster helper')
    if b[cpu(0x9CA2):cpu(0x9CA2)+4]!=EXPECTED_X:
        raise ValueError('Expected v0.14 Slot4 X correction -64; do not use Slot2/3/5')
    if b[cpu(0x9CAA):cpu(0x9CAA)+4]!=EXPECTED_FONT:
        raise ValueError('Original stable glyph pattern refs are missing')
    if struct.unpack_from('<H',b,VDC_REGS+2*19)[0]!=0x0C00:
        raise ValueError('Unexpected SATB DMA source; abort rather than patch wrong VRAM')

def sat(b):
    entries=[]
    for i in range(64):
        y,x,pat,flags=struct.unpack_from('<4H',b,VDC_SAT+8*i)
        if (y|x|pat|flags)==0:continue
        height=HEIGHTS[(flags>>12)&3]
        width=WIDTHS[(flags>>8)&1]
        sub=(pat in SUBTITLE_PATTERNS and flags&0x0F==15 and height==16)
        entries.append(dict(index=i,y=(y&0x03ff)-64,x=(x&0x03ff)-32,
                            width=width,height=height,pattern=pat,flags=flags,subtitle=sub))
    return entries

def should_mask(e,mode):
    if e['subtitle']:return False
    top=e['y'];bottom=top+e['height']
    if mode=='fully_outside':return bottom<=PICTURE_TOP or top>=PICTURE_BOTTOM
    if mode=='touching_both':return top<PICTURE_TOP or bottom>PICTURE_BOTTOM
    if mode=='touching_bottom':return bottom>PICTURE_BOTTOM
    if mode=='reference':return False
    raise ValueError('Unknown mask mode')

def build_states(source):
    validate(source)
    entries=sat(source)
    native=[e for e in entries if not e['subtitle']]
    if not native:
        raise ValueError('No native SAT sprites in source checkpoint. Capture a state during an actual glitch frame.')
    outputs={}
    report={'source_sha256':sha(source),'source_SAT_sprites':entries,
            'visible_picture_bounds':[PICTURE_TOP,PICTURE_BOTTOM],
            'status':'STATIC SAT ISOLATION; REAL GEARGRAFX TEST REQUIRED',
            'warning':'A native scene redraw can overwrite live/shadow SAT immediately; the test may be transient.',
            'variants':{}}
    satb=VDC_VRAM+0x0c00*2
    for slot,mode in SLOT_MODES.items():
        result=bytearray(source)
        masked=[]
        expected=set()
        for e in entries:
            if not should_mask(e,mode):continue
            i=e['index']
            for off in (VDC_SAT+8*i,satb+8*i):
                struct.pack_into('<H',result,off,0x03ff)
                expected.update((off,off+1))
            masked.append(i)
        changed={k for k,(a,b) in enumerate(zip(source,result)) if a!=b}
        if not changed.issubset(expected):
            raise AssertionError('Modified bytes beyond approved SAT Y words')
        for e in entries:
            if e['subtitle']:
                i=e['index']
                if result[VDC_SAT+8*i:VDC_SAT+8*i+8]!=source[VDC_SAT+8*i:VDC_SAT+8*i+8]:
                    raise AssertionError('Subtitle SAT entry was touched')
        if result[:VDC_VRAM]!=source[:VDC_VRAM] or result[-200:]!=source[-200:]:
            raise AssertionError('Resident program code or metadata changed')
        outputs[slot]=bytes(result)
        report['variants'][str(slot)]={'mode':mode,'masked_native_indices':masked,
                                      'changed_state_bytes':len(changed),'sha256':sha(outputs[slot])}
    return outputs,report

def make_cue(raw):
    if raw.count('FILE "'+TRACK+'" BINARY')!=1 or len(re.findall(r'^\s*TRACK\s+\d+',raw,re.M))!=35:
        raise ValueError('Expected split 35-track v0.14 cue reusing v0.10 Track02')
    if not re.search(r'^\s*TRACK\s+28\s+AUDIO\s*$',raw,re.M):
        raise ValueError('Japanese voiced physical Track 28 absent')
    return raw

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--glitch-state',required=True,type=Path,
                    help='Captured during visible glitch using v0.14 Slot4 code X=-64')
    ap.add_argument('--cue',required=True,type=Path,help='Existing v0.14 CUE')
    ap.add_argument('--outdir',required=True,type=Path,help='Existing directory containing v0.10 Track02')
    a=ap.parse_args()
    if not a.outdir.is_dir() or not (a.outdir/TRACK).is_file():
        ap.error('Existing unchanged v0.10 BIN must be present in output directory')
    paths=[a.outdir/CUE]+[a.outdir/(STEM+str(i)) for i in SLOT_MODES]+[a.outdir/REPORT]
    if any(path.exists() for path in paths):ap.error('Refusing to overwrite an existing v0.15 file')
    states,report=build_states(a.glitch_state.read_bytes())
    cue=make_cue(a.cue.read_text(encoding='utf-8-sig'))
    paths[0].write_text(cue,encoding='utf-8',newline='\n')
    for slot in SLOT_MODES:(a.outdir/(STEM+str(slot))).write_bytes(states[slot])
    paths[-1].write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
