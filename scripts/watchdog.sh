#!/usr/bin/env bash
# Kosmate :: watchdog. Cek server, restart kalau mati, lapor ke Telegram (opsional).
#   bash scripts/watchdog.sh          -> sekali cek
#   bash scripts/watchdog.sh --loop   -> cek tiap 5 menit (biarkan jalan di background)
#
# Set di .env (opsional):
#   TELEGRAM_BOT_TOKEN=123456:ABC...
#   TELEGRAM_CHAT_ID=8948050245
set -u
cd "$(dirname "$0")/.." || exit 1

ok(){ printf '  [ok] %s\n' "$*"; }
warn(){ printf '  [!!] %s\n' "$*"; }

PORT="$(grep -E '^PORT=' .env 2>/dev/null | cut -d= -f2)"; PORT="${PORT:-8080}"
TOKEN="$(grep -E '^TELEGRAM_BOT_TOKEN=' .env 2>/dev/null | cut -d= -f2- | tr -d '[:space:]')"
CHAT="$(grep -E '^TELEGRAM_CHAT_ID=' .env 2>/dev/null | cut -d= -f2- | tr -d '[:space:]')"
PY="$(cat .kosmate-runtime 2>/dev/null | tr -d '[:space:]')"
[ -x "${PY:-}" ] || { [ -x .venv/bin/python ] && PY=".venv/bin/python" || PY="python"; }
mkdir -p data

kirim() {  # pesan via Telegram kalau token+chat ada (pakai python, bukan curl)
  [ -z "$TOKEN" ] && return 0
  [ -z "$CHAT" ] && return 0
  "$PY" - "$TOKEN" "$CHAT" "$1" <<'PY' >/dev/null 2>&1 || true
import sys, urllib.parse, urllib.request
tok, chat, msg = sys.argv[1], sys.argv[2], sys.argv[3]
data = urllib.parse.urlencode({"chat_id": chat, "text": msg[:3500]}).encode()
req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage", data=data)
urllib.request.urlopen(req, timeout=20).read()
PY
}

cek_sekali() {
  if "$PY" scripts/_health.py "$PORT" >/dev/null 2>&1; then
    return 0
  fi
  warn "server mati (port $PORT) — mencoba restart"
  bash scripts/restart.sh "$PORT" >> data/watchdog.log 2>&1
  sleep 3
  if "$PY" scripts/_health.py "$PORT" >/dev/null 2>&1; then
    ok "berhasil dihidupkan lagi"
    kirim "⚠️ Kosmate sempat mati, sudah gue nyalain lagi (port $PORT)."
  else
    warn "gagal dihidupkan — cek data/watchdog.log"
    kirim "❌ Kosmate MATI dan gagal di-restart. Cek HP-nya. (port $PORT)"
    return 1
  fi
}

if [ "${1:-}" = "--loop" ]; then
  echo "watchdog jalan tiap 5 menit (Ctrl+C buat stop)"
  kirim "🟢 Watchdog Kosmate aktif."
  while true; do
    cek_sekali
    sleep 300
  done
fi

cek_sekali && ok "server hidup di port $PORT"
