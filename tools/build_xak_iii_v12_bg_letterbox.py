#!/usr/bin/env python3
"""Xak III v0.12 A/B: test BG-only in letterboxed raster bands.

Creates two new v44 Geargrafx states from the exact pinned v0.9 King-state
source. No game BIN, CUE, audio, or original savestate is modified.

A slot2: BG enabled / sprites disabled in previously blank raster bands.
B slot3: same, additionally injects small SUB TEST BG tiles in candidate BAT
         rows. This is diagnostic, NOT final subtitle rendering. BG may expose
         native scene graphics in letterboxed regions. Stop on corruption.
"""
from __future__ import annotations
import argparse, hashlib, json, re, struct
from pathlib import Path

SRC_SHA='8b40e7d95c5cfc6ec57eeffa00f58058a3b6692c055469e56d579a1bbd5c5fb2'
SRC_STATE='Xak_III_English_SUB_TEST_v09_Pilot01.state2'
NAME='Xak_III_English_SUB_TEST_v12_Pilot01'
REPORT='Xak_III_v12_BG_Letterbox_Report.json'
V05_TRACK='Xak_III_English_Track02_SUB_TEST_v05.bin'
V10_TRACK='Xak_III_English_Track02_SUB_TEST_v10.bin'
SIZE=749238; HEADER=200
RAM=13+8+32768+4
VDC=0x48C67; VCE=VDC-1059
FONT_IDS={'S':2025,'U':2026,'B':2027,'T':2028,'E':2029}
FONT5={
 'S':('01110','10001','10000','01110','00001','10001','01110'),
 'U':('10001','10001','10001','10001','10001','10001','01110'),
 'B':('11110','10001','10001','11110','10001','10001','11110'),
 'T':('11111','00100','00100','00100','00100','00100','00100'),
 'E':('11111','10000','10000','11110','10000','10000','11111')}
ROWS=(18,21,24,27,30,33) # candidate only; not per-scene calibrated
COLUMN=12
TEXT='SUB TEST'
OLD=bytes.fromhex('29 3F 1D 72 3E 10 02 09 40 60')
# AND #$3F ; ORA $3E72,X ; BMI +3 ; ORA #$80 ; RTS ; ORA #$40 ; RTS
# BG-native on: BG+SPR on. Blank native: BG only, SPR off.
NEW=bytes.fromhex('29 3F 1D 72 3E 30 03 09 80 60 09 40 60')

def sha(b): return hashlib.sha256(b).hexdigest()
def cpu(adr):
 if not 0x4000<=adr<0xC000:raise ValueError('CPU address out of bank range')
 return RAM+adr-0x4000

def verify(s):
 if len(s)!=SIZE or sha(s)!=SRC_SHA or struct.unpack_from('<III',s,SIZE-HEADER)!=(0x82190619,44,SIZE):
  raise ValueError('Use the exact pinned v0.9 early King Slot2')
 if s[cpu(0x76DF):cpu(0x76DF)+len(OLD)]!=OLD or any(s[cpu(0x76DF)+len(OLD):cpu(0x76DF)+len(NEW)]):
  raise ValueError('Unexpected raster helper code / occupied tail')
 if s[cpu(0x65AA):cpu(0x65AF)]!=bytes.fromhex('20 DF 76 EA EA'):
  raise ValueError('Missing v0.9 native raster hook')
 regs=struct.unpack_from('<20H',s,VDC+65536+4)
 if regs[5]!=0x00CC or regs[9]!=0x0050 or regs[11]!=0x041F:
  raise ValueError('VDC1 mode mismatch')
 palette=struct.unpack_from('<512H',s,VCE+11)
 if tuple(palette[7*16:7*16+16])!=tuple([0]*15+[0x01FF]):
  raise ValueError('Expected BG palette7 black/white not found')
 referenced={struct.unpack_from('<H',s,VDC+2*i)[0]&0x7ff for i in range(4096)}
 for tile in FONT_IDS.values():
  if any(s[VDC+tile*32:VDC+tile*32+32]) or tile in referenced:
   raise ValueError('BG tile slot collision at '+str(tile))

