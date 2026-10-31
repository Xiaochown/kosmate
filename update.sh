#!/usr/bin/env bash
# Kosmate :: update kode dari GitHub lalu restart server
#   bash ~/kosmate/update.sh
set -u
cd "$(dirname "$0")" || exit 1

ok(){ printf '  [ok] %s\n' "$*"; }
warn(){ printf '  [!!] %s\n' "$*"; }

if [ -d .git ]; then
  echo "== ambil kode terbaru =="
  if git pull --ff-only; then ok "kode terbaru"; else warn "git pull gagal (ada perubahan lokal?)"; fi
else
  warn "folder ini bukan repo git. Jalankan installer dulu: curl -sL https://raw.githubusercontent.com/Xiaochown/kosmate/main/install.sh | bash"
  exit 1
fi

echo "== cek dependency (kalau ada yang baru) =="
bash scripts/install.sh >/dev/null 2>&1 && ok "dependency dicek" || warn "install.sh melaporkan masalah"

echo "== restart server =="
for p in $(pgrep -f "uvicorn kos.app" 2>/dev/null); do kill "$p" 2>/dev/null; done
sleep 1
PORT="$(grep -E '^PORT=' .env 2>/dev/null | cut -d= -f2)"; PORT="${PORT:-8080}"
mkdir -p data
nohup bash run.sh "$PORT" >> data/boot.log 2>&1 &
for i in $(seq 1 25); do
  sleep 1
  curl -s -m 2 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1 && break
done
if H="$(curl -s -m 4 "http://127.0.0.1:$PORT/api/health" 2>/dev/null)"; then
  ok "server hidup di port $PORT"
  echo "     $H"
else
  warn "server belum nyahut — cek: tail -30 data/boot.log"
fi
