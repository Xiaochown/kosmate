"""Pemilihan voice aktif (bisa diubah dari UI, tanpa edit .env).

Disimpan di data/voice.json supaya pilihan bertahan setelah restart.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import CFG

FILE = CFG.data_dir / "voice.json"

PRESETS: dict[str, dict[str, Any]] = {
    "miyaa": {
        "label": "Miyaa — perempuan muda, ceria",
        "engine": "fish",
        "ref": "37df5d3ba8c74b90b9aa1c6fa646823c",
        "rate": "-20%",
    },
    "kdm": {
        "label": "Kang Dedi — laki-laki, ceria, ekspresif",
        "engine": "fish",
        "ref": "41f9f6fa88d74916b9daaf1f1a1a9546",
        "rate": "-15%",
    },
    "prabowo": {
        "label": "Prabowo — laki-laki, dalam, tegas",
        "engine": "fish",
        "ref": "b8d594e696694b499aa12e32d0c1b618",
        "rate": "-20%",
    },
    "gadis": {
        "label": "Gadis — edge-tts (tanpa Fish)",
        "engine": "edge",
        "ref": "",
        "rate": "-15%",
    },
}

DEFAULT_KEY = "miyaa"


def _read() -> str:
    try:
        if FILE.exists():
            data = json.loads(FILE.read_text(encoding="utf-8"))
            key = str(data.get("key", "")).strip()
            if key in PRESETS:
                return key
    except Exception:  # noqa: BLE001
        pass
    return DEFAULT_KEY


def active_key() -> str:
    return _read()


def active() -> dict[str, Any]:
    key = _read()
    p = dict(PRESETS[key])
    p["key"] = key
    return p


def set_active(key: str) -> dict[str, Any]:
    key = (key or "").strip().lower()
    if key not in PRESETS:
        raise ValueError(f"voice tidak dikenal: {key}")
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps({"key": key}, indent=2), encoding="utf-8")
    return active()


def available() -> list[dict[str, Any]]:
    out = []
    for key, p in PRESETS.items():
        item = dict(p)
        item["key"] = key
        item["ready"] = bool(CFG.fish_key) if p["engine"] == "fish" else True
        out.append(item)
    return out
