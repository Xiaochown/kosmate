#!/usr/bin/env bash
# Kosmate :: instalasi di Termux (HP Android, TANPA root, TANPA proot)
# Tahan terhadap: pip rusak setelah upgrade python, venv gak bisa dibuat,
# uv gak ada, edge-tts gagal dikompilasi.
#
# jalankan: bash scripts/install.sh
set -u
cd "$(dirname "$0")/.." || exit 1

say(){ printf '%s\n' "$*"; }
ok(){ printf '   [ok] %s\n' "$*"; }
warn(){ printf '   [!!] %s\n' "$*"; }
step(){ printf '\n== %s ==\n' "$*"; }

step "0/7 cek environment"
if [ -n "${TERMUX_VERSION:-}" ] || [ -d /data/data/com.termux ]; then
  ok "Termux terdeteksi"
else
  warn "bukan Termux — kalau ini Linux biasa, pakai: python -m venv .venv"
fi

step "1/7 paket sistem"
# Cepat: hanya panggil pkg kalau benar-benar ada yang kurang.
# `pkg update` + ffmpeg (±50 MB) sering bikin instalasi menggantung lama.
BUTUH=""
for b in python git; do
  command -v "$b" >/dev/null 2>&1 || BUTUH="$BUTUH $b"
done
if [ -n "$BUTUH" ] && [ "${KOSMATE_SKIP_PKG:-0}" != "1" ]; then
  say "   paket kurang:$BUTUH — memasang…"
  pkg update -y >/dev/null 2>&1 || true
  pkg install -y $BUTUH >/dev/null 2>&1 || true
else
  ok "paket sistem sudah lengkap — pkg dilewati (cepat)"
fi
ok "python: $(python -V 2>&1)"
if command -v ffmpeg >/dev/null; then
  ok "ffmpeg ada"
else
  ok "ffmpeg tidak ada — tidak wajib (cuma buat konversi audio opsional)"
fi

step "2/7 perbaiki pip kalau rusak"
# Gejala umum: /usr/bin/pip nunjuk ke python3.13 padahal python sudah 3.14
# (terjadi setelah `pkg upgrade`). Rantai perbaikan dari paling ringan:
#   1. ensurepip        2. paket python-pip   3. termux-fix-shebang
#   4. reinstall python 5. get-pip.py
pip_ok(){ python -m pip --version >/dev/null 2>&1; }

if pip_ok; then
  ok "pip sehat ($(python -m pip --version 2>/dev/null | cut -d' ' -f1-2))"
else
  warn "pip rusak (bad interpreter) — memperbaiki otomatis"

  python -m ensurepip --upgrade >/dev/null 2>&1 || true
  pip_ok && ok "dibenerin lewat ensurepip"

  if ! pip_ok; then
    [ "${KOSMATE_SKIP_PKG:-0}" = "1" ] || pkg install -y python-pip >/dev/null 2>&1 || true
    pip_ok && ok "dibenerin lewat paket python-pip"
  fi

  if ! pip_ok && command -v termux-fix-shebang >/dev/null 2>&1; then
    termux-fix-shebang "$PREFIX"/bin/pip "$PREFIX"/bin/pip3 >/dev/null 2>&1 || true
  fi

  if ! pip_ok; then
    warn "reinstall paket python (paling ampuh, ±1 menit)"
    pkg reinstall -y python >/dev/null 2>&1 || true
  fi

  if ! pip_ok && command -v curl >/dev/null 2>&1; then
    warn "coba get-pip.py"
    curl -sSLo /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py 2>/dev/null \
      && python /tmp/get-pip.py >/dev/null 2>&1 || true
  fi

  if pip_ok; then
    ok "pip sekarang sehat ($(python -m pip --version 2>/dev/null | cut -d' ' -f1-2))"
  else
    warn "pip tetap tidak bisa dipakai — coba manual lalu jalankan ulang script ini:"
    say  "     pkg reinstall -y python"
    say  "     curl -sSLo /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py && python /tmp/get-pip.py"
  fi
fi

step "3/7 tentukan cara instalasi"
PYBIN=""
MODE=""

# A. venv yang sudah ada
if [ -x .venv/bin/python ]; then
  if .venv/bin/python -c "import starlette" >/dev/null 2>&1; then
    PYBIN=".venv/bin/python"; MODE="venv-lama"; ok "venv lama masih bagus"
  elif .venv/bin/python -m pip --version >/dev/null 2>&1; then
    PYBIN=".venv/bin/python"; MODE="venv-lama"; ok "venv lama dipakai, dependency dilengkapi"
  else
    warn "venv lama rusak (pip gak jalan) -> dihapus, dibuat ulang"
    rm -rf .venv
  fi
