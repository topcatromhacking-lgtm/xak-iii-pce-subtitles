#!/usr/bin/env python3
"""Read-only Geargrafx v44 Xak III subtitle-stage comparison.

Supports the verified 749238-byte native v44 state layout only.
Never modifies save states or game files. Saved registers cannot establish
the transient rendering state on earlier raster scanlines.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

SIZE=749238
HEADER=200
VDC1=0x48C67
VCE=VDC1-1059
VPC=VCE-33
REGS=VDC1+65536+4
SAT=REGS+40
LATCHED_CR=SAT+512+63
CDRAM=13+8+32768+4
PATTERNS=(59,56,57,58)
SAT2=(0x76,0x70,0x72,0x74)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    data=Path(path).read_bytes()
    if len(data)!=SIZE or struct.unpack_from('<III',data,len(data)-HEADER)!=(0x82190619,44,len(data)):
        raise ValueError('Expect a native 749238-byte Geargrafx 1.8.4/v44 state')
    h=len(data)-HEADER
    size=struct.unpack_from('<I',data,h+156)[0]
    width,height=struct.unpack_from('<HH',data,h+160)
    if (size,width,height)!=(256*240*4,256,240):
        raise ValueError('Unexpected save-state screen format')
    if struct.unpack_from('<I',data,13+8+32768)[0]!=65536:
        raise ValueError('Unexpected saved CD-ROM RAM size')
    regs=struct.unpack_from('<20H',data,REGS)
    sat=struct.unpack_from('<256H',data,SAT)
    sprites=[sat[i:i+4] for i in range(0,256,4)]
    subtitle=[[i for i,r in enumerate(sprites)
               if tuple(r)==(192,x,pat,0x8F)]
              for x,pat in zip((64,80,96,112),SAT2)]
    glyphs={}
    for p in PATTERNS:
        bitmap=data[VDC1+p*128:VDC1+(p+1)*128]
        glyphs[str(p)]={'sha256':digest(bitmap),'nonzero_bytes':sum(v!=0 for v in bitmap)}
    word=lambda offset:struct.unpack_from('<H',data,offset)[0]
    return {
        'filename':Path(path).name,'sha256':digest(data),
        'mpr':[f'{v:02X}' for v in data[13:21]],
        'bank82_loaded_hook_flag_9C99':f'{data[CDRAM+0x5C99]:02X}',
        'vdc1':{
            'CR':f'{regs[5]:04X}',
            'latched_CR_at_save_instant':f'{word(LATCHED_CR):04X}',
            'RCR':f'{regs[6]:04X}','HDR':f'{regs[11]:04X}',
            'MWR':f'{regs[9]:04X}','DVSSR':f'{regs[19]:04X}',
            'live_sat_entries':sum(any(r) for r in sprites),
            'subtitle_sat_indices':subtitle},
        'vdc2_CR':f'{word(VDC1+68401+65536+4+5*2):04X}',
        'vpc_huc6202_sha256':digest(data[VPC:VPC+33]),
        'vce_sprite_palette_15_color_15':f'{word(VCE+11+511*2):04X}',
        'patterns':glyphs}

def compare(a,b):
    return {
        'early':a,'later':b,
        'same_saved_CR':a['vdc1']['CR']==b['vdc1']['CR'],
        'same_latched_CR_at_save':a['vdc1']['latched_CR_at_save_instant']==b['vdc1']['latched_CR_at_save_instant'],
        'same_saved_HDR':a['vdc1']['HDR']==b['vdc1']['HDR'],
        'same_VPC_snapshot':a['vpc_huc6202_sha256']==b['vpc_huc6202_sha256'],
        'same_glyph_bitmaps':{str(p):a['patterns'][str(p)]['sha256']==b['patterns'][str(p)]['sha256'] for p in PATTERNS},
        'limitation':'Save-state snapshots cannot reveal per-line raster VDC writes, SAT timing, or video priority during the previous frame.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--early',type=Path,required=True)
    parser.add_argument('--later',type=Path,required=True)
    parser.add_argument('--out',type=Path,help='New JSON file only (never overwrites)')
    args=parser.parse_args()
    text=json.dumps(compare(read(args.early),read(args.later)),indent=2)+'\n'
    if args.out:
        with args.out.open('x',encoding='utf-8') as f:f.write(text)
    else:
        print(text,end='')

if __name__=='__main__':
    main()
