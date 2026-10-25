#!/usr/bin/env python3
"""Xak III v0.9: background-gated native sprite-enable experiment (state only).

Copies the user's pinned early-King Geargrafx v44 save state and creates a
new v0.9 state2/CUE. Leaves v0.5's game disc and Japanese CD-DA unchanged.

Native raster computation: (CR & $3F) | table[X].
Proposed: enable sprites ONLY when background is enabled in the same band.
This is not production-safe across unsampled scenes; inspect on emulator.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

SOURCE_SHA='63a2ea5434314c0303b9c5fb5266962de76c0c260cd093d7f649a760036cc694'
SIZE=749238
HEADER=200
CDRAM=13+8+32768+4
CALLSITE=0x65AA
CAVE=0x76DF
TRACK02='Xak_III_English_Track02_SUB_TEST_v05.bin'
NAME='Xak_III_English_SUB_TEST_v09_Pilot01'
ORIGINAL=bytes.fromhex('AD 3D 23 29 3F 1D 72 3E 03 05 8D 02 00')
REDIRECT=bytes.fromhex('20 DF 76 EA EA')
# AND #$3F; ORA $3E72,X; BPL .done; ORA #$40; .done: RTS
HELPER=bytes.fromhex('29 3F 1D 72 3E 10 02 09 40 60')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def ram(cpu):
    if not 0x6000<=cpu<0x8000:
        raise ValueError('Expected bank81 local CPU address')
    return CDRAM+0x2000+cpu-0x6000

def validate(data, pin=True):
    if len(data)!=SIZE or struct.unpack_from('<III',data,len(data)-HEADER)!=(0x82190619,44,len(data)):
        raise ValueError('Expected 749238-byte native Geargrafx v44 state')
    if pin and sha(data)!=SOURCE_SHA:
        raise ValueError('Early King state5 source hash mismatch')
    if data[ram(CALLSITE-3):ram(CALLSITE-3)+len(ORIGINAL)]!=ORIGINAL:
        raise ValueError('Unexpected native raster routine')
    if data[ram(CAVE):ram(CAVE)+128]!=bytes(128):
        raise ValueError('Candidate code cave is not empty')
    if data[13:21]!=bytes.fromhex('FF F8 80 81 82 83 84 00'):
        raise ValueError('Unexpected CPU bank map')
    if data[21+0x33D]!=0xCC:
        raise ValueError('Unexpected native VDC base CR')
    if struct.unpack_from('<H',data,0x48C67+65536+4+5*2)[0]!=0xCC:
        raise ValueError('Unexpected saved VDC1 CR')

def build_state(data, pin=True):
    validate(data,pin)
    result=bytearray(data)
    result[ram(CALLSITE):ram(CALLSITE)+5]=REDIRECT
    result[ram(CAVE):ram(CAVE)+len(HELPER)]=HELPER
    result=bytes(result)
    diff=[i for i,(a,b) in enumerate(zip(data,result)) if a!=b]
    expected=list(range(ram(CALLSITE),ram(CALLSITE)+5))+list(range(ram(CAVE),ram(CAVE)+len(HELPER)))
    if diff!=expected or result[-HEADER:]!=data[-HEADER:]:
        raise AssertionError('Unexpected changed state bytes')
    return result, {
        'experiment':'Xak III v0.9 background-gated sprite enable',
        'state':'OFFLINE VERIFIED / GEARGRAFX TEST PENDING',
        'source_sha256':sha(data),'output_sha256':sha(result),
        'changed_bytes':len(diff),
        'callsite':'bank81 $65AA: JSR $76DF / NOP / NOP',
        'helper':'bank81 $76DF: '+HELPER.hex(' '),
        'king_table_80':'CR $CC -> BG and sprites ON',
        'black_table_00':'CR $0C -> BG and sprites OFF',
        'normal_table_c0':'CR $CC unchanged',
        'disc_modified':False,'voice_modified':False,
        'risk':'May show other native sprites in BG-enabled raster bands',
    }

def cue_validate(cue):
    if len(re.findall(r'^\s*TRACK\s+\d+',cue,re.M))!=35:
        raise ValueError('Expected 35-track split CUE')
    if len(re.findall(r'^\s*TRACK\s+28\s+AUDIO\s*$',cue,re.M))!=1:
        raise ValueError('Expected physical Japanese audio Track 28')
    if cue.count('FILE "'+TRACK02+'" BINARY')!=1:
        raise ValueError('Expected unchanged v0.5 Track02 reference')
    return cue

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,required=True)
    parser.add_argument('--cue',type=Path,required=True)
    parser.add_argument('--outdir',type=Path)
    args=parser.parse_args()
    root=args.outdir or args.cue.parent
    if not root.is_dir():
        parser.error('Output directory must exist')
    outputs=[root/(NAME+'.cue'),root/(NAME+'.state2'),root/'Xak_III_v09_selective_raster_report.json']
    if any(x.exists() for x in outputs) or args.state.resolve() in [x.resolve() for x in outputs]:
        parser.error('Refusing to overwrite a source or existing v0.9 output')
    if not (args.cue.parent/TRACK02).is_file():
        parser.error('Original v0.5 Track02 missing next to source CUE')
    image,report=build_state(args.state.read_bytes())
    cue=cue_validate(args.cue.read_text(encoding='utf-8-sig'))
    outputs[0].write_text(cue,encoding='utf8',newline='\n')
    outputs[1].write_bytes(image)
    outputs[2].write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))
    print('Boot',outputs[0],'and load v0.9 Slot 2')

if __name__=='__main__':
    main()
