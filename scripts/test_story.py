import json
import time
import urllib.request


def post(path, body):
    r = urllib.request.Request("http://127.0.0.1:8080" + path, data=json.dumps(body).encode(),
                               method="POST", headers={"content-type": "application/json"})
    return urllib.request.urlopen(r, timeout=30)


post("/api/settings", {"preset": "story"})
post("/api/mode", {"mode": "cerita"})

body = json.dumps({"message": "Bacain cerita pengantar tidur tentang mahasiswa yang tersesat di hutan pinus dan menemukan rumah kecil.",
                   "session": "test-cerita3"}).encode()
r = urllib.request.Request("http://127.0.0.1:8080/api/chat", data=body, method="POST",
                           headers={"content-type": "application/json"})
teks, done, t0 = "", {}, time.time()
with urllib.request.urlopen(r, timeout=560) as resp:
    for raw in resp:
        line = raw.decode("utf-8", "ignore").strip()
        if not line.startswith("data:"):
            continue
        try:
            evt = json.loads(line[5:].strip())
        except Exception:
            continue
        if evt.get("type") == "delta":
            teks += evt["text"]
        elif evt.get("type") == "done":
            done = evt

kata = len(teks.split())
print(f"panjang : {len(teks)} char · {kata} kata → ~{kata/130:.1f} menit dibacakan")
print(f"generate: {time.time()-t0:.0f}s | truncated={done.get('truncated')}")
print("akhir   :", repr(teks[-90:]))
print("penutup sah?", teks.rstrip()[-1:] in ".!?…")
print("potongan TTS @800:", -(-len(teks) // 800))
