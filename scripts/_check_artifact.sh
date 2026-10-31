#!/usr/bin/env bash
# verifikasi artefak zip yang dikirim ke user
set -u
ZIP="/sdcard/Download/kosmate/kosmate.zip"
WORK=/tmp/chk_art

rm -rf "$WORK"
mkdir -p "$WORK"
cd "$WORK" || exit 1
unzip -q "$ZIP" || { echo "GAGAL unzip"; exit 1; }
unzip -t "$ZIP" >/dev/null && echo "zip utuh: OK"

cd kosmate || exit 1
echo "--- file kunci ---"
for f in scripts/autoinstall.sh scripts/install.sh scripts/_write_env.py run.sh scripts/termux-start.sh scripts/termux-boot.sh scripts/termux-diag.sh docs/TUTORIAL.html; do
  [ -e "$f" ] && printf '  ada   %s\n' "$f" || printf '  HILANG %s\n' "$f"
done

echo "--- syntax shell ---"
for f in scripts/autoinstall.sh scripts/install.sh run.sh scripts/termux-start.sh scripts/termux-boot.sh scripts/termux-diag.sh; do
  bash -n "$f" && printf '  ok  %s\n' "$f" || printf '  ERR %s\n' "$f"
done

echo "--- syntax python ---"
/root/kosmate/.venv/bin/python -m py_compile kos/*.py scripts/_write_env.py && echo "  ok  semua modul python"

echo "--- dependency yang dipakai (tanpa pydantic) ---"
grep -vE "^#|^$" requirements.txt | sed 's/^/  /'
