#!/usr/bin/env bash
# =====================================================================
#  KOSMATE :: installer satu baris
#
#    curl -sL https://cdn.jsdelivr.net/gh/Xiaochown/kosmate@main/install.sh | bash
#
#  Alur: paket dasar -> ambil kode (git, atau zip lewat python kalau git rusak)
#        -> jalankan installer interaktif (tanya API key, tes, nyalakan).
#
#  Opsi:
#    bash install.sh --no-install     cuma ambil/update kode
#    KOSMATE_FORCE_ZIP=1 bash ...     paksa jalur unduh zip (buat tes)
# =====================================================================
set -u

REPO="${KOSMATE_REPO:-https://github.com/Xiaochown/kosmate.git}"
REPO_ZIP="${KOSMATE_ZIP:-https://codeload.github.com/Xiaochown/kosmate/zip/refs/heads/main}"
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
if ! command -v python >/dev/null 2>&1; then
  warn "python tidak ada. jalankan: pkg install -y python"
  exit 1
fi
ok "python siap ($(python -V 2>&1))"

step "2/3 ambil kode"

# unduh zip lewat python: tidak memakai libcurl, jadi tetap jalan walau
# curl/git di Termux sedang rusak (mis. simbol ngtcp2 tidak ketemu).
fetch_zip() {
  rm -f "$TMP/kosmate.zip"
  python - "$REPO_ZIP" "$TMP/kosmate.zip" <<'PY' || return 1
import sys, urllib.request
url, out = sys.argv[1], sys.argv[2]
req = urllib.request.Request(url, headers={"User-Agent": "kosmate-installer"})
data = urllib.request.urlopen(req, timeout=120).read()
open(out, "wb").write(data)
print("  [ok] unduh %d byte" % len(data))
PY
  python - "$TMP/kosmate.zip" "$TMP" <<'PY' || return 1
import sys, zipfile
zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])
print("  [ok] ekstrak selesai")
PY
  SRC="$(find "$TMP" -maxdepth 1 -type d -name 'kosmate-*' 2>/dev/null | head -1)"
  [ -d "${SRC:-}" ] || return 1
  mkdir -p "$TMP/kosmate"
  cp -a "$SRC/." "$TMP/kosmate/" || return 1
  return 0
}

if [ -d "$TARGET/.git" ] && [ "${KOSMATE_FORCE_ZIP:-0}" != "1" ]; then
  if git -C "$TARGET" pull --ff-only >/dev/null 2>&1; then
    ok "kode di-update (git pull)"
  else
    warn "git pull gagal, pakai kode yang sudah ada di $TARGET"
  fi
else
  TMP="$(mktemp -d 2>/dev/null || echo "/tmp/kosmate-clone-$$")"
  mkdir -p "$TMP"
  GOT=0

  if [ "${KOSMATE_FORCE_ZIP:-0}" != "1" ] && command -v git >/dev/null 2>&1; then
    if git clone --depth 1 "$REPO" "$TMP/kosmate" >/dev/null 2>&1; then
      ok "repo di-clone (git)"
      GOT=1
    else
      warn "git clone gagal — beralih ke unduh zip lewat python"
    fi
  fi

  if [ "$GOT" = "0" ]; then
    if fetch_zip; then
      ok "kode diunduh lewat python (tanpa git/libcurl)"
      GOT=1
    else
      warn "gagal ambil kode. Cek koneksi internet, lalu coba lagi."
      rm -rf "$TMP"
      exit 1
    fi
  fi

  # pertahankan memori + konfigurasi lama kalau folder tujuan sudah ada
  mkdir -p "$TARGET"
  KEPT=0
  if [ -d "$TARGET/data" ]; then
    mkdir -p "$TMP/kosmate/data"
    cp -a "$TARGET/data/." "$TMP/kosmate/data/" 2>/dev/null && KEPT=1
  fi
  if [ -f "$TARGET/.env" ]; then
    cp -a "$TARGET/.env" "$TMP/kosmate/.env" 2>/dev/null && KEPT=1
  fi
  [ "$KEPT" = "1" ] && ok "memori & .env lama dipertahankan"

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
# `curl ... | bash` bikin stdin berupa pipe, jadi prompt bakal mati.
# Ambil lagi stdin dari terminal supaya installer bisa nanya API key.
if [ ! -t 0 ] && [ -e /dev/tty ]; then
  if { true < /dev/tty; } 2>/dev/null; then
    exec bash scripts/autoinstall.sh < /dev/tty
  fi
fi
exec bash scripts/autoinstall.sh
