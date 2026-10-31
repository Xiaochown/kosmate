import json
import subprocess
import urllib.request
from pathlib import Path

IDS = {
    "prabowo_b8d594": "b8d594e696694b499aa12e32d0c1b618",
    "kedua_37df5d": "37df5d3ba8c74b90b9aa1c6fa646823c",
}
OUT = Path("/root/kosmate/data/samples/fish")
OUT.mkdir(parents=True, exist_ok=True)
ENV = {"LD_LIBRARY_PATH": "/usr/lib/aarch64-linux-gnu/blas:/usr/lib/aarch64-linux-gnu/lapack",
       "PATH": "/usr/bin:/bin"}


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "kosmate"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


for name, mid in IDS.items():
    print("=" * 70)
    try:
        m = get(f"https://api.fish.audio/model/{mid}")
    except Exception as e:  # noqa: BLE001
        print(f"{name}: gagal ambil metadata -> {e}")
        continue
    print(f"title      : {m.get('title')}")
    print(f"id         : {m.get('_id')}")
    print(f"deskripsi  : {(m.get('description') or '')[:140]}")
    print(f"tags       : {m.get('tags')}")
    print(f"bahasa     : {m.get('languages')}")
    print(f"likes/task : {m.get('like_count')} / {m.get('task_count')}")
    print(f"author     : {(m.get('author') or {}).get('name')}")
    samples = m.get("samples") or []
    print(f"samples    : {len(samples)}")
    for i, s in enumerate(samples[:3]):
        print(f"  [{i}] {s.get('title')} :: {(s.get('text') or '')[:90]}")
        print(f"      {s.get('audio')}")
    if samples:
        mp3 = OUT / f"{name}.mp3"
        req = urllib.request.Request(samples[0]["audio"], headers={"User-Agent": "kosmate"})
        mp3.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        ogg = mp3.with_suffix(".ogg")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-c:a", "libopus",
                        "-b:a", "48k", "-ar", "48000", "-ac", "1", str(ogg)], env=ENV, check=False)
        print(f"  -> tersimpan {mp3.name} ({mp3.stat().st_size} byte), ogg={ogg.exists()}")
