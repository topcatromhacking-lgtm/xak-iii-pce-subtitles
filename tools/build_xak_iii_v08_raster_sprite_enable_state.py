#!/usr/bin/env python3
"""Xak III v0.8: save-state-only probe of King Wavis raster sprite enable.

Uses an original, SHA-pinned v0.5 Geargrafx state5. Creates a NEW v0.8
CUE (references unchanged v0.5 BIN/audio) and new state2. Exactly one
loaded CD RAM byte changes: bank81 CPU $65AB AND #$3F -> AND #$7F.
No original disc/ISO, CD-DA track, save state, or screenshot changes.
Diagnostic only; can reveal other sprites in formerly blank raster bands.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

SOURCE_SHA="63a2ea5434314c0303b9c5fb5266962de76c0c260cd093d7f649a760036cc694"
TRACK="Xak_III_English_Track02_SUB_TEST_v05.bin"
CUE_NAME="Xak_III_English_SUB_TEST_v08_Pilot01.cue"
STATE_NAME="Xak_III_English_SUB_TEST_v08_Pilot01.state2"
REPORT_NAME="Xak_III_v08_Early_King_Raster_Probe_Report.json"
STATE_SIZE=749238
CD_RAM=13+8+32768+4
OP_ADDRESS=0x65AB
BANK81_OFFSET=0x2000
OFF=CD_RAM+BANK81_OFFSET+(OP_ADDRESS-0x6000)
INSTRUCTION=bytes.fromhex("AD 3D 23 29 3F 1D 72 3E 03 05 8D 02 00")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verify(b, require_hash=True):
    if len(b)!=STATE_SIZE or struct.unpack_from("<III",b,len(b)-200)!=(0x82190619,44,len(b)):
        raise ValueError("Expected Geargrafx 1.8.4 native v44 state")
    if require_hash and sha(b)!=SOURCE_SHA:
        raise ValueError("Not the pinned original v0.5 early King state5")
    if b[OFF-4:OFF-4+len(INSTRUCTION)]!=INSTRUCTION:
        raise ValueError("Original raster VDC-CR code is not present")
    if b[13:21]!=bytes.fromhex("FF F8 80 81 82 83 84 00"):
        raise ValueError("Unexpected HuC6280 bank mapping")
    if b[21+(0x233D-0x2000)]!=0xCC:
        raise ValueError("Expected native base CR=$CC")
    if struct.unpack_from("<H",b,0x48C67+65536+4+5*2)[0]!=0xCC:
        raise ValueError("Unexpected saved VDC1 CR")
    return True

def patch_state(state, require_hash=True):
    verify(state,require_hash)
    result=bytearray(state)
    assert result[OFF]==0x3F
    result[OFF]=0x7F
    result=bytes(result)
    changed=[i for i,(x,y) in enumerate(zip(state,result)) if x!=y]
    if changed!=[OFF] or state[-200:]!=result[-200:]:
        raise AssertionError("Only the operand byte may change")
    report={
        "experiment":"Xak III v0.8 raster CR sprite-enable diagnostic",
        "status":"OFFLINE-VERIFIED; NO EMULATOR RESULT YET",
        "original_state_sha256":sha(state),
        "patched_state_sha256":sha(result),
        "changed_bytes":1,
        "offset":OFF,
        "instruction":"CPU bank81 $65AB: AND #$3F -> AND #$7F",
        "why":"King raster table $80 (background only) vs later $C0 (BG+sprites)",
        "original_king_CR":"($CC & $3F) | $80 = $8C (no sprites)",
        "test_king_CR":"($CC & $7F) | $80 = $CC (sprites enabled)",
        "risks":"Temporary forced sprite output may expose native sprites on black bands",
        "game_bin_or_audio_modified":False,
        "original_v05_saves_modified":False,
    }
    return result,report

def validate_cue(cue):
    if len(re.findall(r"^\s*TRACK\s+\d+",cue,re.M))!=35:
        raise ValueError("Expected 35 tracks")
    if len(re.findall(r"^\s*TRACK\s+28\s+AUDIO\s*$",cue,re.M))!=1:
        raise ValueError("Expected physical Japanese audio Track 28")
    if cue.count('FILE "'+TRACK+'" BINARY')!=1:
        raise ValueError("Expected original v0.5 Track02 reference")
    return cue

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state",type=Path,required=True)
    ap.add_argument("--cue",type=Path,required=True)
    ap.add_argument("--outdir",type=Path)
    args=ap.parse_args()
    root=args.outdir or args.cue.parent
    outputs=[root/CUE_NAME,root/STATE_NAME,root/REPORT_NAME]
    if any(p.exists() for p in outputs):
        ap.error("Refusing to overwrite any existing v0.8 file")
    b,report=patch_state(args.state.read_bytes())
    cue=validate_cue(args.cue.read_text(encoding="utf-8-sig"))
    if not (args.cue.parent/TRACK).is_file():
        ap.error("The existing v0.5 data Track02 must be beside the input CUE")
    root.mkdir(parents=True,exist_ok=True)
    outputs[0].write_text(cue,encoding="utf-8",newline="\n")
    outputs[1].write_bytes(b)
    outputs[2].write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    print("Boot",outputs[0],"then load Slot 2 for the King's first speech")

if __name__=="__main__":
    main()
