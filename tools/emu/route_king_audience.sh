#!/usr/bin/env bash
# route_king_audience.sh CUE TAG (STATES not included; Xvfb :90 must be started by start_session.sh) : boot, load camp slot1, go to King Webis audience, capture cinema
set -e; D="$(cd "$(dirname "$0")" && pwd)"; export LIVE=${LIVE:-/tmp/live}; mkdir -p "$LIVE"; cd "$LIVE"; K="$D/key.sh"
"$D/start_session.sh" "$1" -filesys.fname_sav %f.%x
sleep 6; $K Return; sleep 38; $K Return; sleep 7; $K KP_3; sleep 3; $K KP_3; sleep 3; $K KP_3; sleep 12
$K W 2; sleep 1; $K KP_3; sleep 2; $K KP_3; sleep 5
for i in 1 2 3 4; do $K KP_3; sleep 4; done
mkdir -p ${LIVE:-/tmp/live}/$2
python3 - "$2" "$K" <<'PY'
import subprocess,time,sys
t0=time.time()
for i in range(130):
    subprocess.run([sys.argv[2],'shot',f'{sys.argv[1]}/f{i:03d}'])
    time.sleep(max(0,t0+1.6*(i+1)-time.time()))
PY
kill -INT $(cat pid); sleep 4; pkill -f "Xvfb :90" || true
mv live.mov $2/rec.mov
