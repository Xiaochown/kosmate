#!/usr/bin/env bash
# jalankan server kosmate di latar (dipakai saat testing di box ini)
cd /root/kosmate || exit 1
PORT="${1:-8080}"
exec .venv/bin/python -m uvicorn kos.app:app --host 0.0.0.0 --port "$PORT"
