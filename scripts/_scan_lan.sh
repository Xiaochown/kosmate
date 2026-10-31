#!/usr/bin/env bash
# cari host dengan port 8022 (sshd Termux) di LAN
NET="${1:-192.168.1}"
PORT="${2:-8022}"
scan_one() {
  if nc -z -w 1 "$1" "$PORT" 2>/dev/null; then echo "OPEN $1:$PORT"; fi
}
export -f scan_one
export PORT
seq 1 254 | xargs -P 48 -I{} bash -c 'scan_one "$0.{}"' "$NET" 2>/dev/null
echo "--- selesai scan $NET.0/24 port $PORT ---"
