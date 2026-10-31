#!/usr/bin/env bash
# =====================================================================
#  KOSMATE :: installer satu baris
#
#    curl -sL https://raw.githubusercontent.com/Xiaochown/kosmate/main/install.sh | bash
#
#  Yang dilakukan: pasang paket dasar -> clone (atau update) repo ke ~/kosmate
#  -> jalankan installer interaktif (tanya API key sekali, tes, nyalakan).
#
#  Opsi:  bash install.sh --no-install   (cuma ambil/update kode, gak install)
# =====================================================================
set -u

REPO="${KOSMATE_REPO:-https://github.com/Xiaochown/kosmate.git}"
TARGET="${KOSMATE_DIR:-$HOME/kosmate}"
NO_INSTALL=0
[ "${1:-}" = "--no-install" ] && NO_INSTALL=1

ok(){   printf '  [ok] %s\n' "$*"; }
warn(){ printf '  [!!] %s\n' "$*"; }
step(){ printf '\n== %s ==\n' "$*"; }

step "1/3 paket dasar"
if command -v pkg >/dev/null 2>&1; then
  pkg install -y git curl python ffmpeg unzip >/dev/null 2>&1 || true
  ok "paket Termux dipasang/dicek"
fi
for c in git curl python; do
  if ! command -v "$c" >/dev/null 2>&1; then
    warn "$c tidak ada. jalankan: pkg install -y git curl python"
    exit 1
  fi
done
ok "git, curl, python siap"

step "2/3 ambil kode"
if [ -d "$TARGET/.git" ]; then
  if git -C "$TARGET" pull --ff-only >/dev/null 2>&1; then ok "kode di-update (git pull)"; else warn "git pull gagal, pakai kode yang ada"; fi
else
  TMP="$(mktemp -d 2>/dev/null || echo "/tmp/kosmate-clone-$$")"
  mkdir -p "$TMP"
  if ! git clone --depth 1 "$REPO" "$TMP/kosmate" >/dev/null 2>&1; then
    warn "clone gagal. cek koneksi / URL repo: $REPO"
    rm -rf "$TMP"; exit 1
  fi
  ok "repo di-clone"

  # pertahankan memori + konfigurasi lama kalau folder tujuan sudah ada
  mkdir -p "$TARGET"
  MOVED=0
  if [ -d "$TARGET/data" ]; then
    mkdir -p "$TMP/kosmate/data"
    cp -a "$TARGET/data/." "$TMP/kosmate/data/" 2>/dev/null && MOVED=1
  fi
  if [ -f "$TARGET/.env" ]; then cp -a "$TARGET/.env" "$TMP/kosmate/.env" 2>/dev/null; MOVED=1; fi
  [ "$MOVED" = "1" ] && ok "memori & .env lama dipindahkan ke kode baru"

  cp -a "$TMP/kosmate/." "$TARGET/" || { warn "gagal menyalin ke $TARGET"; rm -rf "$TMP"; exit 1; }
  rm -rf "$TMP"
  ok "terpasang di $TARGET"
fi
mkdir -p "$TARGET/data"

step "3/3 jalankan installer"
if [ "$NO_INSTALL" = "1" ]; then
  ok "dilewati (--no-install). Kode siap di $TARGET"
  exit 0
fi
cd "$TARGET" || exit 1
exec bash scripts/autoinstall.sh
