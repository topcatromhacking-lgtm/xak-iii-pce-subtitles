#!/usr/bin/env python3
"""Xak III Pilot 01 v0.10: promote v0.9 selective King raster fix to disc.

Requires the exact user-owned v0.5 Track 02 and matching split 35-track CUE.
Creates a NEW patched raw Track02, CUE, IPS and JSON report; optionally seeds
verified military-camp Slot 1. Original v0.5 remains unchanged. Neither any
Japanese CD-DA nor any of 34 audio tracks is included or modified.

This patch implements the real-Geargrafx-validated v0.9 *state* technique on
Xak III's bank81 CD-RAM source bytes in Track02:
    $65AA: JSR $76DF ; NOP ; NOP  (5 bytes)
    $76DF: AND #$3F ; ORA $3E72,X ; BPL +2 ; ORA #$40 ; RTS

The helper enables sprite output in raster bands where the original game
already enabled the background, without enabling sprites in $00 blank bands.
The global visual effect outside this audience scene is NOT fully validated;
this is an isolated experimental build, not a final subtitle translation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

import build_xak_iii_v03_visibility_probe as core
import build_xak_iii_v05_glyph_stability_probe as v05

INPUT_TRACK = 'Xak_III_English_Track02_SUB_TEST_v05.bin'
INPUT_CUE = 'Xak_III_English_SUB_TEST_v05_Pilot01.cue'
OUTPUT_TRACK = 'Xak_III_English_Track02_SUB_TEST_v10.bin'
OUTPUT_CUE = 'Xak_III_English_SUB_TEST_v10_Pilot01.cue'
OUTPUT_IPS = 'Xak_III_Pilot01_v10_from_v05_Track02.ips'
OUTPUT_REPORT = 'Xak_III_Pilot01_v10_report.json'
CAMP_STATE = 'Xak_III_English_SUB_TEST_v05_Pilot01.state1'
OUTPUT_CAMP = 'Xak_III_English_SUB_TEST_v10_Pilot01.state1'
V05_SHA = 'a87babc4dafa0f43091015b86014036978940fdf3c44048409727a0f9acdc207'
EXPECTED_LENGTH = 54_773_376

# Provenance of the resident first-64KiB CD-RAM block (source indexed ISO
# user-data offset 0xFE800), mapped into HuC6280 banks $80 through $87.
CD_RAM_INDEXED_USER_OFFSET = 0xFE800
TRACK02_PREGAP_RAW_SECTORS = 225
CALLSITE = 0x65AA
CAVE = 0x76DF
CALLSITE_CONTEXT = bytes.fromhex('AD 3D 23 29 3F 1D 72 3E 03 05 8D 02 00')
OLD = bytes.fromhex('29 3F 1D 72 3E')
NEW = bytes.fromhex('20 DF 76 EA EA')
HELPER = bytes.fromhex('29 3F 1D 72 3E 10 02 09 40 60')
CAVE_GUARD_LEN = 128
EDITED_CPU_BYTES = {*(CALLSITE + i for i in range(len(OLD))),
                    *(CAVE + i for i in range(len(HELPER)))}
EXPECTED_SECTORS = (738, 740)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def disc_byte_offset(cpu: int) -> int:
    """Map $4000..$BFFF through verified bank80..83 CD-RAM provenance.

    Does not apply to CPU $C000+ (different memory banks), nor does it claim
    a physical disc-CPU correspondence for other scenes.
    """
    if not 0x4000 <= cpu < 0xC000:
        raise ValueError('CPU address is outside verified CD RAM mapping')
    logical = CD_RAM_INDEXED_USER_OFFSET + cpu - 0x4000
    indexed_sector, offset = divmod(logical, 2048)
    physical_sector = indexed_sector + TRACK02_PREGAP_RAW_SECTORS
    return physical_sector * core.SECTOR_SIZE + 16 + offset


def read_code(track: bytes, cpu: int, count: int) -> bytes:
    """Reads a contiguous CPU instruction within one MODE1 sector."""
    first = disc_byte_offset(cpu)
    end = disc_byte_offset(cpu + count - 1)
    if end != first + count - 1:
        raise ValueError('Code slice spans a MODE1 sector boundary')
    return track[first:first + count]


def check_track(track: bytes, expected_sha: str = V05_SHA):
    if len(track) != EXPECTED_LENGTH or sha(track) != expected_sha:
        raise ValueError('Wrong Track02: requires exact original v0.5 BIN (size and SHA-256)')
    if disc_byte_offset(CALLSITE) != 0x1A821A or disc_byte_offset(CAVE) != 0x1A95AF:
        raise AssertionError('Disc bank mapping anchors changed')
    for sector in EXPECTED_SECTORS:
        start = sector * core.SECTOR_SIZE
        if not core.verify_mode1_sector(track[start:start + core.SECTOR_SIZE]):
            raise ValueError(f'Input MODE1 sector {sector} has invalid EDC/ECC')
    if read_code(track, CALLSITE - 3, len(CALLSITE_CONTEXT)) != CALLSITE_CONTEXT:
        raise ValueError('Racing native raster code does not match v0.9 state')
    if read_code(track, CALLSITE, len(OLD)) != OLD:
        raise ValueError('Original raster mask callsite mismatch')
    if read_code(track, CAVE, CAVE_GUARD_LEN) != bytes(CAVE_GUARD_LEN):
        raise ValueError('Disc code cave $76DF is not zero; refusing unsafe injection')
    if read_code(track, 0x9C00, 10) != bytes.fromhex('48 DA 5A AD 99 9C C9 FF D0 41'):
        raise ValueError('Expected v0.5 subtitle hook is missing')
    if read_code(track, 0x9C99, 1) != b'\xFF':
        raise ValueError('Expected uninitialized subtitle flag $9C99 is missing')
    if read_code(track, 0x9CAA, 4) != bytes((59*2, 56*2, 57*2, 58*2)):
        raise ValueError('v0.5 font relocation was not found')
    if track[0x1AB145:0x1AB148] != bytes.fromhex('20 00 9C'):
        raise ValueError('Scene-loop JSR to subtitle hook missing')
    return True


def patch_track(track: bytes, expected_sha: str = V05_SHA) -> bytes:
    check_track(track, expected_sha)
    buf = bytearray(track)
    for cpu, payload in ((CALLSITE, NEW), (CAVE, HELPER)):
        off = disc_byte_offset(cpu)
        buf[off:off + len(payload)] = payload
    for sector in EXPECTED_SECTORS:
        start = sector * core.SECTOR_SIZE
        buf[start:start+core.SECTOR_SIZE] = core.restore_mode1_sector(
            bytes(buf[start:start+core.SECTOR_SIZE]))
    result = bytes(buf)
    for sector in EXPECTED_SECTORS:
        start = sector * core.SECTOR_SIZE
        assert core.verify_mode1_sector(result[start:start+core.SECTOR_SIZE])
    # Compare sectors instead of scanning every individual byte of the 54MB BIN.
    changed = [i for i in range(len(track)//core.SECTOR_SIZE)
               if track[i*core.SECTOR_SIZE:(i+1)*core.SECTOR_SIZE] !=
                  result[i*core.SECTOR_SIZE:(i+1)*core.SECTOR_SIZE]]
    if changed != list(EXPECTED_SECTORS):
        raise AssertionError('Modified unexpected raw sectors: '+str(changed))
    changed_userdata = set()
    for sector in EXPECTED_SECTORS:
        start = sector * core.SECTOR_SIZE
        changed_userdata.update(start+i for i in range(16,2064) if track[start+i] != result[start+i])
    expected_userdata = {disc_byte_offset(cpu) for cpu in EDITED_CPU_BYTES}
    if changed_userdata != expected_userdata:
        raise AssertionError('Changed unexpected indexed user-data bytes: '+str(changed_userdata ^ expected_userdata))
    if read_code(result, CALLSITE, len(NEW)) != NEW or read_code(result, CAVE, len(HELPER)) != HELPER:
        raise AssertionError('New native code did not match v0.9 validation')
    for cpu, n in ((0x9C00, 10), (0x9C99, 1), (0x9CAA, 4), (0x9C9A, 8)):
        if read_code(result,cpu,n) != read_code(track,cpu,n):
            raise AssertionError('Changed protected subtitle field at '+hex(cpu))
    return result


def make_cue(original: str) -> str:
    old = f'FILE "{INPUT_TRACK}" BINARY'
    if original.count(old) != 1 or len(re.findall(r'^\s*TRACK\s+\d+', original, re.M)) != 35:
        raise ValueError('Expected original v0.5 split 35-track CUE')
    if len(re.findall(r'^\s*TRACK\s+28\s+AUDIO\s*$',original,re.M))!=1:
        raise ValueError('Physical Japanese Track28 dialogue audio not found')
    return original.replace(old, f'FILE "{OUTPUT_TRACK}" BINARY')


def check_camp(state: bytes) -> bool:
    if len(state)!=749238 or sha(state)!=v05.CLEAN_CAMP_SHA256 or \
            struct.unpack_from('<III',state,len(state)-200)!=(0x82190619,44,len(state)):
        raise ValueError('Original military-camp state1 failed pinned hash check')
    return True


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--track02',type=Path,required=True,help='Exact v0.5 raw 54,773,376-byte Track02')
    p.add_argument('--cue',type=Path,required=True,help='Matching existing v0.5 CUE')
    p.add_argument('--camp-state',type=Path,help='Optional exact verified clean camp state1')
    args=p.parse_args()
    track_path=args.track02.resolve()
    cue_path=args.cue.resolve()
    if track_path.parent!=cue_path.parent:
        p.error('Track02 and CUE must be in the same existing game directory')
    if track_path.name!=INPUT_TRACK or cue_path.name!=INPUT_CUE:
        p.error('Expected exact v0.5 filenames')
    root=track_path.parent
    expected_paths=[root/x for x in (OUTPUT_TRACK,OUTPUT_CUE,OUTPUT_IPS,OUTPUT_REPORT)]
    camp_source=args.camp_state.resolve() if args.camp_state else root/CAMP_STATE
    camp_bytes=None
    if camp_source.exists():
        camp_bytes=camp_source.read_bytes()
        check_camp(camp_bytes)
        expected_paths.append(root/OUTPUT_CAMP)
    elif args.camp_state:
        p.error('Explicit --camp-state file is missing')
    if any(x.exists() for x in expected_paths):
        p.error('An output v0.10 file already exists; refusing to overwrite anything')
    before=track_path.read_bytes()
    after=patch_track(before)
    cue=make_cue(cue_path.read_text(encoding='utf-8-sig'))
    ips=core.create_ips(before,after)
    if core.apply_ips(before,ips)!=after:
        raise AssertionError('Independent IPS application did not reproduce new Track02')
    report={
        'experiment':'Xak III Pilot01 v0.10 disc-native selective raster sprite visibility',
        'status':'OFFLINE-VERIFIED; ACTUAL DISC BOOT AND SCENE TEST PENDING',
        'v09_state_only_runtime_result':'User reported all good; King subtitle visible, clean borders, normal scene',
        'input_v05_sha256':sha(before), 'output_v10_sha256':sha(after),
        'delta_ips_sha256':sha(ips), 'delta_ips_bytes':len(ips),
        'changed_raw_mode1_sectors':list(EXPECTED_SECTORS),
        'changed_user_data_cpu_bytes':{'$65AA':OLD.hex(' ')+' -> '+NEW.hex(' '),
                                       '$76DF':HELPER.hex(' ')},
        'mode1_edc_ecc_valid':True,
        '35_track_cue':True, 'japanese_cdda_tracks':'REUSED UNCHANGED',
        'existing_v05_subtitle_font_and_native_sprite_writer':'UNCHANGED',
        'old_v05_disc_and_save_states':'UNCHANGED',
        'clean_camp_slot1_seeded':camp_bytes is not None,
        'warning':'Prototype enables sprites for every BG-enabled raster band in this patched module; '
                  'the full game and actual synchronized captions remain to be tested',
    }
    blobs=[after,cue.encode('utf-8'),ips,(json.dumps(report,indent=2)+'\n').encode('utf-8')]
    if camp_bytes is not None:
        blobs.append(camp_bytes)
    for path,data in zip(expected_paths,blobs):
        path.write_bytes(data)
    print(json.dumps(report,indent=2))
    print('BOOT:',root/OUTPUT_CUE)


if __name__=='__main__':
    main()
