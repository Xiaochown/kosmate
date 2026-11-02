"""Mode nyanyi: TTS per suku kata + pitch-shift ke nada lagu.

Kenapa bukan model nyanyi beneran: tidak ada GPU dan Fish Audio itu TTS, bukan
singing model. Trik yang dipakai (sama seperti "speech-to-song" klasik):
  1. lirik dipecah jadi suku kata
  2. tiap suku kata disintesis pendek lewat TTS
  3. tiap potongan digeser nadanya ke nada target (ffmpeg asetrate + atempo)
  4. dipotong/dipanjangkan sesuai durasi not, lalu digabung

Hasilnya bukan penyanyi studio, tapi nadanya mengikuti lagu yang diminta.
"""
from __future__ import annotations

import asyncio
import math
import re
import subprocess
import tempfile
from pathlib import Path

from . import tts

# ---------------------------------------------------------------- melodi bawaan
# (nada MIDI, ketukan). Hanya lagu domain publik / lagu anak.
MELODI: dict[str, dict] = {
    "pelangi": {
        "judul": "Pelangi (nada Twinkle Twinkle)",
        "bpm": 100,
        "nada": [
            (60, 1), (60, 1), (67, 1), (67, 1), (69, 1), (69, 1), (67, 2),
            (65, 1), (65, 1), (64, 1), (64, 1), (62, 1), (62, 1), (60, 2),
        ],
    },
    "twinkle": {
        "judul": "Twinkle Twinkle Little Star",
        "bpm": 100,
        "nada": [
            (60, 1), (60, 1), (67, 1), (67, 1), (69, 1), (69, 1), (67, 2),
            (65, 1), (65, 1), (64, 1), (64, 1), (62, 1), (62, 1), (60, 2),
        ],
    },
    "birthday": {
        "judul": "Happy Birthday (domain publik)",
        "bpm": 108,
        "nada": [
            (67, 0.75), (67, 0.25), (69, 1), (67, 1), (72, 1), (71, 2),
            (67, 0.75), (67, 0.25), (69, 1), (67, 1), (74, 1), (72, 2),
        ],
    },
    "amazing": {
        "judul": "Amazing Grace (domain publik)",
        "bpm": 84,
        "nada": [
            (67, 1), (72, 2), (72, 0.5), (69, 0.5), (67, 1), (65, 2),
            (67, 1), (72, 2), (72, 0.5), (74, 0.5), (76, 3),
        ],
    },
    "balon": {
        "judul": "Balonku (lagu anak)",
        "bpm": 112,
        "nada": [
            (67, 1), (67, 1), (69, 1), (67, 1), (72, 1), (71, 2),
            (67, 1), (67, 1), (69, 1), (67, 1), (74, 1), (72, 2),
        ],
    },
}

VOKAL = set("aeiouAEIOU")


def pecah_suku(kata: str) -> list[str]:
    """Pemenggalan suku kata Indonesia sederhana (V-K-V).

    'pelangi' -> ['pe','lan','gi'] · 'balonku' -> ['ba','lon','ku']
    'alangkah' -> ['a','lang','kah']
    """
    k = kata
    if not k:
        return []
    out: list[str] = []
    i = 0
    n = len(k)
    while i < n:
        # 1. onset: konsonan sebelum vokal pertama
        j = i
        while j < n and k[j] not in VOKAL:
            j += 1
        if j >= n:                       # sisa konsonan, tempel ke suku terakhir
            if out:
                out[-1] += k[i:]
            else:
                out.append(k[i:])
            break
        # 2. vokal (termasuk diftong seperti 'ai', 'au')
        m = j
        while m < n and k[m] in VOKAL:
            m += 1
        # 3. konsonan setelah vokal
        konson = m
        while konson < n and k[konson] not in VOKAL:
            konson += 1
        if konson >= n:                  # suku terakhir
            out.append(k[i:])
            break
        kelompok = k[m:konson]
        sisip = kelompok[:-1] if len(kelompok) > 1 else ""   # sisakan 1 untuk suku depan
        out.append(k[i:m] + sisip)
        i = m + len(sisip)
    return out or [kata]


def lirik_ke_suku(lirik: str) -> list[tuple[str, bool]]:
    """Kembalikan [(suku, akhir_kata)] supaya jeda antar kata tetap terasa."""
    out: list[tuple[str, bool]] = []
    for kata in re.split(r"\s+", lirik.strip()):
        if not kata:
            continue
        suku = pecah_suku(kata)
        for i, s in enumerate(suku):
            out.append((s, i == len(suku) - 1))
    return out


def ada_ffmpeg() -> bool:
    import shutil

    return bool(shutil.which("ffmpeg"))


_ENV_FF: dict | None = None


