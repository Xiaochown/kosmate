#!/usr/bin/env bash
# ============================================================================
# Kosmate :: deploy / update di HP (Termux). Satu perintah, tanpa ditanya-tanya.
#
#   cd ~/kosmate && bash go.sh
#
# Yang dilakukan:
#   1) ambil kode terbaru dari GitHub (ZIP) — folder data/ & file .env AMAN
#   2) pastikan dependency python siap
#   3) restart server, lalu cek kesehatan
#   4) cetak alamat yang harus dibuka di Chrome
# ============================================================================
set -u

DIR="${KOSMATE_DIR:-$HOME/kosmate}"
cd "$DIR" 2>/dev/null || { echo "  [!!] folder $DIR gak ada"; exit 1; }

ok()   { printf '  [ok] %s\n' "$*"; }
warn() { printf '  [!!] %s\n' "$*"; }
step() { printf '\n== %s ==\n' "$*"; }

VER="$(cat VERSION 2>/dev/null || echo '?')"
printf '\n';
printf '  KOSMATE — cozy farm edition %s\n' "$VER"
printf '  folder: %s\n' "$DIR"

# ---------------------------------------------------------------- 1. kode
step "1/4 ambil kode terbaru"
TMPD="$(mktemp -d 2>/dev/null || echo "$DIR/.tmp-go")"
mkdir -p "$TMPD"
python - "$TMPD/install.sh" <<'PY' 2>/dev/null || cp install.sh "$TMPD/install.sh" 2>/dev/null
import sys, urllib.request
url = "https://raw.githubusercontent.com/Xiaochown/kosmate/main/install.sh"
open(sys.argv[1], "wb").write(urllib.request.urlopen(url, timeout=60).read())
PY
if [ -f "$TMPD/install.sh" ] && KOSMATE_FORCE_ZIP=1 KOSMATE_DIR="$DIR" bash "$TMPD/install.sh" --no-install >/dev/null 2>&1; then
  ok "kode diperbarui (data/ & .env tidak disentuh)"
else
  warn "gagal ambil kode baru — lanjut pakai yang sudah ada"
fi
rm -rf "$TMPD"
[ -f .env ] || cp .env.example .env

# aset wajib ada (kalau ZIP lama, tema baru gak muncul)
MISSING=""
for f in web/style.css web/app.js web/extras.js web/index.html \
         web/assets/mascot.webp web/assets/mascot-listen.webp \
         web/assets/tex-wood-dark.webp web/assets/banner.webp; do
  [ -f "$f" ] || MISSING="$MISSING $f"
done
if [ -z "$MISSING" ]; then ok "aset tema lengkap"; else warn "aset kurang:$MISSING"; fi

# ---------------------------------------------------------- 2. dependency
step "2/4 dependency"
if bash scripts/install.sh >/dev/null 2>&1; then ok "dependency siap"; else warn "dependency ada masalah (server mungkin tetap jalan)"; fi

# --------------------------------------------------------------- 3. key
step "3/4 Fish Audio key"
CUR="$(grep -E '^FISH_API_KEY=' .env 2>/dev/null | head -1 | cut -d= -f2- | tr -d '[:space:]')"
if [ "${#CUR}" -ge 20 ]; then
  ok "FISH_API_KEY sudah terpasang (${#CUR} karakter)"
else
  warn "FISH_API_KEY belum ada -> jalankan: bash scripts/set_key.sh"
fi

# ------------------------------------------------------------ 4. restart
step "4/4 restart + cek"
bash scripts/restart.sh
RC=$?

printf '\n=== SELESAI (versi %s) ===\n' "$VER"
if [ "$RC" = "0" ]; then
  PORT="$(grep -E '^PORT=' .env 2>/dev/null | head -1 | cut -d= -f2- | tr -d '[:space:]')"
  PORT="${PORT:-8080}"
  printf '  buka di Chrome HP ini:\n'
  printf '     http://127.0.0.1:%s\n' "$PORT"
  printf '  ukur layout (kalau tampilan aneh):\n'
  printf '     http://127.0.0.1:%s/?debug=1\n' "$PORT"
  printf '  install sebagai app: Chrome menu (3 titik) -> Install app\n'
  printf '\n  kalau tampilan masih versi lama:\n'
  printf '     tarik-refresh, atau Chrome -> Settings -> Privacy -> clear browsing data\n'
else
  printf '  server belum hidup. 20 baris log terakhir:\n\n'
  tail -20 data/boot.log 2>/dev/null | sed 's/^/    /'
  printf '\n  kirim blok di atas ke gw.\n'
fi
exit "$RC"
