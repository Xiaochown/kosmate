#!/usr/bin/env bash
# uji semua endpoint versi Starlette
set -u
B="${1:-http://127.0.0.1:8098}"
pass=0; fail=0
chk(){ if [ "$2" = "$3" ]; then printf '  [ok]   %-42s %s\n' "$1" "$2"; pass=$((pass+1)); else printf '  [!!]   %-42s dapat=%s harap=%s\n' "$1" "$2" "$3"; fail=$((fail+1)); fi }

code(){ curl -s -o /dev/null -w '%{http_code}' -m 20 "$@"; }

chk "GET  /api/health"            "$(code "$B/api/health")" 200
chk "GET  / (index)"             "$(code "$B/")" 200
chk "GET  /style.css"            "$(code "$B/style.css")" 200
chk "GET  /api/memory/stats"     "$(code "$B/api/memory/stats")" 200
chk "GET  /api/memory/context"   "$(code "$B/api/memory/context?q=ujian")" 200
chk "GET  /api/memory/search"    "$(code "$B/api/memory/search?q=kopi")" 200
chk "GET  /api/export"           "$(code "$B/api/export")" 200
chk "POST /api/mode"             "$(code -X POST -H 'content-type: application/json' -d '{"mode":"tutor"}' "$B/api/mode")" 200
chk "POST /api/mode invalid"     "$(code -X POST -H 'content-type: application/json' -d '{"mode":"xxx"}' "$B/api/mode")" 400
chk "POST /api/tts"              "$(code -X POST -H 'content-type: application/json' -d '{"text":"tes suara starlette"}' "$B/api/tts")" 200
chk "POST /api/tts kosong"       "$(code -X POST -H 'content-type: application/json' -d '{"text":""}' "$B/api/tts")" 400
chk "POST /api/greeting"         "$(code -X POST "$B/api/greeting")" 200
chk "POST /api/chat kosong"      "$(code -X POST -H 'content-type: application/json' -d '{"message":""}' "$B/api/chat")" 400

FID=$(curl -s -m 15 -X POST -H 'content-type: application/json' \
  -d '{"predicate":"tes","object":"endpoint starlette"}' "$B/api/memory/facts" \
  | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id"))')
chk "POST /api/memory/facts"     "$([ "$FID" != "None" ] && echo ok || echo gagal)" ok
chk "DELETE /api/memory/facts/id" "$(code -X DELETE "$B/api/memory/facts/$FID")" 200

printf 'dummy' > /tmp/tiny.wav
chk "POST /api/stt (file kecil)"  "$(code -F "audio=@/tmp/tiny.wav" "$B/api/stt")" 200
chk "POST /api/stt tanpa file"    "$(code -X POST "$B/api/stt")" 400

echo
echo "hasil: $pass lolos, $fail gagal"
