#!/usr/bin/env bash
# cari username Termux (u0_aNNN) yang menerima key kita
IP="${1:-192.168.1.17}"
PORT="${2:-8022}"
KEY="/root/.ssh/kosmate_poco"
OUT=/tmp/ssh_found.txt
: > "$OUT"

try() {
  u="$1"
  if ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        -o ConnectTimeout=3 -o PreferredAuthentications=publickey -o PubkeyAuthentication=yes \
        -i "$KEY" -p "$PORT" "$u@$IP" 'echo MASUK; whoami; getprop ro.product.model 2>/dev/null' \
        >/tmp/try_$u.log 2>/dev/null; then
    echo "FOUND $u" >> "$OUT"
    cp "/tmp/try_$u.log" "/tmp/ssh_ok_$u.txt"
  fi
  rm -f "/tmp/try_$u.log"
}
export -f try
export IP PORT KEY OUT

seq 100 260 | xargs -P 16 -I{} bash -c 'try "u0_a{}"' 2>/dev/null
echo "--- hasil ---"
cat "$OUT" 2>/dev/null || true
[ -s "$OUT" ] || echo "belum ketemu di rentang u0_a100..u0_a260"
