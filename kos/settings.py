"""Setelan runtime yang bisa diubah dari UI (tanpa restart).

Disimpan di data/settings.json. Semua nilai di-clamp ke batas aman supaya
salah ketik (mis. token 999999999) tidak bikin server/providers ngamuk.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FILE = Path(__file__).resolve().parent.parent / "data" / "settings.json"

# nilai awal + batas (min, max) + label buat UI
SPEK: dict[str, dict[str, Any]] = {
    "max_tokens":          {"default": 8000,  "min": 200,   "max": 32000, "step": 100, "label": "Max output tokens",
                            "hint": "Panjang jawaban maksimum. Cerpen 20–30 menit butuh 12000–24000."},
    "temperature":         {"default": 0.75,  "min": 0.0,   "max": 1.5,   "step": 0.05, "label": "Creativity (temperature)",
                            "hint": "Rendah = konsisten, tinggi = lebih bebas/liar. Cerita enak di 0.85–0.95."},
    "llm_timeout":         {"default": 120,   "min": 20,    "max": 600,   "step": 10, "label": "LLM read timeout (s)",
                            "hint": "Jeda antar-chunk sebelum dianggap putus. Naikin buat cerita panjang."},
    "tts_timeout":         {"default": 120,   "min": 20,    "max": 600,   "step": 10, "label": "TTS timeout (s)",
                            "hint": "Batas waktu satu request suara."},
    "tts_max_chars":       {"default": 20000, "min": 500,   "max": 60000, "step": 500, "label": "Max chars per TTS request",
                            "hint": "Batas teks yang boleh dikirim sekali jalan ke mesin suara."},
    "chunk_chars":         {"default": 400,   "min": 120,   "max": 3000,  "step": 20, "label": "Speech chunk size (chars)",
                            "hint": "Kecil = suara mulai lebih cepat, besar = lebih sedikit potongan."},
    "tts_parallel":        {"default": 2,     "min": 1,     "max": 4,     "step": 1, "label": "Parallel TTS requests",
                            "hint": "Berapa potongan digenerate barengan. 2–3 aman; 4 bisa kena rate limit."},
    "history_messages":    {"default": 8,     "min": 0,     "max": 40,    "step": 1, "label": "Conversation history",
                            "hint": "Berapa pesan terakhir dikirim ulang ke model."},
    "story_words":         {"default": 1500,  "min": 300,   "max": 8000,  "step": 100, "label": "Story target (words)",
                            "hint": "Di mode Story, cerita dilanjutkan otomatis sampai panjang ini. 130 kata ≈ 1 menit suara."},
    "memory_chars":        {"default": 1400,  "min": 0,     "max": 6000,  "step": 100, "label": "Memory context (chars)",
                            "hint": "Berapa banyak fakta/memori disisipkan ke prompt."},
}

PRESETS: dict[str, dict[str, Any]] = {
    "default": {},
    "story": {
        "max_tokens": 16000,
        "temperature": 0.9,
        "chunk_chars": 800,
        "tts_parallel": 3,
        "tts_max_chars": 30000,
        "llm_timeout": 240,
        "tts_timeout": 240,
        "story_words": 1800,
    },
    "chat": {
        "max_tokens": 4000,
        "temperature": 0.8,
        "chunk_chars": 400,
        "tts_parallel": 2,
    },
}


def _clamp(key: str, val: Any) -> Any:
    s = SPEK[key]
    try:
        if isinstance(s["default"], float):
            v = round(float(val), 2)
        else:
            v = int(float(val))
    except (TypeError, ValueError):
        v = s["default"]
    return max(s["min"], min(s["max"], v))


def load() -> dict[str, Any]:
    data: dict[str, Any] = {k: v["default"] for k, v in SPEK.items()}
    try:
        if FILE.exists():
            saved = json.loads(FILE.read_text(encoding="utf-8"))
            for k in SPEK:
                if k in saved:
                    data[k] = _clamp(k, saved[k])
    except Exception:  # noqa: BLE001
        pass
    return data


def get(key: str) -> Any:
    return load()[key]


def save(baru: dict[str, Any]) -> dict[str, Any]:
    data = load()
    for k, v in (baru or {}).items():
        if k in SPEK:
            data[k] = _clamp(k, v)
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def preset(nama: str) -> dict[str, Any]:
    if nama not in PRESETS:
        raise ValueError(f"preset tidak dikenal: {nama}")
    base = {k: v["default"] for k, v in SPEK.items()}
    base.update(PRESETS[nama])
    return save(base)


def skema() -> dict[str, Any]:
    return {"spec": SPEK, "presets": list(PRESETS), "values": load()}
