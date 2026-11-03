#!/usr/bin/env bash
# Build the sprite-subtitle prototype HuCard, run it headless in Mednafen,
# and save frames to review/. Usage: tools/pce_proto/run_proto.sh [cue_ids] [frames]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../.." && pwd)"
W=$(mktemp -d); OUT="$ROOT/review"; mkdir -p "$OUT"
python3 "$HERE/gen_proto.py" "$W" ${1:+--cues "$1"} ${2:+--frames "$2"}
cp "$HERE/proto.s" "$W/"; (cd "$W" && ca65 --cpu huc6280 -o proto.o proto.s && ld65 -C "$HERE/proto.cfg" -o proto.pce proto.o)
DISP=:79; Xvfb $DISP -screen 0 1024x768x24 >/dev/null 2>&1 & XP=$!; sleep 1
DISPLAY=$DISP mednafen -sound 0 -video.driver sdl -qtrecord "$W/out.mov" "$W/proto.pce" >"$W/med.log" 2>&1 & MP=$!
sleep 7; kill -INT $MP; sleep 2; kill $XP 2>/dev/null || true
# Mednafen records 1024x464 (4x horizontal, 2x vertical of 256x232 visible).
for t in 1.5 3.5 5.5; do ffmpeg -loglevel error -y -ss $t -i "$W/out.mov" -frames:v 1 "$W/raw_$t.png"; done
python3 - "$W" "$OUT" <<'PY'
import sys; from PIL import Image
w, out = sys.argv[1:]
for i, t in enumerate(["1.5", "3.5", "5.5"], 1):
    im = Image.open(f"{w}/raw_{t}.png").convert("RGB")
    im.resize((im.width // 2, im.height), Image.NEAREST).save(f"{out}/proto_sprite_subs_cue{i}.png")
    print(f"{out}/proto_sprite_subs_cue{i}.png")
PY
cp "$W/proto.pce" "$OUT/proto_sprite_subs.pce"; echo "ROM: $OUT/proto_sprite_subs.pce  work: $W"
