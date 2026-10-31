"""Pilih & uji voice Fish Audio untuk Kosmate.

pakai:
  python scripts/fish_voice_set.py --list          # lihat kandidat
  python scripts/fish_voice_set.py <model_id>      # set + uji suara itu
  python scripts/fish_voice_set.py --test          # uji voice yang sekarang dipakai

Script ini nulis FISH_REFERENCE_ID ke .env lalu tes sintesis langsung ke Fish.
Butuh FISH_API_KEY sudah terisi di .env.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"

# hasil pencarian pasar voice Fish (language=id), urut prioritas
# DEFAULT: Miyaa (perempuan muda, cheerful, friendly)
KANDIDAT = [
    ("37df5d3ba8c74b90b9aa1c6fa646823c", "Miyaa — perempuan muda, cheerful, friendly  ← DEFAULT"),
    ("b8d594e696694b499aa12e32d0c1b618", "Prabowo — laki-laki, dalam, tegas (143rb pemakaian)"),
    ("25bdf652971e49b1b089cecfd4b1f943", "indonesia — perempuan muda, tenang, conversational"),
    ("970f714811ad4dd2b7bc2ffae8627901", "drama Indonesia — halus, smooth, kalem"),
    ("3095f8e1d1fa4b82acaa8aca720a7f83", "Vestia Zeta — rame/energik, gaya VTuber"),
    ("d0b314896b3a479aa5cb04c29a8e9e25", "Narator Berita Olahraga — jelas, profesional"),
]
DEFAULT_VOICE = KANDIDAT[0][0]


def env_get(key: str) -> str:
    if not ENV.exists():
        return ""
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(key + "="):
            return line.split("=", 1)[1].strip()
    return ""


def env_set(key: str, val: str) -> None:
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(key + "="):
            lines[i] = f"{key}={val}"
            found = True
            break
    if not found:
        lines.append(f"{key}={val}")
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def tes(model_id: str) -> bool:
    key = env_get("FISH_API_KEY")
    if not key:
        print("  [!!] FISH_API_KEY kosong di .env — isi dulu")
        return False
    model = env_get("FISH_MODEL") or "s2.1-pro-free"
    body = {
        "text": "Halo, gue Kai. Suara ini bakal nemenin lu tiap hari.",
        "format": "mp3",
        "mp3_bitrate": 128,
        "normalize": True,
        "chunk_length": 200,
        "latency": "balanced",
        "prosody": {"speed": 0.88, "volume": 0, "normalize_loudness": True},
        "reference_id": model_id,
    }
    req = urllib.request.Request(
        "https://api.fish.audio/v1/tts",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "model": model,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
        out = ROOT / "data" / "samples" / "fish_terpilih.mp3"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print(f"  [ok] suara berhasil dibuat: {len(data)} byte -> {out}")
        return True
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:300]
        print(f"  [!!] HTTP {e.code}: {detail}")
        if e.code == 402:
            print("       model gratis menolak reference suara. Coba FISH_MODEL=s2.1-pro (isi credit dulu).")
        elif e.code == 401:
            print("       key tidak valid.")
        return False
    except Exception as e:  # noqa: BLE001
        print(f"  [!!] {type(e).__name__}: {e}")
        return False


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else "--list"

    if arg in ("--list", "-l"):
        print("Kandidat voice perempuan Indonesia di Fish Audio:\n")
        for mid, note in KANDIDAT:
            print(f"  {mid}  {note}")
        print("\nset salah satu:  python scripts/fish_voice_set.py <model_id>")
        print(f"sekarang dipakai: {env_get('FISH_REFERENCE_ID') or '(belum diset)'}")
        return

    if arg == "--test":
        mid = env_get("FISH_REFERENCE_ID")
        if not mid:
            print("FISH_REFERENCE_ID belum diset. pakai --list dulu.")
            return
        print(f"tes voice {mid} …")
        tes(mid)
        return

    if not re.fullmatch(r"[0-9a-f]{24,40}", arg):
        print("model id harus hex 24-40 karakter. lihat --list")
        return

    print(f"set FISH_REFERENCE_ID = {arg}")
    env_set("FISH_REFERENCE_ID", arg)
    env_set("TTS_PROVIDER", "fish")
    print("tes sintesis …")
    if tes(arg):
        print("\nselesai. restart biar aktif:  bash ~/kosmate/update.sh   (atau restart server)")


if __name__ == "__main__":
    main()