def _env_ffmpeg() -> dict:
    """Cari kombinasi LD_LIBRARY_PATH yang benar-benar bisa menjalankan ffmpeg.

    Di proot, menambahkan lib Termux justru merusak (ELF Android vs glibc),
    jadi dicoba satu-satu lalu hasilnya di-cache.
    """
    global _ENV_FF
    if _ENV_FF is not None:
        return _ENV_FF

    import os

    kandidat = [
        None,
        "/usr/lib/aarch64-linux-gnu/blas:/usr/lib/aarch64-linux-gnu/lapack",
        "/usr/lib/aarch64-linux-gnu",
        "/data/data/com.termux/files/usr/lib",
    ]
    for tambahan in kandidat:
        env = dict(os.environ)
        if tambahan:
            env["LD_LIBRARY_PATH"] = tambahan
        else:
            env.pop("LD_LIBRARY_PATH", None)
        try:
            r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=10, env=env)
            if r.returncode == 0:
                _ENV_FF = env
                return env
        except Exception:  # noqa: BLE001
            continue
    _ENV_FF = dict(os.environ)
    return _ENV_FF


def _ff(cmd: list[str], timeout: int = 60) -> bool:
    try:
        subprocess.run(cmd, timeout=timeout, check=True, env=_env_ffmpeg(),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:  # noqa: BLE001
        return False


def _geser_nada(sumber: Path, keluar: Path, semiton: float, durasi: float) -> bool:
    """Geser pitch dengan ffmpeg, lalu paksa durasinya."""
    r = 2 ** (semiton / 12)
    # asetrate mengubah pitch + tempo; atempo mengembalikan tempo
    atempo = max(0.5, min(2.0, 1 / r))
    fil = (
        f"asetrate=44100*{r:.6f},aresample=44100,atempo={atempo:.6f},"
        f"atrim=0:{durasi:.3f},apad=whole_dur={durasi:.3f},"
        "afade=t=in:st=0:d=0.01,afade=t=out:st=" + f"{max(0.0, durasi-0.03):.3f}" + ":d=0.03"
    )
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(sumber), "-af", fil,
           "-ar", "44100", "-ac", "1", str(keluar)]
    ok = _ff(cmd, timeout=30)
    return ok and keluar.exists() and keluar.stat().st_size > 200


async def nyanyi(
    lirik: str,
    lagu: str = "pelangi",
    nada_khusus: list[tuple[int, float]] | None = None,
    bpm: float | None = None,
) -> bytes:
    """Hasilkan MP3 nyanyian. Raise ValueError kalau input tidak masuk akal."""
    if not ada_ffmpeg():
        raise ValueError("mode nyanyi butuh ffmpeg. Di Termux: pkg install ffmpeg")
    suku = lirik_ke_suku(lirik)
    if not suku:
        raise ValueError("lirik kosong")
    if len(suku) > 64:
        raise ValueError("lirik kepanjangan (maks 64 suku kata)")

    if nada_khusus:
        nada = nada_khusus
        tempo = bpm or 100
    else:
        pola = MELODI.get((lagu or "pelangi").lower())
        if not pola:
            raise ValueError("lagu belum ada. pilih: " + ", ".join(MELODI))
        nada = pola["nada"]
        tempo = bpm or pola["bpm"]

    # ulang pola nada kalau suku katanya lebih banyak
    while len(nada) < len(suku):
        nada = nada + nada
    nada = nada[: len(suku)]

    dasar = sorted(n for n, _ in nada)[len(nada) // 2]  # median sebagai acuan

    tmp = Path(tempfile.mkdtemp(prefix="kosmate-sing-"))
    potongan: list[Path] = []
    try:
        for i, ((s, akhir_kata), (nota, ketuk)) in enumerate(zip(suku, nada)):
            durasi = max(0.18, (60.0 / tempo) * ketuk)
            teks = s if not akhir_kata else s + ","
            try:
                audio = b"".join([c async for c in tts._fish(teks, speed=1.0, ref=_ref())])
            except Exception:  # noqa: BLE001
                audio = b""
            if len(audio) < 300:
                continue
            mentah = tmp / f"{i:03d}.mp3"
            mentah.write_bytes(audio)
            jadi = tmp / f"{i:03d}.wav"
            if _geser_nada(mentah, jadi, nota - dasar, durasi):
                potongan.append(jadi)
            # jeda tipis antar kata
            if akhir_kata:
                jeda = max(0.05, 0.02 * durasi)
                diam = tmp / f"{i:03d}-jeda.wav"
                _ff(
                    ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                     "anullsrc=r=44100:cl=mono", "-t", f"{jeda:.3f}", str(diam)],
                    timeout=15,
                )
                if diam.exists():
                    potongan.append(diam)

        if not potongan:
            raise ValueError("gagal membuat suara — cek FISH_API_KEY / kuota TTS")

        daftar = tmp / "daftar.txt"
        daftar.write_text("".join(f"file '{p}'\n" for p in potongan), encoding="utf-8")
        hasil = tmp / "hasil.mp3"
        if not _ff(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", str(daftar), "-ar", "44100", "-b:a", "128k", str(hasil)],
            timeout=120,
        ):
            raise ValueError("gagal menggabungkan audio (ffmpeg)")
        return hasil.read_bytes()
    finally:
        for f in tmp.glob("*"):
            try:
                f.unlink()
            except OSError:
                pass
        try:
            tmp.rmdir()
        except OSError:
            pass


def _ref() -> str:
    from . import voices

    v = voices.active()
    return v.get("ref", "") if v.get("engine") == "fish" else ""


def daftar_lagu() -> list[dict]:
    return [{"kunci": k, "judul": v["judul"], "bpm": v["bpm"], "not": len(v["nada"])}
            for k, v in MELODI.items()]
