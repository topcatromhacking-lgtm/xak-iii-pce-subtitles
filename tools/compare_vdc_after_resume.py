#!/usr/bin/env python3
"""Read-only Geargrafx v44 VDC comparison after resuming a subtitle test state.

Compares the experimental slot 3 before runtime with a fresh slot 4 saved
after gameplay resumes. Emits only status/byte counts, never raw game memory.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

VDC_VRAM=0x48C67
VDC_REGS=VDC_VRAM+0x10000+4
VDC_SAT=VDC_REGS+40
PATTERNS=[504,505,506,507,30,31,43,56]


def hash_data(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    data=path.read_bytes()
    if len(data)<VDC_SAT+512+200:
        raise ValueError('Too short for Geargrafx v44 state')
    tail=len(data)-200
    if struct.unpack_from('<III',data,tail)!=(0x82190619,44,len(data)):
        raise ValueError('Geargrafx v44 native file header mismatch')
    regs=struct.unpack_from('<20H',data,VDC_REGS)
    if regs[19]>=0x7f00:
        raise ValueError('SAT DMA source points outside VRAM')
    shadow=VDC_VRAM+regs[19]*2
    if shadow+512>VDC_VRAM+0x10000:
        raise ValueError('SAT shadow outside VRAM')
    return {
        'data':data, 'regs':regs, 'shadow_offset':shadow,
        'live':data[VDC_SAT:VDC_SAT+512],
        'auto':data[shadow:shadow+512],
        'glyphs':[data[VDC_VRAM+p*128:VDC_VRAM+(p+1)*128] for p in PATTERNS],
    }


def compare(before,after):
    a=load(before)
    b=load(after)
    diffs=lambda x,y:sum(i!=j for i,j in zip(x,y))
    nonzero=lambda parts:[sum(x!=0 for x in y) for y in parts]
    report={
        'before':before.name, 'after':after.name,
        'before_sha256':hash_data(a['data']),
        'after_sha256':hash_data(b['data']),
        'same_disc_CRC':a['data'][1:5]==b['data'][1:5],
        'VDC_CR':{'before':f'{a["regs"][5]:04X}','after':f'{b["regs"][5]:04X}'},
        'VDC_DCR':{'before':f'{a["regs"][15]:04X}','after':f'{b["regs"][15]:04X}'},
        'VDC_DVSSR':{'before':f'{a["regs"][19]:04X}','after':f'{b["regs"][19]:04X}'},
        'video_sprites_enabled_after':bool(b['regs'][5]&0x40),
        'live_SAT_different_bytes':diffs(a['live'],b['live']),
        'live_SAT_nonzero_bytes_after':sum(x!=0 for x in b['live']),
        'live_SAT_first_8_entries_unchanged':a['live'][:64]==b['live'][:64],
        'automatic_SAT_source_moved':a['shadow_offset']!=b['shadow_offset'],
        'automatic_SAT_source_different_bytes':diffs(a['auto'],b['auto']),
        'automatic_SAT_source_nonzero_bytes_after':sum(x!=0 for x in b['auto']),
        'automatic_SAT_first_8_entries_unchanged':a['auto'][:64]==b['auto'][:64],
        'font_pattern_ids':PATTERNS,
        'font_patterns_changed':[
            {'index':i,'changed_bytes':diffs(x,y)}
            for i,(x,y) in enumerate(zip(a['glyphs'],b['glyphs'])) if x!=y
        ],
        'font_pattern_nonzero_bytes_after':nonzero(b['glyphs']),
        'caution':'Static snapshots only: exact modifying instructions remain unknown.',
    }
    report['candidate_reason']=(
        'Sprite-enable register is now off' if not report['video_sprites_enabled_after'] else
        'Sprite entries were replaced' if not report['live_SAT_first_8_entries_unchanged'] else
        'Font glyph VRAM was replaced' if report['font_patterns_changed'] else
        'SAT and glyph bytes survive; inspect actual sprite/scanline renderer'
    )
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before',type=Path,required=True)
    parser.add_argument('--after',type=Path,required=True)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.out and (
        args.out.exists() or
        args.out.resolve() in (args.before.resolve(),args.after.resolve())
    ):
        parser.error('Refusing to overwrite any file')
    result=json.dumps(compare(args.before,args.after),indent=2)+'\n'
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(result,encoding='utf-8')
    print(result,end='')


if __name__=='__main__':
    main()
