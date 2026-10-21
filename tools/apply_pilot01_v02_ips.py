#!/usr/bin/env python3
"""Apply the tiny v0.2 experimental Xak III subtitle proof to an authorized
raw (MODE1/2352) English split Track 02. Refuses unknown inputs, never
overwrites the original or an existing destination.
"""
import argparse
import hashlib
from pathlib import Path

SOURCE_SHA256 = "c3aef214616309a6a87f9836bdc8062e57b3e2d5b492b089f72fd52848cd9b72"
TARGET_SHA256 = "c69aa8dd3f0878dc70e8e80f804d0160a5b5c3572c4bad9ebcea711082a2268d"
PATCH_SHA256 = "74b0291217c3b880683e56b5ec73e1d9055571b5d477df956092be85948e4d4d"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def apply_ips(original, patch):
    if not patch.startswith(b"PATCH") or not patch.endswith(b"EOF"):
        raise ValueError("Invalid IPS marker")
    out=bytearray(original)
    i=5
    while i < len(patch)-3:
        offset=int.from_bytes(patch[i:i+3],"big")
        length=int.from_bytes(patch[i+3:i+5],"big")
        i+=5
        if length==0:
            if i+3 > len(patch)-3:
                raise ValueError("Truncated RLE record")
            run=int.from_bytes(patch[i:i+2],"big")
            fill=patch[i+2]
            data=bytes([fill])*run
            i+=3
        else:
            data=patch[i:i+length]
            if len(data)!=length:
                raise ValueError("Truncated IPS record")
            i+=length
        if offset+len(data) > len(out):
            raise ValueError("Patch would resize file")
        out[offset:offset+len(data)]=data
    if i!=len(patch)-3:
        raise ValueError("Unexpected trailing IPS bytes")
    return bytes(out)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base",type=Path,required=True,help="English split Track 02 raw BIN")
    ap.add_argument("--patch",type=Path,default=Path(__file__).parents[1]/
                    "patches/Xak_III_Pilot01_SUB_TEST_v02_Track02.ips")
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists() or args.out.resolve() in (
            args.base.resolve(),args.patch.resolve()):
        ap.error("Refusing to overwrite input or existing output")
    original=args.base.read_bytes()
    patch=args.patch.read_bytes()
    if sha256(original)!=SOURCE_SHA256 or len(original)!=54773376:
        ap.error("Unrecognized English split-track baseline; no file changed")
    if sha256(patch)!=PATCH_SHA256:
        ap.error("Unknown/damaged IPS; no file changed")
    new=apply_ips(original,patch)
    if sha256(new)!=TARGET_SHA256:
        raise RuntimeError("Output regression mismatch; no file written")
    differences=[i for i in range(0,len(original),2352) if
                 original[i:i+2352]!=new[i:i+2352]]
    if differences!=[743*2352,745*2352]:
        raise RuntimeError("Unexpected disc-sector changes")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(new)
    print("Experimental v0.2 output verified:",args.out)
    print("SHA-256:",sha256(new))


if __name__=="__main__":
    main()
