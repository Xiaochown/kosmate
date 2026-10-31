#!/usr/bin/env bash
# Kosmate :: start di Termux, tahan dari dibunuh Android
# pakai: bash scripts/termux-start.sh [port]
set -u
cd "$(dirname "$0")/.." || exit 1

PORT="${1:-8080}"

# 1) cegah Android ngebunuh proses waktu layar mati / app di background
if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock && echo "[kosmate] wake lock aktif"
else
  echo "[kosmate] termux-api belum ada -> 'pkg install termux-api' (biar gak dibunuh Android)"
fi

# 2) browser harus boleh akses mik. localhost = secure context, jadi mic jalan
#    tanpa sertifikat HTTPS. Kalau diakses lewat IP LAN, mic DIBLOK Chrome.
echo "[kosmate] buka di Chrome: http://127.0.0.1:$PORT   (JANGAN pakai IP LAN buat mic)"
if command -v termux-open-url >/dev/null 2>&1; then
  sleep 3 && termux-open-url "http://127.0.0.1:$PORT" >/dev/null 2>&1 &
fi

# 3) jalanin otak
exec bash run.sh "$PORT"
