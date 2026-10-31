#!/usr/bin/env bash
# Kosmate :: jalankan otak (server lokal)
# pakai: bash run.sh [port]
set -e
cd "$(dirname "$0")" || exit 1

if [ ! -f .env ]; then
  cp .env.example .env
  echo "!! .env belum ada, gw bikin dari contoh. Isi LLM_API_KEY dulu."
fi

# python mana yang dipakai: hasil install.sh -> .venv -> python sistem
PY=""
if [ -f .kosmate-runtime ]; then
  RUNTIME_CMD="$(cat .kosmate-runtime 2>/dev/null | tr -d '\r\n')"
  if [ -n "$RUNTIME_CMD" ]; then
    if [ -x "$RUNTIME_CMD" ] || command -v "$RUNTIME_CMD" >/dev/null 2>&1; then
      PY="$RUNTIME_CMD"
    fi
  fi
fi
if [ -z "$PY" ]; then
  if [ -x .venv/bin/python ]; then PY=".venv/bin/python"; else PY="python"; fi
fi
if ! "$PY" -c "import starlette" >/dev/null 2>&1; then
  echo "!! dependency belum terpasang untuk: $PY"
  echo "   jalankan dulu: bash scripts/install.sh"
  exit 1
fi

PORT="${1:-$(grep -E '^PORT=' .env | cut -d= -f2)}"
PORT="${PORT:-8080}"
HOST="${KOSMATE_HOST:-0.0.0.0}"

echo "python: $PY"
echo "Kosmate jalan di http://$HOST:$PORT  (di HP: http://127.0.0.1:$PORT)"
exec "$PY" -m uvicorn kos.app:app --host "$HOST" --port "$PORT" --log-level info
