#!/usr/bin/env python3
"""Inspect xdelta3/VCDIFF reference patch layout and optionally compare game tracks.

Pure header mode requires only the published .xdelta. Optional --source
strictly verifies an original Japanese track via source-hashes.json,
reconstructs into temporary storage using xdelta3, verifies target
SHA-256, and reports changed raw-sector ranges. Never exports game bytes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

MAGIC = bytes.fromhex("d6c3c400")
SECONDARY = {1: "DJW", 2: "LZMA", 16: "FGK"}
SECTOR = 2352

class FormatError(ValueError):
    pass

def varint(data, p):
    n = 0
    for _ in range(10):
        if p >= len(data):
            raise FormatError("Truncated VCDIFF integer")
        b = data[p]
        p += 1
        n = n * 128 + (b & 127)
        if n > (1 << 63) - 1:
            raise FormatError("Oversized VCDIFF integer")
        if not b & 128:
            return n, p
    raise FormatError("Excessively long VCDIFF integer")

def parse_vcdiff(data):
    if not data.startswith(MAGIC):
        raise FormatError("Not a VCDIFF/xdelta3 file")
    if len(data) < 5:
        raise FormatError("Truncated header")
    p, header = 5, data[4]
    if header & ~7:
        raise FormatError("Unsupported header bits")
    sid = None
    if header & 1:
        if p >= len(data):
            raise FormatError("Missing secondary compressor")
        sid = data[p]
        p += 1
    if header & 2:
        n, p = varint(data, p)
        p += n
    app = None
    if header & 4:
        n, p = varint(data, p)
        if p + n > len(data):
            raise FormatError("Truncated app header")
        app = data[p:p+n].decode("utf8", "replace")
        p += n
    if p > len(data):
        raise FormatError("Truncated code table")
    windows = []
    target_offset = 0
    while p < len(data):
        start, flags = p, data[p]
        p += 1
        if flags & ~7 or flags & 3 == 3:
            raise FormatError("Invalid window flags")
        src_len = src_pos = None
        if flags & 3:
            src_len, p = varint(data, p)
            src_pos, p = varint(data, p)
        delta_len, p = varint(data, p)
        begin = p
        target_len, p = varint(data, p)
        if p >= len(data):
            raise FormatError("Missing delta indicator")
        delta_flags = data[p]
        p += 1
        if delta_flags & ~7:
            raise FormatError("Invalid delta flags")
        data_len, p = varint(data, p)
        inst_len, p = varint(data, p)
        addr_len, p = varint(data, p)
        checksum = None
        if flags & 4:
            if p + 4 > len(data):
                raise FormatError("Truncated Adler-32")
            checksum = data[p:p+4].hex()
            p += 4
        end = p + data_len + inst_len + addr_len
        if end != begin + delta_len or end > len(data):
            raise FormatError("Invalid VCDIFF window length")
        windows.append({
            "file_offset": start, "source_length": src_len,
            "source_offset": src_pos, "target_offset": target_offset,
            "target_length": target_len, "adler32": checksum,
            "compressed_sections": {
                "data": bool(delta_flags & 1),
                "instructions": bool(delta_flags & 2),
                "addresses": bool(delta_flags & 4)},
            "stored_section_bytes": {
                "data": data_len, "instructions": inst_len,
                "addresses": addr_len}})
        target_offset += target_len
        p = end
    return {"patch_bytes": len(data), "compressor_id": sid,
            "compressor": SECONDARY.get(sid),
            "application_header": app,
            "target_bytes": target_offset, "windows": windows}

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def changed_raw_sectors(a, b):
    if a.stat().st_size != b.stat().st_size:
        raise ValueError("Source and target sizes differ")
    if a.stat().st_size % SECTOR:
        raise ValueError("Not raw 2352-byte sectors")
    spans, open_span, changed_bytes, changed_sectors = [], None, 0, 0
    with a.open("rb") as x, b.open("rb") as y:
        for sector in range(a.stat().st_size // SECTOR):
            before, after = x.read(SECTOR), y.read(SECTOR)
            diff = sum(v != w for v, w in zip(before, after))
            if diff:
                changed_bytes += diff
                changed_sectors += 1
                if open_span is None:
                    open_span = {"first": sector, "last": sector, "bytes": diff}
                else:
                    open_span["last"] = sector
                    open_span["bytes"] += diff
            elif open_span is not None:
                spans.append(open_span)
                open_span = None
    if open_span is not None:
        spans.append(open_span)
    return {"changed_sectors": changed_sectors, "changed_bytes": changed_bytes,
            "raw_sector_spans": spans}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--patch", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, help="Public source-hashes.json")
    ap.add_argument("--source", type=Path, help="Your original matching Japanese track")
    ap.add_argument("--xdelta3", default="xdelta3")
    ap.add_argument("--report", type=Path, help="New JSON output file only")
    args = ap.parse_args()
    if args.source and not args.manifest:
        ap.error("--source requires --manifest")
    report = {"patch_name": args.patch.name, "sha256": sha256(args.patch),
              **parse_vcdiff(args.patch.read_bytes())}
    if args.manifest:
        manifest = json.loads(args.manifest.read_text(encoding="utf8"))
        matches = [r for r in manifest["tracks"] if r.get("patch") == args.patch.name]
        if len(matches) != 1 or sha256(args.patch) != matches[0]["patch_sha256"]:
            raise ValueError("Patch does not match published reference manifest")
        row = matches[0]
        report["manifest_verified"] = True
        report["reference_track"] = row["file"]
        if args.source:
            if args.source.stat().st_size != row["bytes"] or sha256(args.source) != row["source_sha256"]:
                raise ValueError("Source game track does not match published manifest")
            exe = shutil.which(args.xdelta3)
            if exe is None:
                raise FileNotFoundError("Install xdelta3 with LZMA support")
            with tempfile.TemporaryDirectory(prefix="xak-ref-") as work:
                output = Path(work) / "patched.bin"
                subprocess.run([exe, "-d", "-s", str(args.source), str(args.patch), str(output)],
                               check=True, capture_output=True)
                if sha256(output) != row["patched_sha256"]:
                    raise ValueError("Decoded target failed published SHA-256")
                report["verified_reconstruction"] = True
                report["sector_diff"] = changed_raw_sectors(args.source, output)
    result = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        with args.report.open("x", encoding="utf8") as f:
            f.write(result)
        print("Report saved:", args.report)
    else:
        print(result, end="")

if __name__ == "__main__":
    main()
