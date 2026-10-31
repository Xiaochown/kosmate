#!/usr/bin/env bash
# unduh browser playwright (buat ukur layout headless)
set -u
PY=/root/.local/share/uv/tools/playwright/bin/python
"$PY" -m playwright install chromium 2>&1 | tail -6
echo "=== cek biner ==="
ls -la /root/.cache/ms-playwright/ 2>/dev/null
