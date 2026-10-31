#!/usr/bin/env bash
# Kosmate :: restart server + kasih tahu kalau gagal (beserta log-nya)
# pakai: bash scripts/restart.sh [port]
set -u
cd "$(dirname "$0")/.." || exit 1

ok(){ printf '  [ok] %s\n' "$*"; }
warn(){ printf '  [!!] %s\n' "$*"; }

PORT="${1:-$(grep -E '^PORT=' .env 2>/dev/null | cut -d= -f2)}"
PORT="${PORT:-8080}"
mkdir -p data

echo "== hentikan proses lama =="
for p in $(pgrep -f "uvicorn kos.app" 2>/dev/null); do kill "$p" 2>/dev/null; done
sleep 1
if (command -v ss >/dev/null && ss -ltn 2>/dev/null | grep -q ":$PORT ") \
   || (command -v netstat >/dev/null && netstat -ltn 2>/dev/null | grep -q ":$PORT "); then
  warn "port $PORT masih dipakai proses lain:"
  (ss -ltnp 2>/dev/null || netstat -ltnp 2>/dev/null) | grep ":$PORT " | head -3
  warn "coba: bash scripts/restart.sh 8081   (atau tutup app yang pakai port itu)"
  exit 1
fi

command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock
echo "== jalankan =="
nohup bash run.sh "$PORT" > data/boot.log 2>&1 &
for i in $(seq 1 25); do
  sleep 1
  curl -s -m 2 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1 && break
done

H="$(curl -s -m 4 "http://127.0.0.1:$PORT/api/health" 2>/dev/null)"
if [ -n "$H" ]; then
  ok "server hidup di port $PORT"
  echo "$H" | python3 -c "
import sys, json
d = json.load(sys.stdin)
v = d.get('voice', {})
print('     llm    :', d.get('llm'), '| key:', d.get('llm_key'))
print('     suara  :', v.get('label', '-'), '|', v.get('engine', '-'), '|', v.get('rate', '-'))
print('     fish   :', 'ada' if d.get('fish_key') else 'KOSONG (isi via scripts/set_key.sh)')
print('     memori :', d.get('memory'))
print('     tts error terakhir:', d.get('tts_last_error') or '-')
" 2>/dev/null || echo "     $H"
else
  warn "server TIDAK nyahut. 20 baris terakhir log:"
  echo "-----------------------------------------"
  tail -n 20 data/boot.log 2>/dev/null || echo "(log kosong)"
  echo "-----------------------------------------"
  exit 1
fi
