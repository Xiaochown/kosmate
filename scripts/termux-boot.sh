#!/usr/bin/env bash
# Kosmate :: autostart waktu HP nyala (butuh app Termux:Boot dari F-Droid)
# cara pakai:
#   mkdir -p ~/.termux/boot
#   cp scripts/termux-boot.sh ~/.termux/boot/10-kosmate.sh
#   chmod +x ~/.termux/boot/10-kosmate.sh
set -u

# tunggu wifi/LAN siap
sleep 20
termux-wake-lock 2>/dev/null || true

cd "$HOME/kosmate" || exit 1
nohup bash run.sh 8080 >> "$HOME/kosmate/data/boot.log" 2>&1 &

sleep 6
termux-open-url "http://127.0.0.1:8080" 2>/dev/null || true
