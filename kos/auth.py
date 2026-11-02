"""Token per device + rate limit untuk akses lewat tunnel.

Kenapa: PIN itu satu sandi yang di-share, gampang bocor lewat screenshot/chat, dan
kalau bocor semua endpoint (jurnal, memori, setelan, kuota) terbuka. Token per
device bisa dicabut satu-satu tanpa mengganggu device lain.

Token disimpan di data/tokens.json:
    {"<token>": {"nama": "hp-iqoo", "dibuat": 1699999999, "terakhir": 1699999999}}
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from pathlib import Path

from .config import CFG

FILE: Path = CFG.data_dir / "tokens.json"

# rate limit sederhana: jendela 60 detik
JENDELA = 60
MAKS_UMUM = 240          # request per menit per IP
MAKS_BERAT = 30          # /api/tts dan /api/chat lebih ketat
_semua: dict[str, list[float]] = {}


def _baca() -> dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _tulis(data: dict) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True)
    FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        FILE.chmod(0o600)
    except OSError:
        pass


def daftar() -> list[dict]:
    out = []
    for tok, info in _baca().items():
        out.append({
            "nama": info.get("nama", "?"),
            "dibuat": info.get("dibuat", 0),
            "terakhir": info.get("terakhir", 0),
            "sidik": sidik(tok),
        })
    return out


def sidik(token: str) -> str:
    """Hanya sidik pendek untuk ditampilkan (token asli tidak pernah dicetak ulang)."""
    return hashlib.sha256(token.encode()).hexdigest()[:8]


def buat(nama: str = "device") -> str:
    token = secrets.token_urlsafe(24)
    data = _baca()
    data[token] = {"nama": (nama or "device")[:40], "dibuat": int(time.time()), "terakhir": 0}
    _tulis(data)
    return token


def cabut(nama_atau_sidik: str) -> bool:
    data = _baca()
    for tok in list(data):
        if data[tok].get("nama") == nama_atau_sidik or sidik(tok) == nama_atau_sidik:
            del data[tok]
            _tulis(data)
            return True
    return False


def cocok(token: str | None) -> bool:
    if not token:
        return False
    data = _baca()
    if token not in data:
        return False
    data[token]["terakhir"] = int(time.time())
    try:
        _tulis(data)
    except Exception:  # noqa: BLE001
        pass
    return True


def ada_token() -> bool:
    return bool(_baca())


def batasi(ip: str, berat: bool = False) -> bool:
    """True kalau masih boleh. False = kena rate limit."""
    sekarang = time.time()
    kunci = f"{ip}|{'berat' if berat else 'umum'}"
    jejak = [t for t in _semua.get(kunci, []) if sekarang - t < JENDELA]
    batas = MAKS_BERAT if berat else MAKS_UMUM
    if len(jejak) >= batas:
        _semua[kunci] = jejak
        return False
    jejak.append(sekarang)
    _semua[kunci] = jejak
    # bersihkan kunci yang sudah kosong biar tidak menumpuk
    if len(_semua) > 500:
        for k in [k for k, v in _semua.items() if not any(sekarang - t < JENDELA for t in v)]:
            _semua.pop(k, None)
    return True
