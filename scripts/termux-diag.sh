#!/usr/bin/env bash
# Kosmate :: diagnosa cepat. Kalau ada yang gagal, kirim output ini ke gw.
set -u
cd "$(dirname "$0")/.." || exit 1
P="$(pwd)"
PORT="$(grep -E '^PORT=' .env 2>/dev/null | cut -d= -f2)"; PORT="${PORT:-8080}"

line(){ printf '\n── %s\n' "$1"; }
ok(){ printf '  [ok]   %s\n' "$1"; }
no(){ printf '  [!!]   %s\n' "$1"; }

printf '===== KOSMATE DIAG =====\n'
printf 'waktu  : %s\n' "$(date)"
printf 'folder : %s\n' "$P"

line "1. environment"
if [ -n "${TERMUX_VERSION:-}" ] || [ -d /data/data/com.termux ]; then ok "Termux terdeteksi"; else no "bukan Termux (jalan di Linux biasa?)"; fi
command -v python >/dev/null && ok "python: $(python -V 2>&1)" || no "python gak ada"
command -v ffmpeg >/dev/null && ok "ffmpeg ada" || no "ffmpeg gak ada (pkg install ffmpeg)"
command -v termux-wake-lock >/dev/null && ok "termux-api ada" || no "termux-api gak ada (pkg install termux-api)"

line "2. venv & dependency"
if [ -x .venv/bin/python ]; then
  ok "venv ada"
  for m in starlette uvicorn httpx; do
    .venv/bin/python -c "import $m" 2>/dev/null && ok "  import $m" || no "  import $m GAGAL"
  done
  .venv/bin/python -c "import edge_tts" 2>/dev/null && ok "  edge-tts ada" || no "  edge-tts gak ada -> butuh FISH_API_KEY"
else
  no "venv gak ada -> bash scripts/install.sh"
fi

line "3. .env"
if [ -f .env ]; then
  ok ".env ada"
  for k in LLM_BASE_URL LLM_MODEL LLM_API_KEY TTS_PROVIDER FISH_API_KEY TTS_VOICE; do
    v="$(grep -E "^$k=" .env | cut -d= -f2-)"
    if [ -z "$v" ]; then no "  $k kosong"
    elif [ "$k" = "LLM_API_KEY" ] || [ "$k" = "FISH_API_KEY" ]; then ok "  $k terisi (${#v} karakter)"
    else ok "  $k = $v"; fi
  done
else
  no ".env gak ada -> cp .env.example .env"
fi

line "4. port & server"
if (command -v ss >/dev/null && ss -ltn 2>/dev/null | grep -q ":$PORT ") || (command -v netstat >/dev/null && netstat -ltn 2>/dev/null | grep -q ":$PORT "); then
  ok "port $PORT kepakai (server mungkin jalan)"
else
  no "port $PORT kosong (server belum jalan)"
fi
if command -v curl >/dev/null; then
  H="$(curl -s -m 6 "http://127.0.0.1:$PORT/api/health" 2>/dev/null)"
  if [ -n "$H" ]; then ok "health: $H"; else no "health gak nyahut"; fi
else
  no "curl gak ada (pkg install curl)"
fi

line "5. memori"
if [ -f data/kosmate.db ]; then
  ok "db ada ($(du -h data/kosmate.db | cut -f1))"
  .venv/bin/python - <<'PY' 2>/dev/null || no "gagal baca db"
import sqlite3, pathlib
c = sqlite3.connect(pathlib.Path("data/kosmate.db"))
for t in ("episodes", "facts", "notes"):
    try:
        print(f"  [ok]   {t}: {c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]} baris")
    except Exception as e:
        print(f"  [!!]   {t}: {e}")
PY
else
  no "db belum ada (normal kalau belum pernah jalan)"
fi

printf '\n===== SELESAI =====\n'
