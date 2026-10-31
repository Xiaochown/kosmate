#!/usr/bin/env bash
# uji memori + ukur latency TTFT
set -u
BASE="http://127.0.0.1:8095"

echo "== kirim pesan berisi fakta permanen =="
T0=$(date +%s%3N)
curl -sN -m 120 -X POST "$BASE/api/chat" -H 'content-type: application/json' \
  -d '{"message":"inget ya, gue alergi kacang, tiap Senin jam 8 pagi ada ujian logika informatika di gedung C, dan gue lagi belajar jaringan pakai packet tracer","session":"smoke2"}' \
  > /tmp/chat2.txt
T1=$(date +%s%3N)
echo "total $(($T1-T0)) ms"
grep -o '"type": "delta"' /tmp/chat2.txt | wc -l | xargs echo "jumlah delta chunk:"
grep '"type": "done"' /tmp/chat2.txt | head -1 | cut -c1-400

echo
echo "== tunggu 15s ekstraksi =="
sleep 15
curl -s -m 10 "$BASE/api/memory/facts?limit=20" | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d['facts']),'fakta');[print(' -',f['predicate'],'=>',f['object'][:90]) for f in d['facts'][:10]]"

echo
echo "== retrieval: tanya 'alergi apa' =="
curl -s -m 30 -X POST "$BASE/api/chat" -H 'content-type: application/json' \
  -d '{"message":"gue alergi apa ya? sama jadwal ujian gue kapan?","session":"smoke3"}' \
  | grep '"type": "done"' | python3 -c "import sys,json;line=sys.stdin.read().split('data: ')[-1];print(json.loads(line)['text'])"

echo
echo "== ukur first-byte TTS =="
curl -s -m 60 -X POST "$BASE/api/tts" -H 'content-type: application/json' \
  -d '{"text":"Tes latency suara Kosmate."}' -o /tmp/tts_lat.mp3 \
  -w "ttfb %{time_starttransfer}s total %{time_total}s bytes %{size_download}\n"
