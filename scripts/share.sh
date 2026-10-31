#!/usr/bin/env bash
# Kosmate :: akses dari HP/device lain lewat HTTPS (mic tetap jalan)
#   bash scripts/share.sh            -> mulai tunnel, cetak URL + PIN
#   bash scripts/share.sh --stop     -> matikan tunnel & PIN
#
# Mic browser hanya jalan di HTTPS atau localhost. Tunnel cloudflared ngasih HTTPS,
# jadi ini satu-satunya cara pakai dari device lain tanpa VPS.
set -u
cd "$(dirname "$0")/.." || exit 1
ok(){ printf '  [ok] %s\n' "$*"; }
warn(){ printf '  [!!] %s\n' "$*"; }
mkdir -p data

PORT="$(grep -E '^PORT=' .env 2>/dev/null | cut -d= -f2)"; PORT="${PORT:-8080}"
PY="$(cat .kosmate-runtime 2>/dev/null | tr -d '[:space:]')"
[ -x "${PY:-}" ] || { [ -x .venv/bin/python ] && PY=".venv/bin/python" || PY="python"; }

if [ "${1:-}" = "--stop" ]; then
  pkill -f "cloudflared tunnel --url http://127.0.0.1" 2>/dev/null && ok "tunnel dimatikan" || warn "tidak ada tunnel jalan"
  rm -f data/pin.txt && ok "PIN dihapus (akses publik mati)"
  exit 0
fi

command -v cloudflared >/dev/null 2>&1 || {
  warn "cloudflared belum ada. pasang: pkg install cloudflared (atau pakai binary di ~/.9router/bin)"
  exit 1
}

"$PY" scripts/_health.py "$PORT" >/dev/null 2>&1 || {
  warn "server belum jalan di port $PORT — jalankan: bash scripts/restart.sh"
  exit 1
}

PIN="$("$PY" -c "import sys;sys.path.insert(0,'.');from kos import pin;print(pin.pastikan())")"
ok "PIN aktif: $PIN (dibutuhkan untuk semua akses dari luar)"

pkill -f "cloudflared tunnel --url http://127.0.0.1" 2>/dev/null || true
sleep 1
: > data/tunnel.log
nohup cloudflared tunnel --url "http://127.0.0.1:$PORT" --protocol http2 --no-autoupdate > data/tunnel.log 2>&1 &

URL=""
for i in $(seq 1 30); do
  sleep 1
  URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' data/tunnel.log | head -1)"
  [ -n "$URL" ] && break
done

if [ -z "$URL" ]; then
  warn "tunnel gagal (log: data/tunnel.log)"
  tail -n 12 data/tunnel.log
  exit 1
fi

ok "tunnel hidup"
printf '\n  buka di HP lain (HTTPS = mic jalan):\n'
printf '  %s/?pin=%s\n\n' "$URL" "$PIN"
printf '  matikan: bash scripts/share.sh --stop\n'
printf '  catatan: URL berubah tiap tunnel di-restart; PIN tetap sampai --stop\n'
