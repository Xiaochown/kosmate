"""STT fallback sisi server (kalau browser tanpa Web Speech API).

Urutan: Fish Audio ASR (transcribe-1-pro) -> whisper.cpp lokal.
Untuk prototype, jalur utama tetap Web Speech API di browser (gratis, streaming).
"""
from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

import httpx

from .config import CFG


async def _fish_asr(data: bytes, filename: str, language: str) -> str:
    if not CFG.fish_key:
        raise RuntimeError("FISH_API_KEY kosong")
    headers = {"Authorization": f"Bearer {CFG.fish_key}", "model": "transcribe-1-pro"}
    files = {"audio": (filename or "audio.m4a", data, "application/octet-stream")}
    form = {"language": language, "ignore_timestamps": "true", "tag_audio_events": "false"}
    timeout = httpx.Timeout(90.0, connect=15.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post("https://api.fish.audio/v1/asr", headers=headers, files=files, data=form)
        if r.status_code >= 400:
            raise RuntimeError(f"fish asr {r.status_code}: {r.text[:200]}")
        return (r.json().get("text") or "").strip()


async def _whisper_cpp(data: bytes) -> str:
    if not CFG.whisper_bin or not CFG.whisper_model:
        raise RuntimeError("WHISPER_CPP_BIN / WHISPER_MODEL_PATH belum diset")
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "in.audio"
        wav = Path(td) / "in.wav"
        src.write_bytes(data)
        if shutil.which("ffmpeg"):
            p = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(wav),
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            await p.wait()
        target = wav if wav.exists() else src
        p = await asyncio.create_subprocess_exec(
            CFG.whisper_bin, "-m", CFG.whisper_model, "-f", str(target), "-l", CFG.stt_language, "-nt",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await p.communicate()
        return out.decode("utf-8", "ignore").strip()


async def transcribe(data: bytes, filename: str = "audio.m4a", language: str | None = None) -> str:
    lang = language or CFG.stt_language
    chain: list[str]
    if CFG.stt_provider == "none":
        return ""
    if CFG.stt_provider == "fish":
        chain = ["fish"]
    elif CFG.stt_provider == "whispercpp":
        chain = ["whispercpp"]
    else:
        chain = (["fish"] if CFG.fish_key else []) + ["whispercpp"]

    errors: list[str] = []
    for name in chain:
        try:
            txt = await (_fish_asr(data, filename, lang) if name == "fish" else _whisper_cpp(data))
            if txt:
                return txt
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {e}")
    if errors:
        print("[stt] gagal:", " | ".join(errors))
    return ""
