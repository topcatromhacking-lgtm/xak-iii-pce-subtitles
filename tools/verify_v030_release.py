#!/usr/bin/env python3
"""Independent, fail-closed verification of the v0.30 VS1 Track 02 xdelta.

This script never modifies a disc or any existing file. Metadata-only mode
needs only the patch; full mode also needs the user's clean Japanese Track 02
and xdelta3 on PATH. It pins the delivered patch's digest and source identity.

Usage:
  python tools/verify_v030_release.py PATCH.xdelta --report audit.json
  python tools/verify_v030_release.py PATCH.xdelta --clean-track02 CLEAN.bin \
    --report full_audit.json
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

MAGIC = b'\xd6\xc3\xc4\x00'
SECTOR = 2352
RAW_BYTES = 54_773_376
PREGAP_BYTES = 225 * SECTOR
CLEAN_SHA256 = 'af04551ce4bf60d50397e99a6467c9e081b3091caa4eb95c67e7984578021733'
PATCH_SHA256 = '9a36d3ca5d2adf2f388c7afbb271b9c36169e2f649407a0be0744810dda6246e'
PATCH_SIZE = 210_217
EXPECTED_WINDOWS = 7
EXPECTED_APP_SOURCE = 'Xak III - The Eternal Recurrence (Japan) (Track 02).bin'


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def varint(buf: bytes, i: int) -> tuple[int, int]:
    """Read RFC 3284 base-128, high-order-first integer, bounded to 64 bits."""
    value = 0
    for _ in range(10):
        if i >= len(buf):
            raise ValueError('Truncated VCDIFF integer')
        c = buf[i]
        i += 1
        if value > ((1 << 64) - 1) >> 7:
            raise ValueError('VCDIFF integer overflow')
        value = (value << 7) | (c & 0x7f)
        if not c & 0x80:
            return value, i
    raise ValueError('Oversized VCDIFF integer')


def parse_vcdiff(raw: bytes) -> dict:
    """Parse VCDIFF metadata and validate all section sizes; no decompression."""
    if raw[:4] != MAGIC:
        raise ValueError('Not a VCDIFF delta')
    i = 4
    if i >= len(raw):
        raise ValueError('Missing VCDIFF header indicator')
    flags = raw[i]
    i += 1
    if flags & ~0x07:
        raise ValueError('Unsupported VCDIFF header flags')
    secondary = None
    if flags & 0x01:
        if i >= len(raw):
            raise ValueError('Missing secondary compressor ID')
        secondary = raw[i]
        i += 1
    if flags & 0x02:
        size, i = varint(raw, i)
        if size > len(raw) - i:
            raise ValueError('Truncated custom code table')
        i += size
    app_header = ''
    if flags & 0x04:
        size, i = varint(raw, i)
        if size > len(raw) - i:
            raise ValueError('Truncated application header')
        app_header = raw[i:i + size].decode('utf-8')
        i += size
    windows = []
    target_total = 0
    while i < len(raw):
        start = i
        indicator = raw[i]
        i += 1
        if indicator & ~0x07 or indicator & 3 == 3:
            raise ValueError(f'Invalid window indicator at {start}')
        source_len = source_pos = None
        if indicator & 3:
            source_len, i = varint(raw, i)
            source_pos, i = varint(raw, i)
            if indicator & 1 and source_pos + source_len > RAW_BYTES:
                raise ValueError('Window source exceeds clean Track 02')
            if indicator & 2 and source_pos + source_len > target_total:
                raise ValueError('Window refers to unavailable target data')
        delta_len, i = varint(raw, i)
        delta_start = i
        target_len, i = varint(raw, i)
        if i >= len(raw):
            raise ValueError('Missing delta indicator')
        delta_indicator = raw[i]
        i += 1
        if delta_indicator & ~0x07:
            raise ValueError('Invalid delta indicator')
        data_len, i = varint(raw, i)
        inst_len, i = varint(raw, i)
        addr_len, i = varint(raw, i)
        adler32 = None
        if indicator & 4:
            if len(raw) - i < 4:
                raise ValueError('Missing Adler32')
            adler32 = raw[i:i + 4].hex()
            i += 4
        if delta_len != (i - delta_start) + data_len + inst_len + addr_len:
            raise ValueError('VCDIFF window delta-length mismatch')
        if data_len + inst_len + addr_len > len(raw) - i:
            raise ValueError('Truncated VCDIFF window sections')
        i += data_len + inst_len + addr_len
        windows.append(dict(output_offset=target_total, output_bytes=target_len,
                            source_offset=source_pos, source_bytes=source_len,
                            window_indicator=indicator, compression_flags=delta_indicator,
                            adler32=adler32))
        target_total += target_len
        if target_total > RAW_BYTES:
            raise ValueError('Decompressed target would exceed Track 02')
    if i != len(raw):
        raise ValueError('Trailing VCDIFF data')
    return dict(header_flags=flags, secondary_compressor=secondary,
                application_header=app_header, window_count=len(windows),
                target_bytes=target_total, windows=windows)


def inspect_patch(path: Path) -> dict:
    if path.stat().st_size != PATCH_SIZE:
        raise ValueError('Not the delivered v0.30 patch (size mismatch)')
    sha = digest(path)
    if sha != PATCH_SHA256:
        raise ValueError('Not the delivered v0.30 patch (SHA-256 mismatch)')
    report = parse_vcdiff(path.read_bytes())
    if report['target_bytes'] != RAW_BYTES or report['window_count'] != EXPECTED_WINDOWS:
        raise ValueError('Unexpected v0.30 target size or window count')
    if EXPECTED_APP_SOURCE not in report['application_header']:
        raise ValueError('Patch does not name the expected clean Track 02')
    report.update(patch_name=path.name, patch_size=path.stat().st_size,
                  patch_sha256=sha, source_sha256_expected=CLEAN_SHA256,
                  status='STRUCTURE VERIFIED — DECODING NOT YET VERIFIED')
    return report


def full_verify(patch: Path, clean: Path, report: dict) -> None:
    if clean.stat().st_size != RAW_BYTES:
        raise ValueError('Wrong clean Track 02 size')
    if digest(clean) != CLEAN_SHA256:
        raise ValueError('Wrong source SHA-256; never apply to v0.10 or a combined BIN')
    exe = shutil.which('xdelta3')
    if not exe:
        raise RuntimeError('xdelta3 is required to decode the full patch')
    with tempfile.TemporaryDirectory(prefix='xak3_v030_verify_') as d:
        out = Path(d) / 'decoded_v030.bin'
        proc = subprocess.run([exe, '-f', '-d', '-s', str(clean), str(patch), str(out)],
                              capture_output=True, text=True)
        if proc.returncode:
            raise RuntimeError('xdelta3 could not decode the patch: ' + proc.stderr[-1000:])
        if out.stat().st_size != RAW_BYTES:
            raise ValueError('Decoded Track 02 has wrong length')
        report['decoded_sha256'] = digest(out)
        changed_sectors = []
        bad_sectors = []
        # Verify raw sector data only where it changed. Source pregap must be identical.
        from xak_iii_disc_utils import verify_mode1_sector
        with clean.open('rb') as a, out.open('rb') as b:
            for sector in range(RAW_BYTES // SECTOR):
                src, dst = a.read(SECTOR), b.read(SECTOR)
                if src == dst:
                    continue
                if sector < PREGAP_BYTES // SECTOR:
                    raise ValueError('Patch unexpectedly changes Track 02 pregap')
                changed_sectors.append(sector)
                if not verify_mode1_sector(dst):
                    bad_sectors.append(sector)
        if bad_sectors:
            raise ValueError(f'EDC/ECC invalid in modified Mode1 sectors {bad_sectors[:12]}')
        report['modified_raw_mode1_sectors'] = changed_sectors
        report['modified_raw_mode1_sector_count'] = len(changed_sectors)
        report['edc_ecc_modified_sectors_valid'] = True
        report['source_sha256_verified'] = True
        report['status'] = 'FULL PATCH DECODE, SOURCE IDENTITY AND EDC/ECC VERIFIED'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('patch', type=Path)
    ap.add_argument('--clean-track02', type=Path)
    ap.add_argument('--report', type=Path)
    ns = ap.parse_args()
    report = inspect_patch(ns.patch)
    if ns.clean_track02:
        full_verify(ns.patch, ns.clean_track02, report)
    if ns.report:
        if ns.report.exists():
            raise FileExistsError(f'Refusing to overwrite existing report: {ns.report}')
        ns.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