fi

# B. venv baru cara klasik
if [ -z "$MODE" ] && python -m venv .venv >/dev/null 2>&1 \
   && [ -x .venv/bin/python ] && .venv/bin/python -m pip --version >/dev/null 2>&1; then
  PYBIN=".venv/bin/python"; MODE="venv"; ok "venv dibuat"
fi

# C. uv (kalau venv klasik gagal, mis. ensurepip hilang)
if [ -z "$MODE" ]; then
  export UV_LINK_MODE=copy
  if ! command -v uv >/dev/null 2>&1; then
    [ "${KOSMATE_SKIP_PKG:-0}" = "1" ] || pkg install -y uv >/dev/null 2>&1 || true
    command -v uv >/dev/null 2>&1 || python -m pip install -q uv >/dev/null 2>&1 || true
  fi
  if command -v uv >/dev/null 2>&1; then
    if uv venv .venv >/dev/null 2>&1 && [ -x .venv/bin/python ]; then
      PYBIN=".venv/bin/python"; MODE="uv"; ok "venv dibuat pakai uv"
    fi
  fi
fi

# D. jalur terakhir: install ke python sistem (tanpa venv)
if [ -z "$MODE" ]; then
  PYBIN="python"; MODE="sistem"; warn "pakai python sistem (tanpa venv) — aman di Termux"
fi

printf '   mode: %s (%s)\n' "$MODE" "$PYBIN"
echo "$PYBIN" > .kosmate-runtime

step "4/7 dependency inti"
install_deps(){
  local req="$1"
  case "$MODE" in
    venv-lama|venv) "$PYBIN" -m pip install -q --upgrade pip >/dev/null 2>&1 || true
                    "$PYBIN" -m pip install -q -r "$req" ;;
    uv)             uv pip install --python "$PYBIN" -q -r "$req" ;;
    sistem)         "$PYBIN" -m pip install -q -r "$req" \
                      || "$PYBIN" -m pip install -q --break-system-packages -r "$req" ;;
  esac
}

if install_deps requirements.txt; then
  ok "starlette + uvicorn + httpx terpasang"
else
  warn "gagal pasang dependency inti. coba manual:"
  say  "     $PYBIN -m pip install starlette uvicorn httpx python-multipart"
  exit 1
fi

step "5/7 suara (edge-tts) — opsional kalau pakai Fish Audio"
install_one(){ # $1 = nama paket
  case "$MODE" in
    venv-lama|venv|sistem) "$PYBIN" -m pip install -q "$1" 2>/dev/null \
                             || "$PYBIN" -m pip install -q --break-system-packages "$1" 2>/dev/null ;;
    uv)                    uv pip install --python "$PYBIN" -q "$1" 2>/dev/null ;;
  esac
}
if "$PYBIN" -c "import edge_tts" >/dev/null 2>&1; then
  ok "edge-tts sudah ada"
elif install_one edge-tts; then
  ok "edge-tts terpasang (suara gratis tanpa API key)"
else
  warn "edge-tts gagal (butuh kompilasi aiohttp). pasang toolchain dulu..."
  [ "${KOSMATE_SKIP_PKG:-0}" = "1" ] || pkg install -y clang python-dev libffi openssl rust >/dev/null 2>&1 || true
  if install_one edge-tts; then
    ok "edge-tts terpasang setelah pasang toolchain"
  else
    warn "edge-tts tetap gagal — PAKAI FISH AUDIO (model s2.1-pro-free = \$0):"
    say  "     .env -> TTS_PROVIDER=fish + FISH_API_KEY=... + FISH_MODEL=s2.1-pro-free"
    sed -i 's/^edge-tts.*$/# edge-tts (gagal dibangun di perangkat ini)/' requirements.txt 2>/dev/null || true
  fi
fi

step "6/7 folder data"
mkdir -p data/cache/tts
ok "data/ siap"

step "7/7 verifikasi"
"$PYBIN" - <<'PY'
mods = ["starlette", "uvicorn", "httpx"]
for m in mods:
    try:
        __import__(m); print(f"   [ok] import {m}")
    except Exception as e:
        print(f"   [!!] import {m} GAGAL: {e}")
try:
    __import__("edge_tts"); print("   [ok] import edge_tts")
except Exception:
    print("   [!!] edge_tts tidak ada (pakai Fish Audio)")
PY

say ""
say "================================================"
say " selesai. langkah berikutnya:"
say "  1. cp .env.example .env   lalu isi LLM_API_KEY (dan FISH_API_KEY)"
say "  2. bash scripts/termux-start.sh"
say "  3. Chrome -> http://127.0.0.1:8080"
say "================================================"
