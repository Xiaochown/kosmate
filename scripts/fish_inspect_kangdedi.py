import json
import subprocess
import urllib.request
from pathlib import Path

MID = "41f9f6fa88d74916b9daaf1f1a1a9546"
OUT = Path("/root/kosmate/data/samples/fish")
OUT.mkdir(parents=True, exist_ok=True)
ENV = {"LD_LIBRARY_PATH": "/usr/lib/aarch64-linux-gnu/blas:/usr/lib/aarch64-linux-gnu/lapack",
       "PATH": "/usr/bin:/bin"}

req = urllib.request.Request(f"https://api.fish.audio/model/{MID}", headers={"User-Agent": "kosmate"})
m = json.load(urllib.request.urlopen(req, timeout=45))

print("title      :", m.get("title"))
print("id         :", m.get("_id"))
print("deskripsi  :", (m.get("description") or "")[:160])
print("tags       :", m.get("tags"))
print("bahasa     :", m.get("languages"))
print("likes/task :", m.get("like_count"), "/", m.get("task_count"))
print("train_mode :", m.get("train_mode"), "| visibility:", m.get("visibility"))

for i, s in enumerate((m.get("samples") or [])[:3]):
    print(f"  sample[{i}] {s.get('title')} :: {(s.get('text') or '')[:100]}")

samples = m.get("samples") or []
if samples:
    mp3 = OUT / "kangdedi.mp3"
    r = urllib.request.Request(samples[0]["audio"], headers={"User-Agent": "kosmate"})
    mp3.write_bytes(urllib.request.urlopen(r, timeout=60).read())
    # versi 0.85x
    slow = OUT / "kangdedi_085x.mp3"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-filter:a", "atempo=0.85",
                    "-c:a", "libopus", "-b:a", "48k", "-ar", "48000", "-ac", "1",
                    str(OUT / "kangdedi_085x.ogg")], env=ENV, check=False)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3),
                    "-c:a", "libopus", "-b:a", "48k", "-ar", "48000", "-ac", "1",
                    str(OUT / "kangdedi_normal.ogg")], env=ENV, check=False)
    for f in ("kangdedi.mp3", "kangdedi_normal.ogg", "kangdedi_085x.ogg"):
        p = OUT / f
        print(f"  -> {f}: {p.stat().st_size if p.exists() else 'GAGAL'} byte")
