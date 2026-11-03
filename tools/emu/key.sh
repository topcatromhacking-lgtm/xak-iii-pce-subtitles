#!/usr/bin/env bash
# k.sh KEY [holdsec] ; k.sh shot NAME
export DISPLAY=:90; W=$(cat ${LIVE:-/tmp/live}/wid)
if [ "$1" = shot ]; then import -window $W ${LIVE:-/tmp/live}/$2.png; exit; fi
xdotool keydown --window $W $1; sleep ${2:-0.15}; xdotool keyup --window $W $1
