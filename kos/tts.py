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


def _cache_path(text: str, voice: str) -> "object":
    key = hashlib.sha1(f"{text}|{CFG.tts_provider}|{voice}|{CFG.fish_ref}".encode()).hexdigest()[:20]
    return CFG.cache_dir / "tts" / f"{key}.mp3"


async def _fish(text: str) -> AsyncIterator[bytes]:
    if not CFG.fish_key:
        raise RuntimeError("FISH_API_KEY kosong")
    body = {
        "text": text,
        "format": "mp3",
        "mp3_bitrate": 128,
        "normalize": True,
        "chunk_length": 200,
        "latency": "balanced",
        "prosody": {"speed": 1.0, "volume": 0, "normalize_loudness": True},
    }
    if CFG.fish_ref:
        body["reference_id"] = CFG.fish_ref
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


async def _edge(text: str, voice: str) -> AsyncIterator[bytes]:
    import edge_tts  # import lokal biar startup cepat

    comm = edge_tts.Communicate(text, voice or CFG.tts_voice, rate=CFG.tts_rate)
    async for chunk in comm.stream():
        if chunk.get("type") == "audio" and chunk.get("data"):
            yield chunk["data"]


def _providers() -> list[str]:
    p = CFG.tts_provider
    if p == "fish":
        return ["fish"]
    if p == "edge":
        return ["edge"]
    return (["fish"] if CFG.fish_key else []) + ["edge"]


async def synth_stream(text: str, voice: str | None = None) -> AsyncIterator[bytes]:
    """Yield potongan MP3. Cache di disk untuk teks pendek."""
    clean = clean_for_speech(text)
    if not clean:
        return
    voice = voice or CFG.tts_voice
    cacheable = len(clean) <= 300
    path = _cache_path(clean, voice)
    if cacheable and path.exists() and path.stat().st_size > 500:
        with open(path, "rb") as fh:
            yield fh.read()
        return

    buf = bytearray()
    errors: list[str] = []
    for name in _providers():
        try:
            if name == "fish":
                agen = _fish(clean)
            else:
                agen = _edge(clean, voice)
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
