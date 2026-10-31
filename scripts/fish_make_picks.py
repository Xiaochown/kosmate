import json
import subprocess
import urllib.request
from pathlib import Path

OUT = Path("/root/kosmate/data/samples/fish")
OUT.mkdir(parents=True, exist_ok=True)
CANDS = json.loads((OUT.parent / "fish_candidates.json").read_text())

picks = {
    "A_indonesia_tenang": "25bdf652971e49b1b089cecfd4b1f943",
    "B_drama_halus": "970f714811ad4dd2b7bc2ffae8627901",
    "C_vtuber_rame": "3095f8e1d1fa4b82acaa8aca720a7f83",
}
ENV = {"LD_LIBRARY_PATH": "/usr/lib/aarch64-linux-gnu/blas:/usr/lib/aarch64-linux-gnu/lapack",
       "PATH": "/usr/bin:/bin"}

for name, mid in picks.items():
    item = next((c for c in CANDS if c["id"] == mid), None)
    if not item:
        print("tidak ada:", name)
        continue
    mp3 = OUT / f"{name}.mp3"
    req = urllib.request.Request(item["audio"], headers={"User-Agent": "kosmate"})
    mp3.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    ogg = mp3.with_suffix(".ogg")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-c:a", "libopus",
                    "-b:a", "48k", "-ar", "48000", "-ac", "1", str(ogg)], env=ENV, check=False)
    print(f"{name:22s} {item['title'][:26]:26s} {mp3.stat().st_size:7d} byte -> ogg {ogg.stat().st_size if ogg.exists() else 0} byte")
