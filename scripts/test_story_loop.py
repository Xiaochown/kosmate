import json
import time
import urllib.request


def post(path, body):
    r = urllib.request.Request("http://127.0.0.1:8080" + path, data=json.dumps(body).encode(),
                               method="POST", headers={"content-type": "application/json"})
    return urllib.request.urlopen(r, timeout=30)


# target besar + max_tokens kecil -> memaksa beberapa kali lanjut otomatis
post("/api/settings", {"values": {"story_words": 3000, "max_tokens": 900}})
post("/api/mode", {"mode": "cerita"})

body = json.dumps({"message": "Cerita pengantar tidur tentang nelayan tua dan laut.", "session": "test-lanjut-cerita"}).encode()
r = urllib.request.Request("http://127.0.0.1:8080/api/chat", data=body, method="POST",
                           headers={"content-type": "application/json"})
teks, done, t0 = "", {}, time.time()
with urllib.request.urlopen(r, timeout=540) as resp:
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
print(f"kata   : {kata} (target 3000)")
print(f"char   : {len(teks)} · ~{kata/130:.1f} menit")
print(f"waktu  : {time.time()-t0:.0f}s | truncated={done.get('truncated')}")
print("akhir  :", repr(teks[-80:]))