def glyph(ch):
 result=[0]*16
 for row,chars in enumerate(FONT5[ch]):
  mask=sum((1<<(6-i)) for i,c in enumerate(chars) if c=='1')
  result[row]=result[row+8]=mask|(mask<<8)
 return struct.pack('<16H',*result)

def prepare(s, bg_text):
 verify(s)
 b=bytearray(s)
 b[cpu(0x76DF):cpu(0x76DF)+len(NEW)]=NEW
 if bg_text:
  for ch,tile in FONT_IDS.items():
   b[VDC+tile*32:VDC+tile*32+32]=glyph(ch)
  for row in ROWS:
   for n,ch in enumerate(TEXT):
    if ch!=' ':
     struct.pack_into('<H',b,VDC+2*(row*64+COLUMN+n),0x7000|FONT_IDS[ch])
 result=bytes(b)
 diff=[i for i,(x,y) in enumerate(zip(s,result)) if x!=y]
 allowed=set(range(cpu(0x76DF),cpu(0x76DF)+len(NEW)))
 if bg_text:allowed.update(range(VDC,VDC+65536))
 if any(i not in allowed for i in diff) or result[-HEADER:]!=s[-HEADER:]:
  raise AssertionError('Unexpected changed-byte range')
 if not bg_text and any(i>=VDC for i in diff):
  raise AssertionError('Pure raster test changed video RAM')
 return result, {'slot':3 if bg_text else 2, 'bg_test_tiles':bg_text,
                 'source_sha256':sha(s),'output_sha256':sha(result),
                 'changed_bytes':len(diff),
                 'changed_regions':'CD RAM helper and candidate VDC1 VRAM BAT tiles' if bg_text else 'CD RAM helper only'}

def cue(src):
 old='FILE "'+V05_TRACK+'" BINARY'
 if src.count(old)!=1 or len(re.findall(r'^\s*TRACK\s+\d+',src,re.M))!=35:
  raise ValueError('v0.9 35-track CUE mismatch')
 if not re.search(r'^\s*TRACK\s+28\s+AUDIO\s*$',src,re.M):
  raise ValueError('Japanese Track 28 absent')
 return src.replace(old,'FILE "'+V10_TRACK+'" BINARY')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--state',required=True,type=Path)
 p.add_argument('--cue',required=True,type=Path)
 p.add_argument('--outdir',required=True,type=Path)
 a=p.parse_args()
 if not a.outdir.is_dir() or not (a.outdir/V10_TRACK).exists():
  p.error('v0.10 BIN missing from the target folder')
 outputs=[a.outdir/(NAME+'.cue'),a.outdir/(NAME+'.state2'),a.outdir/(NAME+'.state3'),a.outdir/REPORT]
 if any(x.exists() for x in outputs):p.error('Refusing to overwrite existing v0.12 files')
 s=a.state.read_bytes();A,ra=prepare(s,False);B,rb=prepare(s,True)
 c=cue(a.cue.read_text(encoding='utf-8-sig'))
 outputs[0].write_text(c,encoding='utf8',newline='\n')
 outputs[1].write_bytes(A); outputs[2].write_bytes(B)
 summary={'status':'OFFLINE VALIDATED / EMULATOR TEST PENDING',
          'objective':'Check whether BG-only letterbox preserves native sprite masking and enables BG text',
          'source':'Exact pinned v0.9 Slot2', 'states':[ra,rb],
          'tested_raster_truth_table':{
            'native_BG_only_$80':'$CC BG+SPR',
            'native_black_$00':'$8C BG only, SPR suppressed',
            'native_BG_SPR_$C0':'$CC BG+SPR'},
          'risk':'Native BG picture may extend into black bands; candidate tiles may damage artwork; diagnostic only',
          'all_original_disc_and_audio_files_unchanged':True}
 outputs[3].write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
