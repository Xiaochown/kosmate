#!/usr/bin/env bash
# Kosmate :: update kode + restart server
#   bash ~/kosmate/update.sh
# Jalan baik untuk instalasi via git MAUPUN via zip (tanpa git).
set -u
cd "$(dirname "$0")" || exit 1
ORIG="$(pwd)"

ok(){ printf '  [ok] %s\n' "$*"; }
warn(){ printf '  [!!] %s\n' "$*"; }

if [ -d .git ]; then
  echo "== ambil kode terbaru (git) =="
  if git pull --ff-only >/dev/null 2>&1; then ok "kode terbaru"; else warn "git pull gagal (ada perubahan lokal?)"; fi
else
  echo "== bukan repo git -> unduh versi terbaru (zip) =="
  TMPD="$(mktemp -d 2>/dev/null || echo "$PWD/.tmp-update")"
  mkdir -p "$TMPD"
  cp install.sh "$TMPD/i.sh" 2>/dev/null || { warn "install.sh tidak ada di folder ini"; exit 1; }
  if KOSMATE_FORCE_ZIP=1 KOSMATE_DIR="$ORIG" bash "$TMPD/i.sh" --no-install; then
    ok "kode diperbarui (data/ dan .env aman)"
  else
    warn "gagal ambil update — cek koneksi internet"
    rm -rf "$TMPD"
    exit 1
  fi
  rm -rf "$TMPD"
fi

echo "== cek dependency =="
if bash scripts/install.sh >/dev/null 2>&1; then ok "dependency dicek"; else warn "install.sh melaporkan masalah"; fi

echo "== restart =="
exec bash scripts/restart.sh
