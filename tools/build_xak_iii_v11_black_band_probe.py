#!/usr/bin/env python3
"""Xak III v0.11: lower-black-band diagnostic; save-state only.

This is source-only logic. The downloadable test ZIP also includes the user's
private, derived v0.11 save state; no state is committed to this repository.
The builder refuses to overwrite any original save or disc track.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct
from pathlib import Path

STATE_NAME='Xak_III_English_SUB_TEST_v11_Pilot01.state2'
CUE_NAME='Xak_III_English_SUB_TEST_v11_Pilot01.cue'
REPORT_NAME='Xak_III_v11_Black_Band_Probe_Report.json'
SOURCE_STATE_NAME='Xak_III_English_SUB_TEST_v09_Pilot01.state2'
V05_TRACK='Xak_III_English_Track02_SUB_TEST_v05.bin'
V10_TRACK='Xak_III_English_Track02_SUB_TEST_v10.bin'
PINNED_SHA='8b40e7d95c5cfc6ec57eeffa00f58058a3b6692c055469e56d579a1bbd5c5fb2'
STATE_SIZE=749238
CDRAM=13+8+32768+4
HEADER=200
HELPER_CPU=0x76DF
SAT_TABLE_CPU=0x9C9A
OLD_HELPER=bytes.fromhex('29 3F 1D 72 3E 10 02 09 40 60')
# Replace BPL +2 with NOP/NOP: sprites enabled in black bands for this test.
NEW_HELPER=bytes.fromhex('29 3F 1D 72 3E EA EA 09 40 60')
OLD_TABLE=bytes.fromhex('C0 C0 C0 C0 00 00 00 00 40 50 60 70')
# SU + B / TE + ST => two text lines inside native screen Y184-219.
NEW_TABLE=bytes.fromhex('F8 F8 0C 0C 00 00 01 01 90 A0 90 A0')

def sha256(b):return hashlib.sha256(b).hexdigest()

def offset(cpu):
    if not 0x4000<=cpu<0xC000:
        raise ValueError('CPU outside verified mounted bank80..83 range')
    return CDRAM + cpu - 0x4000

def check_source(s,*,require_pinned=True):
    if len(s)!=STATE_SIZE or struct.unpack_from('<III',s,len(s)-HEADER)!=(0x82190619,44,len(s)):
        raise ValueError('Expected Geargrafx 1.8.4 native 749238-byte state')
    if require_pinned and sha256(s)!=PINNED_SHA:
        raise ValueError('Source is not exact v0.9 early King checkpoint')
    if s[offset(HELPER_CPU):offset(HELPER_CPU)+len(OLD_HELPER)]!=OLD_HELPER:
        raise ValueError('v0.9 raster helper mismatch')
    if s[offset(SAT_TABLE_CPU):offset(SAT_TABLE_CPU)+len(OLD_TABLE)]!=OLD_TABLE:
        raise ValueError('Subtitle SAT coordinate tables mismatch')
    if s[offset(0x9CAA):offset(0x9CAE)]!=bytes.fromhex('76 70 72 74'):
        raise ValueError('Stable v0.5 glyph refs changed')
    if s[offset(0x65AA):offset(0x65AF)]!=bytes.fromhex('20 DF 76 EA EA'):
        raise ValueError('v0.9 callsite mismatch')
    if s[offset(0x9C99)]!=0:
        raise ValueError('Early King subtitle init flag mismatch')

def patch_state(s,*,require_pinned=True):
    check_source(s,require_pinned=require_pinned)
    b=bytearray(s)
    b[offset(HELPER_CPU):offset(HELPER_CPU)+len(NEW_HELPER)]=NEW_HELPER
    b[offset(SAT_TABLE_CPU):offset(SAT_TABLE_CPU)+len(NEW_TABLE)]=NEW_TABLE
    result=bytes(b)
    diff={i for i,(a,c) in enumerate(zip(s,result)) if a!=c}
    expected={offset(HELPER_CPU)+i for i,(a,c) in enumerate(zip(OLD_HELPER,NEW_HELPER)) if a!=c}
    expected|={offset(SAT_TABLE_CPU)+i for i,(a,c) in enumerate(zip(OLD_TABLE,NEW_TABLE)) if a!=c}
    if diff!=expected or len(diff)!=12:
        raise AssertionError('Unexpected changed state bytes')
    if s[:CDRAM]!=result[:CDRAM] or s[CDRAM+65536:]!=result[CDRAM+65536:]:
        raise AssertionError('Non-CD-RAM save mutated')
    return result,{
      'experiment':'Xak III v0.11 bottom black band: SUB / TEST two-line marker',
      'status':'OFFLINE-VERIFIED; ACTUAL EMULATOR RESULT PENDING',
      'source_state_sha256':sha256(s),'patched_state_sha256':sha256(result),
      'changed_bytes':len(diff),'changed_file_offsets':sorted(diff),
      'cpu_edit':'bank81 $76E4 BPL +2 -> NOP NOP (temporary, diagnostic)',
      'subtitle_screen_y':[184,204],'subtitle_sprite_x':[144,160,144,160],
      'expected_marker':['SUB','TEST'],
      'note':'BG-off bands may show unrelated game sprites; abort on artifacts',
      'original_v05_v09_v10_disc_and_audio_modified':False}

def make_cue(cue):
    old='FILE "'+V05_TRACK+'" BINARY'
    if cue.count(old)!=1 or len(re.findall(r'^\s*TRACK\s+\d+',cue,re.M))!=35:
        raise ValueError('Expected original split v0.9 35-track cue')
    if len(re.findall(r'^\s*TRACK\s+28\s+AUDIO\s*$',cue,re.M))!=1:
        raise ValueError('Japanese speech Track28 missing')
    return cue.replace(old,'FILE "'+V10_TRACK+'" BINARY')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state',required=True,type=Path)
    p.add_argument('--cue',required=True,type=Path)
    p.add_argument('--outdir',type=Path)
    args=p.parse_args()
    root=args.outdir or args.cue.parent
    if not root.is_dir() or not (root/V10_TRACK).is_file():
        p.error('Existing v0.10 Track02 BIN required in output game folder')
    outputs=(root/CUE_NAME,root/STATE_NAME,root/REPORT_NAME)
    if any(f.exists() for f in outputs):
        p.error('Refusing to overwrite existing v0.11 outputs')
    state,report=patch_state(args.state.read_bytes())
    cue=make_cue(args.cue.read_text(encoding='utf-8-sig'))
    outputs[0].write_text(cue,encoding='utf8',newline='\n')
    outputs[1].write_bytes(state)
    outputs[2].write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
