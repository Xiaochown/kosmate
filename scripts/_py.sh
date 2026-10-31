#!/usr/bin/env bash
# runner tipis: bash scripts/_py.sh <script.py> [args...]
cd /root/kosmate || exit 1
exec .venv/bin/python "$@"
