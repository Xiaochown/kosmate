"""TTS Kosmate: Fish Audio (streaming, model gratis) -> fallback edge-tts.

Keduanya menghasilkan MP3, jadi client cukup mainkan <audio> berurutan.
Caching untuk kalimat pendek (sapaan, filler) bikin respons kedua instan.
"""
from __future__ import annotations

import hashlib
import re
from typing import AsyncIterator

import httpx

from .config import CFG
from . import voices

_EMOJI = re.compile(
    "[" "\U0001F300-\U0001FAFF" "\U00002700-\U000027BF" "\U0001F1E6-\U0001F1FF" "\U00002600-\U000026FF" "]+"
)


def clean_for_speech(text: str) -> str:
    t = text or ""
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", t)
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"[*_#>|~]+", " ", t)
    t = _EMOJI.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:1200]


def _cache_path(text: str, voice: str, rate: str, pitch: str) -> "object":
    key = hashlib.sha1(
        f"{text}|{CFG.tts_provider}|{voice}|{CFG.fish_ref}|{rate}|{pitch}".encode()
    ).hexdigest()[:20]
    return CFG.cache_dir / "tts" / f"{key}.mp3"


async def _fish(text: str, speed: float = 1.0, ref: str = "") -> AsyncIterator[bytes]:
    if not CFG.fish_key:
        raise RuntimeError("FISH_API_KEY kosong di .env — voice Fish belum bisa dipakai")
    body = {
        "text": text,
        "format": "mp3",
        "mp3_bitrate": 128,
        "normalize": True,
        "chunk_length": CFG.fish_chunk,
        "latency": CFG.fish_latency,
        "prosody": {"speed": round(speed, 2), "volume": 0, "normalize_loudness": True},
    }
    use_ref = ref or CFG.fish_ref
    if use_ref:
        body["reference_id"] = use_ref
    headers = {
        "Authorization": f"Bearer {CFG.fish_key}",
        "Content-Type": "application/json",
        "model": CFG.fish_model,
    }
    timeout = httpx.Timeout(60.0, connect=15.0, read=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", "https://api.fish.audio/v1/tts", json=body, headers=headers) as r:
            if r.status_code >= 400:
                detail = (await r.aread()).decode("utf-8", "ignore")[:300]
                raise RuntimeError(f"fish {r.status_code}: {detail}")
            async for chunk in r.aiter_bytes(4096):
                if chunk:
                    yield chunk


async def _edge(text: str, voice: str, rate: str, pitch: str) -> AsyncIterator[bytes]:
    import edge_tts  # import lokal biar startup cepat

    comm = edge_tts.Communicate(
        text, voice or CFG.tts_voice, rate=rate, pitch=pitch, volume=CFG.tts_volume
    )
    async for chunk in comm.stream():
        if chunk.get("type") == "audio" and chunk.get("data"):
            yield chunk["data"]


def _providers() -> list[str]:
    """Engine TTS yang dipakai.

    PENTING: kalau voice yang dipilih berbasis Fish, TIDAK ADA fallback ke edge.
    Lebih baik diam + kasih error yang jelas daripada tiba-tiba ganti suara jelek.
    """
    v = voices.active()
    if v.get("engine") == "fish":
        return ["fish"]
    return ["edge"]


def _rate_to_speed(rate: str) -> float:
    m = re.match(r"^([+-]?)(\d{1,2})%$", (rate or "").strip())
    if not m:
        return 1.0
    sign = -1 if m.group(1) == "-" else 1
    return max(0.5, min(1.6, 1 + sign * int(m.group(2)) / 100))


async def synth_stream(
    text: str, voice: str | None = None, rate: str | None = None
) -> AsyncIterator[bytes]:
    """Yield potongan MP3. Satu suara saja (dikunci), tempo bisa diatur."""
    clean = clean_for_speech(text)
    if not clean:
        return

    # voice aktif ditentukan dari pilihan user (data/voice.json)
    v = voices.active()
    use_ref = v.get("ref", "") if v.get("engine") == "fish" else ""
    use_voice = "fish" if use_ref else CFG.tts_voice
    use_rate = (rate or v.get("rate") or CFG.tts_rate).strip()
    use_pitch = CFG.tts_pitch

    cacheable = len(clean) <= 300
    path = _cache_path(clean, f"{use_voice}:{use_ref or 'default'}", use_rate, use_pitch)
    if cacheable and path.exists() and path.stat().st_size > 500:
        with open(path, "rb") as fh:
            yield fh.read()
        return

    buf = bytearray()
    errors: list[str] = []
    for name in _providers():
        try:
            if name == "fish":
                agen = _fish(clean, _rate_to_speed(use_rate), use_ref)
            else:
                agen = _edge(clean, use_voice, use_rate, use_pitch)
            async for chunk in agen:
                buf.extend(chunk)
                yield chunk
            if buf:
                if cacheable:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(bytes(buf))
                return
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {e}")
            if buf:  # sudah ada audio terkirim, jangan dobel
                return
    raise RuntimeError("TTS gagal semua provider -> " + " | ".join(errors))
