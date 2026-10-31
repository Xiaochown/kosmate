"""Tes FISH_API_KEY + 3 voice di model gratis, simpan sampel nyata.

pakai: python scripts/test_fish_key.py
Key dibaca dari .env (FISH_API_KEY). Kalau tidak ada, coba file .fish_key.
Berguna buat memastikan: key valid, model gratis menerima reference voice,
dan tempo tiap voice sesuai.
"""
import json
import pathlib
import subprocess
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent


def baca_key() -> str:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("FISH_API_KEY="):
                v = s.split("=", 1)[1].split("#")[0].strip()
                if v:
                    return v
    f = ROOT / ".fish_key"
    if f.exists():
        return f.read_text().strip()
    raise SystemExit("FISH_API_KEY belum ada di .env — isi dulu: bash scripts/set_key.sh")


KEY = baca_key()
OUT = ROOT / "data" / "samples" / "fish"
OUT.mkdir(parents=True, exist_ok=True)
ENV = {"LD_LIBRARY_PATH": "/usr/lib/aarch64-linux-gnu/blas:/usr/lib/aarch64-linux-gnu/lapack",
       "PATH": "/usr/bin:/bin"}

VOICES = [
    ("miyaa", "37df5d3ba8c74b90b9aa1c6fa646823c", 0.80),
    ("kdm", "41f9f6fa88d74916b9daaf1f1a1a9546", 0.85),
    ("prabowo", "b8d594e696694b499aa12e32d0c1b618", 0.80),
]
TEKS = "Halo Faa, gue Kai. Hari ini gimana? Kalau capek, kita santai dulu aja, gue temenin."


def tts(model: str, ref: str, speed: float, text: str) -> tuple[bool, str, bytes]:
    body = {
        "text": text,
        "format": "mp3",
        "mp3_bitrate": 128,
        "normalize": True,
        "chunk_length": 200,
        "latency": "balanced",
        "prosody": {"speed": speed, "volume": 0, "normalize_loudness": True},
        "reference_id": ref,
    }
    req = urllib.request.Request(
        "https://api.fish.audio/v1/tts",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "model": model},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return True, "ok", r.read()
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:220]}", b""
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}", b""


def cek_wallet() -> None:
    for path in ("/wallet", "/v1/wallet", "/user/wallet"):
        try:
            req = urllib.request.Request("https://api.fish.audio" + path, headers={"Authorization": f"Bearer {KEY}"})
            with urllib.request.urlopen(req, timeout=25) as r:
                print(f"  wallet {path}: {r.read()[:200]}")
                return
        except urllib.error.HTTPError as e:
            if e.code != 404:
                print(f"  wallet {path}: HTTP {e.code}")
        except Exception:
            pass


print("== cek key ==")
cek_wallet()

for model in ("s2.1-pro-free", "s2.1-pro"):
    print(f"\n== model {model} ==")
    for name, ref, speed in VOICES:
        t0 = time.time()
        ok, msg, data = tts(model, ref, speed, TEKS)
        dt = time.time() - t0
        if ok:
            mp3 = OUT / f"nyata_{name}_{model.replace('.', '').replace('-', '_')}.mp3"
            mp3.write_bytes(data)
            ogg = mp3.with_suffix(".ogg")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-c:a", "libopus",
                            "-b:a", "48k", "-ar", "48000", "-ac", "1", str(ogg)], env=ENV, check=False)
            dur = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", str(ogg)], env=ENV, capture_output=True, text=True
            ).stdout.strip()
            print(f"  {name:8s} speed={speed} OK  {len(data):7d} byte  {dt:5.1f}s  durasi={dur}s")
        else:
            print(f"  {name:8s} GAGAL {msg}")
    if model == "s2.1-pro-free":
        print("  (kalau semua gagal 402, berarti free tier menolak reference voice)")
