#!/usr/bin/env python3
"""Read-only Xak III Geargrafx v44 CPU-state and scene code-copy resolver.

Disc images and Geargrafx save states are user-owned inputs, never modified.
The resulting source offsets do not identify a safe executable hook.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

CPU_OFFSET=0x6A2C9
PREGAP=225
PROBES=(0x2000, 0x4000, 0x5000)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def parse_state(state):
    h=len(state)-200
    if h<0 or struct.unpack_from("<III", state, h)!=(0x82190619,44,len(state)):
        raise ValueError("Unsupported Geargrafx state format")
    if state[0]!=1:
        raise ValueError("CD hardware not enabled")
    mpr=list(state[13:21])
    p=13+8+0x8000
    cd_size=struct.unpack_from("<I",state,p)[0]
    if cd_size!=0x10000:
        raise ValueError("Expected 64 KiB CD RAM")
    p+=4
    ram=state[p:p+cd_size]
    p+=cd_size
    card_size=struct.unpack_from("<I",state,p)[0]
    if card_size!=0x30000:
        raise ValueError("Expected 192 KiB Super CD RAM")
    p+=4+card_size
    if state[p:p+2]!=bytes([0x68,0x7F]):
        raise ValueError("Unknown Super CD bank allocation")
    # Memory tail + HuC6202 + HuC6260 + 2x HuC6270.
    if p+(2+0x800+1+1+1+1)+33+1059+2*68401!=CPU_OFFSET:
        raise AssertionError("State serializer layout unexpected")
    pc,A,X,Y,S,P=struct.unpack_from("<H5B",state,CPU_OFFSET)
    bank=mpr[pc//0x2000]
    if not 0x80<=bank<0x88:
        raise ValueError("Snapshot PC outside mapped CD RAM")
    local=(bank-0x80)*0x2000+pc%0x2000
    return dict(pc=pc,bank=bank,local=local,
                registers=dict(A=A,X=X,Y=Y,S=S,P=P),
                state_sha256=sha(state),ram=ram)


def read_iso_from_raw(track):
    if len(track)%2352 or len(track)//2352<=PREGAP:
        raise ValueError("Expected full raw Track 02, 2352 bytes/sector")
    first=track[PREGAP*2352:(PREGAP+1)*2352]
    if first[:12]!=bytes([0]+[255]*10+[0]) or first[15]!=1:
        raise ValueError("Indexed Track 02 first sector not MODE1")
    return b"".join(track[i+16:i+2064] for i in
                    range(PREGAP*2352,len(track),2352))


def find_all(data,pattern):
    found=[];i=0
    while (i:=data.find(pattern,i))>=0:
        found.append(i)
        if len(found)>1000:
            raise ValueError("Too many occurrences")
        i+=1
    return found


def resolve(ram,iso,local):
    observations={}
    for offset in PROBES:
        pattern=ram[offset:offset+128]
        if len(pattern)!=128 or len(set(pattern))<4:
            raise ValueError("Insufficiently distinct loaded code data")
        positions=find_all(iso,pattern)
        observations[format(offset,"04X")]={"matches":len(positions),
            "deltas":sorted(set(i-offset for i in positions))}
    choices=set.intersection(*(set(v["deltas"]) for v in observations.values()))
    if len(choices)!=1:
        raise ValueError("Co-loaded code copy is ambiguous")
    delta=choices.pop()
    iso_offset=delta+local
    sector,inside=divmod(iso_offset,2048)
    return dict(probes=observations,selected_delta=delta,
                selected_PC_indexed_ISO_offset=iso_offset,
                selected_PC_indexed_sector=sector,
                selected_PC_raw_sector=sector+PREGAP,
                selected_PC_raw_byte_offset=(sector+PREGAP)*2352+16+inside)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state",type=Path,required=True)
    ap.add_argument("--data-track",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    if (a.out.exists() or a.out.resolve() in
            (a.state.resolve(), a.data_track.resolve())):
        ap.error("Refusing to overwrite existing files or sources")
    state=parse_state(a.state.read_bytes())
    track=a.data_track.read_bytes()
    summary=resolve(state.pop("ram"),read_iso_from_raw(track),state["local"])
    summary.update(cpu_PC=hex(state["pc"]),cpu_bank=hex(state["bank"]),
                   cpu_registers=state["registers"],
                   state_sha256=state["state_sha256"],
                   track_sha256=sha(track),
                   status="Static source provenance, not a verified runtime hook")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
