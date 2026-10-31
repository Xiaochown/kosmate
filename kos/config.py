"""Konfigurasi KOSMATE — baca .env tanpa dependency tambahan."""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        # buang komentar inline: "auto   # auto | fish | none" -> "auto"
        v = re.split(r"\s+#", v, maxsplit=1)[0].strip()
        os.environ.setdefault(k, v)


_load_env()


def get(key: str, default: str = "") -> str:
    return (os.environ.get(key) or default).strip()


class Cfg:
    # LLM
    llm_base = get("LLM_BASE_URL", "https://api.teamorouter.com/v1").rstrip("/")
    llm_key = get("LLM_API_KEY")
    llm_model = get("LLM_MODEL", "deepseek-v4-flash-free")
    llm_fallback = get("LLM_MODEL_FALLBACK", "gemini-3.5-flash-lite")

    # TTS
    tts_provider = get("TTS_PROVIDER", "auto").lower()
    fish_key = get("FISH_API_KEY")
    fish_model = get("FISH_MODEL", "s2.1-pro-free")
    fish_ref = get("FISH_REFERENCE_ID")
    # prosodi: chunk lebih panjang = intonasi nyambung (Fish batasnya 100-300)
    fish_chunk = max(100, min(300, int(get("FISH_CHUNK_LENGTH", "300") or 300)))
    fish_latency = get("FISH_LATENCY", "normal")
    # satu suara saja, dikunci. Gadis = satu-satunya voice perempuan id-ID di edge-tts
    tts_voice = get("TTS_VOICE", "id-ID-GadisNeural")
    tts_rate = get("TTS_RATE", "-20%")
    tts_pitch = get("TTS_PITCH", "-2Hz")
    tts_volume = get("TTS_VOLUME", "+0%")
    tts_strict = get("TTS_STRICT", "1") == "1"
    allow_voice_override = get("ALLOW_VOICE_OVERRIDE", "0") == "1"

    # STT
    stt_provider = get("STT_PROVIDER", "auto").lower()
    stt_language = get("STT_LANGUAGE", "id")
    whisper_bin = get("WHISPER_CPP_BIN")
    whisper_model = get("WHISPER_MODEL_PATH")

    # Persona
    assistant_name = get("ASSISTANT_NAME", "Kai")
    user_name = get("USER_NAME", "Faa")
    persona_mode = get("PERSONA_MODE", "temen").lower()

    # Server
    host = get("HOST", "127.0.0.1")
    port = int(get("PORT", "8080"))
    data_dir = Path(get("DATA_DIR", "./data"))
    if not data_dir.is_absolute():
        data_dir = (ROOT / data_dir).resolve()
    db_path = data_dir / "kosmate.db"
    cache_dir = data_dir / "cache"


CFG = Cfg()
CFG.data_dir.mkdir(parents=True, exist_ok=True)
CFG.cache_dir.mkdir(parents=True, exist_ok=True)
