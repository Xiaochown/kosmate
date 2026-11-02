"""Uji endpoint /api/sing lewat HTTP (bukan cuma fungsi internal)."""
import json
import time
import urllib.request

B = "http://127.0.0.1:8080"


def post(path, body):
    req = urllib.request.Request(B + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=180)


print("--- 1. daftar lagu ---")
songs = json.load(urllib.request.urlopen(B + "/api/sing/songs", timeout=15))
for s in songs["items"]:
    print(f"  {s['kunci']:10s} {s['judul']}")

print("\n--- 2. nyanyi 5 kata (lagu balon) ---")
t0 = time.time()
try:
    r = post("/api/sing", {"lirik": "balonku ada lima rupa", "lagu": "balon"})
    audio = r.read()
    print(f"  status {r.status} · {len(audio)//1024} KB · {time.time()-t0:.1f} detik")
    open("/tmp/nyanyi-http.mp3", "wb").write(audio)
    print("  disimpan /tmp/nyanyi-http.mp3")
except Exception as e:  # noqa: BLE001
    print("  GAGAL:", type(e).__name__, str(e)[:200])

print("\n--- 3. lagu tidak dikenal harus 400 ---")
try:
    post("/api/sing", {"lirik": "tes", "lagu": "lagu-plagiat"})
    print("  TIDAK menolak (salah)")
except urllib.error.HTTPError as e:
    print("  ditolak:", e.code, e.read().decode()[:80])

print("\n--- 4. lirik kosong harus 400 ---")
try:
    post("/api/sing", {"lirik": "   ", "lagu": "balon"})
    print("  TIDAK menolak (salah)")
except urllib.error.HTTPError as e:
    print("  ditolak:", e.code)

print("\n--- 5. metrik sing tercatat ---")
m = json.load(urllib.request.urlopen(B + "/api/metrics", timeout=15))
print("  sing:", m.get("sing"))
print("  tts_first_byte:", m.get("tts_first_byte"))
