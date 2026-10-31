#!/usr/bin/env bash
# Kosmate :: siapkan HP jadi kiosk (butuh ADB dari laptop; opsional)
# pakai: bash scripts/kiosk.sh [ip-hp]
set -u
IP="${1:-}"

if [ -n "$IP" ]; then
  ADB="adb -s $IP:5555"
  adb connect "$IP:5555" >/dev/null 2>&1 || true
else
  ADB="adb"
fi

echo "== cek perangkat =="
$ADB devices | tail -n +2

echo "== izin yang dibutuhkan (setujui di layar HP kalau muncul) =="
$ADB shell pm grant com.android.chrome android.permission.RECORD_AUDIO 2>/dev/null || true

echo "== layar selalu nyala selama dicas =="
$ADB shell settings put global stay_on_while_plugged_in 7

echo "== matikan battery optimization buat Chrome + Termux =="
$ADB shell cmd deviceidle whitelist +com.android.chrome 2>/dev/null || true
$ADB shell cmd deviceidle whitelist +com.termux 2>/dev/null || true

echo "== buka Kosmate di Chrome fullscreen =="
$ADB shell am start -n com.android.chrome/com.google.android.apps.chrome.Main \
  -a android.intent.action.VIEW -d "http://127.0.0.1:8080" >/dev/null 2>&1 || true

echo
echo "CATATAN (lebih penting dari skrip ini):"
echo "- Cara paling gampang tanpa ADB: install 'Fully Kiosk Browser' (gratis),"
echo "  set Start URL = http://127.0.0.1:8080, nyalakan: Keep Screen On,"
echo "  Launch on Boot, Restart on Crash, Enable Webcam/Mic permission,"
echo "  dan matikan battery optimization buat app itu."
echo "- Root/Magisk: pakai 'Battery Charge Limit' set 60-80% biar baterai awet"
echo "  walau dicas 24/7. Tanpa root: colok ke smart plug + timer, atau terima risiko."
