#!/usr/bin/env bash
# start.sh CUE [extra mednafen args]  -> persistent session on :90
export DISPLAY=:90
pkill -f "Xvfb :90"; sleep 0.5
Xvfb :90 -screen 0 1280x960x24 >/dev/null 2>&1 &
sleep 1
CUE="$1"; shift; rm -f ${LIVE:-/tmp/live}/live.mov
SDL_AUDIODRIVER=dummy nohup mednafen -sound 1 -sound.driver sdl -video.driver sdl -qtrecord ${LIVE:-/tmp/live}/live.mov "$@" "$CUE" > ${LIVE:-/tmp/live}/med.log 2>&1 &
echo $! > ${LIVE:-/tmp/live}/pid; for i in $(seq 40); do sleep 0.5; W=$(xdotool search --pid $(cat ${LIVE:-/tmp/live}/pid) 2>/dev/null | tail -1); [ -n "$W" ] && break; done; sleep 1
xdotool search --pid $(cat ${LIVE:-/tmp/live}/pid) | tail -1 > ${LIVE:-/tmp/live}/wid
