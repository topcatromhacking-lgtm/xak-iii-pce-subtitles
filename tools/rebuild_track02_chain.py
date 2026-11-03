#!/usr/bin/env python3
"""Rebuild the pilot Track 02 chain (v0.2 -> v0.3 -> v0.4.1 -> v0.5 -> v0.10) from the
user's own discs and check every step against its SHA-256 pin.

Base = NightWolve English v1.0 Track 02 (from the single-BIN English cue) with the
225-sector Redump pregap of the user's clean Japanese Track 02 in front. That base
plus patches/Xak_III_Pilot01_SUB_TEST_v02_Track02.ips gives the v0.2 Track 02.
The later IPS files are the user's private builds (not in this repo); pass their folder.

  python3 tools/rebuild_track02_chain.py --clean-track02 "...(Track 02).bin" \
      --english-cue "...(English v1.0).cue" --ips-dir PRIVATE_DIR -o build/chain
No game data is written anywhere except the -o directory.
"""
import argparse, hashlib, re
from pathlib import Path

S = 2352
PINS = {  # SHA-256 of each Track 02 build (54,773,376 bytes)
    'v02': 'c69aa8dd', 'v03': 'd87e2850', 'v041': 'fb74bbfd',
    'v05': 'a87babc4dafa0f43091015b86014036978940fdf3c44048409727a0f9acdc207',
    'v10': '64ef0a47',
}
CLEAN_T02 = 'af04551c'
CHAIN = [('v02', 'Xak_III_Pilot01_SUB_TEST_v02_Track02.ips'),
         ('v03', 'Xak_III_Pilot01_SUB_TEST_v03_from_v02_Track02.ips'),
         ('v041', 'Xak_III_Pilot01_SUB_TEST_v041_from_v03_Track02.ips'),
         ('v05', 'Xak_III_Pilot01_SUB_TEST_v05_from_v041_Track02.ips'),
         ('v10', 'Xak_III_Pilot01_v10_from_v05_Track02.ips')]


def ips_apply(src: bytes, patch: bytes) -> bytes:
    d = bytearray(src)
    if patch[:5] != b'PATCH':
        raise ValueError('not an IPS file')
    i = 5
    while patch[i:i + 3] != b'EOF':
        off = int.from_bytes(patch[i:i + 3], 'big'); n = int.from_bytes(patch[i + 3:i + 5], 'big'); i += 5
        if n == 0:
            n = int.from_bytes(patch[i:i + 2], 'big'); seg = bytes([patch[i + 2]]) * n; i += 3
        else:
            seg = patch[i:i + n]; i += n
        if off + n > len(d):
            d.extend(bytes(off + n - len(d)))
        d[off:off + n] = seg
    return bytes(d)


def msf(s: str) -> int:
    m, sec, f = map(int, s.split(':')); return (m * 60 + sec) * 75 + f


def english_track02(cue: Path) -> bytes:
    """Track 02 user sectors from a single-BIN cue (PREGAP not stored)."""
    txt = cue.read_text()
    binf = cue.parent / re.search(r'FILE "([^"]+)"', txt).group(1)
    idx = {}
    for tr, body in re.findall(r'TRACK (\d+) \S+\s*((?:\s*(?:PREGAP|INDEX)[^\n]*\n)+)', txt):
        idx[int(tr)] = {k: msf(v) for k, v in re.findall(r'(PREGAP|INDEX 01) (\d+:\d+:\d+)', body)}
    # PREGAPs are not stored in the BIN, so cue times are file positions and the
    # Track 02 data runs up to Track 03 INDEX 01 (checked against the v0.2 pin).
    start = idx[2]['INDEX 01']; end = idx[3]['INDEX 01']
    with open(binf, 'rb') as f:
        f.seek(start * S); return f.read((end - start) * S)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--clean-track02', required=True, type=Path)
    ap.add_argument('--english-cue', required=True, type=Path)
    ap.add_argument('--ips-dir', type=Path, help='folder with the private v0.3+ IPS files')
    ap.add_argument('--repo-patches', type=Path, default=Path(__file__).resolve().parents[1] / 'patches')
    ap.add_argument('-o', '--out', type=Path, default=Path('build/chain'))
    a = ap.parse_args()
    clean = a.clean_track02.read_bytes()
    h = hashlib.sha256(clean).hexdigest(); print('clean Track 02', h[:16], 'OK' if h.startswith(CLEAN_T02) else 'MISMATCH')
    en = english_track02(a.english_cue)
    cur = clean[:225 * S] + en
    assert len(cur) == len(clean), (len(cur), len(clean))
    a.out.mkdir(parents=True, exist_ok=True)
    ok = True
    for tag, name in CHAIN:
        p = a.repo_patches / name
        if not p.exists() and a.ips_dir:
            p = a.ips_dir / name
        if not p.exists():
            print(f'{tag}: {name} not found, stopping'); break
        cur = ips_apply(cur, p.read_bytes())
        h = hashlib.sha256(cur).hexdigest(); good = h.startswith(PINS[tag]); ok &= good
        print(f'{tag}: {h[:16]} {"OK" if good else "MISMATCH (pin " + PINS[tag][:8] + ")"}')
        (a.out / f'track02_{tag}.bin').write_bytes(cur)
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
