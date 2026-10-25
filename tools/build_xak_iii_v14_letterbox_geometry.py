#!/usr/bin/env python3
"""Xak III v0.14: preserve v0.11 letterbox and measure scene-dependent X shift.

Supports exact user-owned Geargrafx v44 v0.11 states from any saved scene.
Creates an independent v0.14 CUE and four 749238-byte states; leaves v0.10
Track02 and all original states untouched. In 'geometry' mode the four states
are identical except for 4 native subtitle X-coordinate bytes.

Optional 'sprite-isolation' mode additionally masks *selected native sprite*
SAT entries only in experimental Slot 4/5. This is a single-checkpoint
experiment: a scene's own SAT rebuild may promptly overwrite the mask.
Never distribute generated native states through public GitHub.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct
from pathlib import Path

SIZE=749238
CDRAM=13+8+32768+4
VRAM=0x48C67
VDC_REGS=VRAM+65536+4
VDC_SAT=VDC_REGS+40
FONT_TABLE_CPU=0x9C9A
X_TABLE_CPU=0x9CA2
FONT_REF_CPU=0x9CAA
HELPER_CPU=0x76DF
CALLSITE_CPU=0x65AA
Y_TABLE=bytes.fromhex('f8 f8 0c 0c 00 00 01 01')
BASE_X=bytes.fromhex('90 a0 90 a0')
HELPER=bytes.fromhex('29 3f 1d 72 3e ea ea 09 40 60')
NATIVE_SPRITE_PATTERNS={0x76,0x70,0x72,0x74}
CUE_NAME='Xak_III_English_SUB_TEST_v14_Pilot01.cue'
STEM='Xak_III_English_SUB_TEST_v14_Pilot01.state'
REPORT='Xak_III_v14_Letterbox_Geometry_Report.json'
V11_TRACK='Xak_III_English_Track02_SUB_TEST_v10.bin'

def digest(data):return hashlib.sha256(data).hexdigest()
def cpu(a):
    if not 0x4000<=a<0xC000:raise ValueError('outside bank80..83 CD RAM')
    return CDRAM+a-0x4000

def sat_info(b):
    reg=struct.unpack_from('<20H',b,VDC_REGS)
    if reg[19]!=0x0C00:raise ValueError('unexpected SATB source')
    out=[]
    for i in range(64):
        y,x,pattern,flags=struct.unpack_from('<4H',b,VDC_SAT+8*i)
        if not (y|x|pattern|flags):continue
        h=(16,32,64,64)[(flags>>12)&3]
        w=(16,32)[(flags>>8)&1]
        is_sub=(pattern in NATIVE_SPRITE_PATTERNS and flags&0x0F==15 and h==16)
        out.append(dict(index=i,x=x-32,y=y-64,width=w,height=h,pattern=pattern,
                        flags=flags,is_subtitle=is_sub))
    return out

def validate(b):
    if len(b)!=SIZE or struct.unpack_from('<III',b,SIZE-200)!=(0x82190619,44,SIZE):
        raise ValueError('expected 749238-byte Geargrafx v44 state')
    if b[cpu(CALLSITE_CPU):cpu(CALLSITE_CPU)+5]!=bytes.fromhex('20 df 76 ea ea'):
        raise ValueError('v0.11 raster callsite is missing')
    if b[cpu(HELPER_CPU):cpu(HELPER_CPU)+10]!=HELPER:
        raise ValueError('v0.11 temporary black-band sprite branch is missing')
    if b[cpu(FONT_TABLE_CPU):cpu(FONT_TABLE_CPU)+8]!=Y_TABLE:
        raise ValueError('v0.11 two-row subtitle Y positions are missing')
    if b[cpu(X_TABLE_CPU):cpu(X_TABLE_CPU)+4]!=BASE_X:
        raise ValueError('v0.11 reference subtitle X values changed')
    if b[cpu(FONT_REF_CPU):cpu(FONT_REF_CPU)+4]!=bytes.fromhex('76 70 72 74'):
        raise ValueError('v0.11 font PAT indices do not match')
    if struct.unpack_from('<20H',b,VDC_REGS)[9]!=0x50:
        raise ValueError('unexpected VDC MWR')
    return True

def shift_coordinates(b, shift):
    validate(b)
    if shift not in (0,-48,-64,-80):
        raise ValueError('unsupported shift, preserve bounded diagnostics')
    dst=bytearray(b)
    values=bytes(n+shift for n in BASE_X)
    dst[cpu(X_TABLE_CPU):cpu(X_TABLE_CPU)+4]=values
    return dst

def native_masks(b,kind):
    """One-frame diagnostic SAT masking. Never edits subtitle sprite indices.

    outside: native sprites wholly outside the sampled picture y[50,178)
    touching: native sprites that touch any black upper/lower band, more
              invasive and may remove otherwise visible game art.
    """
    if kind not in ('outside','touching'):raise ValueError('unexpected cull kind')
    reports=sat_info(b)
    covered=[]
    for s in reports:
        if s['is_subtitle']:continue
        y,h=s['y'],s['height']
        if kind=='outside': cull=(y+h<=50 or y>=178)
        else:cull=(y<50 or y+h>178)
        if cull:
            i=s['index']
            for off in (VDC_SAT+8*i,VRAM+0x0C00*2+8*i):
                struct.pack_into('<H',b,off,0x03ff)
            covered.append(i)
    return covered

def make_variants(source:bytes,mode='geometry'):
    validate(source)
    if mode=='geometry':
        configs=[(2,0,None),(3,-48,None),(4,-64,None),(5,-80,None)]
    elif mode=='sprite-isolation':
        configs=[(2,0,None),(3,-64,None),(4,-64,'outside'),(5,-64,'touching')]
    else:raise ValueError('unknown mode')
    output=[]
    for slot,shift,mask in configs:
        copy=shift_coordinates(source,shift)
        masked=[]
        if mask:
            masked=native_masks(copy,mask)
        data=bytes(copy)
        changes=[i for i,(a,b) in enumerate(zip(source,data)) if a!=b]
        safe={cpu(X_TABLE_CPU)+j for j in range(4)}
        if mask:
            for index in masked:
                safe.update(range(VDC_SAT+8*index,VDC_SAT+8*index+2))
                safe.update(range(VRAM+0x1800+8*index,VRAM+0x1800+8*index+2))
        if set(changes)-safe or data[:CDRAM]!=source[:CDRAM] or data[-200:]!=source[-200:]:
            raise AssertionError('Unexpected game state edit outside native subtitle X / SAT Y')
        output.append((slot,data,dict(slot=slot,shift_x=shift,mask_type=mask,
                                     masked_native_sat_indices=masked,
                                     changed_bytes=len(changes),
                                     sha256=digest(data))))
    return output

def make_cue(cue):
    if len(re.findall(r'^\s*TRACK\s+\d+',cue,re.M))!=35 or not re.search(r'^\s*TRACK\s+28\s+AUDIO\s*$',cue,re.M):
        raise ValueError('expected original 35-track CUE with audio Track28')
    if cue.count('FILE "'+V11_TRACK+'" BINARY')!=1:
        raise ValueError('expected unchanged existing v0.10 Track02 BIN reference')
    return cue

def build(state:Path,cue:Path,root:Path,mode,tag='v14'):
    if not (root/V11_TRACK).is_file():
        raise ValueError('v0.10 Track02 BIN must be present beside new output')
    if not root.is_dir():raise ValueError('output folder must exist')
    if tag not in ('v14','v14clip','v14leaks'):
        raise ValueError('tag must be v14, v14clip or v14leaks')
    cue_name=CUE_NAME.replace('v14',tag)
    state_stem=STEM.replace('v14',tag)
    report_name=REPORT.replace('v14',tag)
    paths=[root/cue_name]+[root/(state_stem+str(i)) for i in (2,3,4,5)]+[root/report_name]
    if any(path.exists() for path in paths):raise FileExistsError('refusing to overwrite v0.14 files')
    raw=state.read_bytes();result=make_variants(raw,mode)
    cue_text=make_cue(cue.read_text(encoding='utf-8-sig'))
    infos=sat_info(raw)
    report=dict(title='Xak III v0.14 — v0.11 black-band preservation / 4:3 centering test',
                status='OFFLINE VALIDATION ONLY, REAL GEARGRAFX TEST PENDING',mode=mode,
                source_state=state.name,source_state_sha256=digest(raw),
                observed_screen_shift_pixels=64,
                native_SAT_snapshot=infos,
                results=[row[2] for row in result],
                data_and_audio_modified=False,
                warning=('Geometry variants are intentionally off-center during some scenes; '
                         'the SAT masks are SINGLE-CHECKPOINT diagnostics and native sprite '
                         'writes may overwrite them. Do not assume they persist or are final fixes.'))
    paths[0].write_text(cue_text,encoding='utf-8',newline='\n')
    for dest,row in zip(paths[1:5],result):dest.write_bytes(row[1])
    paths[-1].write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state',type=Path,required=True,help='Geargrafx v0.11 save made at the relevant cinematic frame')
    p.add_argument('--cue',type=Path,required=True,help='v0.11 CUE from your existing game folder')
    p.add_argument('--outdir',type=Path,required=True,help='Existing folder with original v0.10 BIN and CD audio')
    p.add_argument('--mode',choices=('geometry','sprite-isolation'),default='geometry')
    p.add_argument('--tag',choices=('v14','v14clip','v14leaks'),default='v14',help='Use v14clip for later per-scene tests without overwriting prebuilt v14 files')
    args=p.parse_args()
    print(json.dumps(build(args.state,args.cue,args.outdir,args.mode,args.tag),indent=2))

if __name__=='__main__':main()
