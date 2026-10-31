"""Pilih & uji voice Fish Audio untuk Kosmate.

pakai:
  python scripts/fish_voice_set.py --list              # 3 pilihan suara
  python scripts/fish_voice_set.py --preview-all       # tes 3 suara sekaligus (butuh key)
  python scripts/fish_voice_set.py <model_id>          # set + tes suara itu
  python scripts/fish_voice_set.py --test              # uji voice yang sekarang dipakai

Setiap voice punya tempo bawaannya sendiri (ditulis ke TTS_RATE saat dipilih).
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
OUT_DIR = ROOT / "data" / "samples"

# (id, label, tempo) — tempo = rate edge-style; Fish memakai speed = 1 + rate/100
KANDIDAT = [
    ("37df5d3ba8c74b90b9aa1c6fa646823c", "Miyaa — perempuan muda, cheerful, friendly   [DEFAULT]", "-20%"),
    ("41f9f6fa88d74916b9daaf1f1a1a9546", "Kang Dedi Mulyadi — laki-laki, ceria, ekspresif", "-15%"),
    ("b8d594e696694b499aa12e32d0c1b618", "Prabowo — laki-laki, dalam, tegas", "-20%"),
]
DEFAULT_VOICE = KANDIDAT[0][0]

TEKS_UJI = "Halo Faa, gue Kai. Hari ini gimana? Kalau capek, kita santai dulu aja, gue temenin."


def rate_of(mid: str) -> str:
    for cid, _label, rate in KANDIDAT:
        if cid == mid:
            return rate
    return "-20%"


def speed_of(rate: str) -> float:
    m = re.match(r"^([+-]?)(\d{1,2})%$", rate.strip())
    if not m:
        return 0.8
    sign = -1 if m.group(1) == "-" else 1
    return max(0.5, min(1.6, 1 + sign * int(m.group(2)) / 100))


def env_get(key: str) -> str:
    if not ENV.exists():
        return ""
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(key + "="):
            return line.split("=", 1)[1].split("#")[0].strip()
    return ""


def env_set(key: str, val: str) -> None:
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    hit = False
    for i, line in enumerate(lines):
        if line.strip().startswith(key + "="):
            lines[i] = f"{key}={val}"
            hit = True
            break
    if not hit:
        lines.append(f"{key}={val}")
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")


def synth(model_id: str, text: str, rate: str, out_mp3: Path) -> bool:
    key = env_get("FISH_API_KEY")
    if not key:
        print("  [!!] FISH_API_KEY kosong di .env — isi dulu")
        return False
    model = env_get("FISH_MODEL") or "s2.1-pro-free"
    body = {
        "text": text,
        "format": "mp3",
        "mp3_bitrate": 128,
        "normalize": True,
        "chunk_length": 200,
        "latency": "balanced",
        "prosody": {"speed": round(speed_of(rate), 2), "volume": 0, "normalize_loudness": True},
        "reference_id": model_id,
    }
    req = urllib.request.Request(
        "https://api.fish.audio/v1/tts",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "model": model},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        out_mp3.parent.mkdir(parents=True, exist_ok=True)
        out_mp3.write_bytes(data)
        print(f"  [ok] {model} · speed {speed_of(rate)} · {len(data)} byte → {out_mp3.name}")
        return True
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:240]
        print(f"  [!!] HTTP {e.code}: {detail}")
        if e.code == 402:
            print("       model gratis nolak reference voice → coba FISH_MODEL=s2.1-pro (perlu credit)")
        elif e.code == 401:
            print("       API key tidak valid")
        return False
    except Exception as e:  # noqa: BLE001
        print(f"  [!!] {type(e).__name__}: {e}")
        return False


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else "--list"

    if arg in ("--list", "-l"):
        print("Pilihan voice Kosmate (Fish Audio):\n")
        for mid, label, rate in KANDIDAT:
            print(f"  {label}")
            print(f"    id={mid}  tempo={rate} (speed {speed_of(rate)})")
        cur = env_get("FISH_REFERENCE_ID")
        print(f"\nsekarang dipakai: {cur or '(belum diset)'}")
        print("\ntes semua suara dulu : python scripts/fish_voice_set.py --preview-all")
        print("set salah satu       : python scripts/fish_voice_set.py <id>")
        return

    if arg == "--preview-all":
        print("bikin contoh suara untuk 3 pilihan (butuh FISH_API_KEY)…\n")
        ok = 0
        for i, (mid, label, rate) in enumerate(KANDIDAT, 1):
            print(f"{i}. {label.split('[')[0].strip()}  (tempo {rate})")
            name = re.sub(r"[^a-z0-9]+", "_", label.split("—")[0].lower()).strip("_")
            if synth(mid, TEKS_UJI, rate, OUT_DIR / f"preview_{i}_{name}.mp3"):
                ok += 1
        print(f"\n{ok}/3 berhasil. file ada di {OUT_DIR}/preview_*.mp3 — dengerin, lalu set yang paling cocok.")
        return

    if arg == "--test":
        mid = env_get("FISH_REFERENCE_ID")
        if not mid:
            print("FISH_REFERENCE_ID belum diset. pakai --list / --preview-all dulu.")
            return
        print(f"tes voice {mid} …")
        synth(mid, TEKS_UJI, env_get("TTS_RATE") or rate_of(mid), OUT_DIR / "fish_terpilih.mp3")
        return

    if not re.fullmatch(r"[0-9a-f]{24,40}", arg):
        print("model id harus hex 24-40 karakter. lihat --list")
        return

    rate = rate_of(arg)
    print(f"set FISH_REFERENCE_ID = {arg}")
    print(f"set TTS_RATE         = {rate}  (speed {speed_of(rate)})")
    env_set("FISH_REFERENCE_ID", arg)
    env_set("TTS_PROVIDER", "fish")
    env_set("TTS_RATE", rate)
    print("tes sintesis …")
    if synth(arg, TEKS_UJI, rate, OUT_DIR / "fish_terpilih.mp3"):
        print("\naktif. restart biar kepakai:  bash ~/kosmate/update.sh")


if __name__ == "__main__":
    main()
