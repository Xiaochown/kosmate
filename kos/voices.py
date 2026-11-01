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
    # ---- koleksi suara perempuan (Fish Audio) ----
    "beatrix": {
        "label": "Beatrix — perempuan, tenang",
        "engine": "fish",
        "ref": "0b4a8834f8f34112860472c8229a517f",
        "rate": "-18%",
    },
    "airia": {
        "label": "Airia — perempuan, lembut",
        "engine": "fish",
        "ref": "b38fe0e89d374bae903adb4a104fff9a",
        "rate": "-18%",
    },
    "toktok": {
        "label": "Live Toktok — perempuan, ceria",
        "engine": "fish",
        "ref": "75bf8251e61548498ce786580abfdea7",
        "rate": "-18%",
    },
    "japangirl": {
        "label": "Japan girl — perempuan, imut",
        "engine": "fish",
        "ref": "63bc41e652214372b15d9416a30a60b4",
        "rate": "-18%",
    },
    "egirl": {
        "label": "E-Girl — perempuan, playful",
        "engine": "fish",
        "ref": "98655a12fa944e26b274c535e5e03842",
        "rate": "-18%",
    },
    "venti": {
        "label": "Venti — perempuan, ringan",
        "engine": "fish",
        "ref": "e34c486929524d41b88646b4ac2f382f",
        "rate": "-18%",
    },
    "raiden": {
        "label": "Raiden Shogun — perempuan, dalam",
        "engine": "fish",
        "ref": "5ac6fb7171ba419190700620738209d8",
        "rate": "-20%",
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
