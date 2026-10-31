#!/usr/bin/env bash
# smoke test end-to-end (tanpa browser)
set -u
BASE="http://127.0.0.1:8095"
echo "== 1. chat (streaming) =="
START=$(date +%s%3N)
curl -sN -m 90 -X POST "$BASE/api/chat" -H 'content-type: application/json' \
  -d '{"message":"gue baru selesai ujian logika informatika, capek banget. besok ada deadline tugas basis data","session":"smoke"}' \
  | awk '{ printf "%s\n", $0; if (NR==1) { } }' | tail -20
END=$(date +%s%3N)
echo "-- total ms: $((END-START))"

echo
echo "== 2. tunggu ekstraksi memori 12s =="
sleep 12
curl -s -m 10 "$BASE/api/memory/facts?limit=20" | python3 -c "import sys,json;d=json.load(sys.stdin);[print('-',f['predicate'],'=>',f['object']) for f in d['facts']]"

echo
echo "== 3. greeting =="
curl -s -m 60 -X POST "$BASE/api/greeting" | python3 -c "import sys,json;print(json.load(sys.stdin)['text'])"

echo
echo "== 4. tts over http =="
curl -s -m 60 -X POST "$BASE/api/tts" -H 'content-type: application/json' \
  -d '{"text":"Ini tes suara Kosmate. Kalau lu denger ini, berarti jalurnya udah nyambung."}' \
  -o /tmp/kosmate_tts.mp3 -w "http %{http_code} bytes %{size_download} time %{time_total}s\n"

echo
echo "== 5. ganti mode =="
curl -s -m 10 -X POST "$BASE/api/mode" -H 'content-type: application/json' -d '{"mode":"tutor"}'; echo
curl -s -m 10 -X POST "$BASE/api/mode" -H 'content-type: application/json' -d '{"mode":"temen"}'; echo
