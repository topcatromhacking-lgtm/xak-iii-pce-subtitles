#!/usr/bin/env python3
"""Geargrafx/Xak III native-SAT routine re-entry test; no disc modifications.

Patch a COPY of the SHA-256-pinned slot5 save:
1. Rewind CPU PC from $8590 to native sprite writer entry $8516.
2. Replace RAM-resident $8593 STZ $3444 with NOP NOP NOP.
This is a temporary diagnostic, not a gameplay-safe patch.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

ORIGINAL_SHA256 = '6ed046b184df5f32ce4371ee81086cf09b3902ac99224db98ba10f4dab418bda'
EXPECTED_TEST_SHA256 = '65cd995a37490f80208a52bcdee1c381927e3066aded4534ff4a32e395087c76'
PC_OFFSET = 0x6A2C9
CD_RAM_OFFSET = 13+8+32768+4
STZ_OFFSET = CD_RAM_OFFSET+(0x8593-0x4000)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def patch(base):
    if sha(base) != ORIGINAL_SHA256:
        raise ValueError('Unrecognized slot5 baseline')
    h = len(base)-200
    if len(base) != 749238 or struct.unpack_from('<III', base, h) != (0x82190619,44,len(base)):
        raise ValueError('Not the expected Geargrafx v44 state')
    if struct.unpack_from('<H',base,PC_OFFSET)[0] != 0x8590:
        raise ValueError('Unexpected saved CPU PC')
    if base[13:21] != bytes.fromhex('FF F8 80 81 82 83 84 00'):
        raise ValueError('Unexpected PCE bank mapping')
    if base[CD_RAM_OFFSET+0x4516:CD_RAM_OFFSET+0x451A] != bytes.fromhex('A9 00 85 F7'):
        raise ValueError('Unexpected routine entry instruction bytes')
    if base[STZ_OFFSET:STZ_OFFSET+3] != bytes.fromhex('9C 44 34'):
        raise ValueError('Unexpected native count-clearing instruction')
    if base[21+0x3444-0x2000] != 8:
        raise ValueError('Expected eight sprite records in working RAM')
    out=bytearray(base)
    struct.pack_into('<H',out,PC_OFFSET,0x8516)
    out[STZ_OFFSET:STZ_OFFSET+3] = b'\xEA'*3
    changes=[i for i,(a,b) in enumerate(zip(base,out)) if a!=b]
    expected=sorted([PC_OFFSET,STZ_OFFSET,STZ_OFFSET+1,STZ_OFFSET+2])
    if changes != expected:
        raise AssertionError('Changed bytes outside intended PC/code addresses')
    if out[-200:] != base[-200:] or out[21:21+32768] != base[21:21+32768]:
        raise AssertionError('State header or sprite record RAM changed')
    if out[0x48C67:PC_OFFSET] != base[0x48C67:PC_OFFSET]:
        raise AssertionError('VDC or other pre-CPU state changed')
    if sha(out) != EXPECTED_TEST_SHA256:
        raise AssertionError('Output regression SHA-256 mismatch')
    return bytes(out)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--slot5',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists() or args.out.resolve() == args.slot5.resolve():
        ap.error('Refusing to overwrite any input or existing output')
    output=patch(args.slot5.read_bytes())
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(output)
    print(json.dumps({
      'changed_bytes':4,'output_sha256':sha(output),
      'status':'Static QA only; Geargrafx runtime test required',
    },indent=2))


if __name__ == '__main__':
    main()
