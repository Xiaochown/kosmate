"""PIN gate sederhana untuk akses lewat tunnel publik.

PIN dibaca dari data/pin.txt setiap request (jadi bisa diganti tanpa restart).
Kalau file tidak ada -> gate mati (mode lokal, seperti sekarang).
"""
from __future__ import annotations

import hmac
import secrets
from pathlib import Path

from .config import CFG

FILE = CFG.data_dir / "pin.txt"


def aktif() -> bool:
    return FILE.exists() and bool(FILE.read_text(encoding="utf-8").strip())


def pin() -> str:
    try:
        return FILE.read_text(encoding="utf-8").strip()
    except Exception:  # noqa: BLE001
        return ""


def cocok(tebakan: str | None) -> bool:
    asli = pin()
    if not asli:
        return True
    if not tebakan:
        return False
    return hmac.compare_digest(asli, tebakan.strip())


def pastikan(panjang: int = 6) -> str:
    """Buat PIN kalau belum ada, kembalikan nilainya."""
    if aktif():
        return pin()
    FILE.parent.mkdir(parents=True, exist_ok=True)
    baru = "".join(secrets.choice("0123456789") for _ in range(panjang))
    FILE.write_text(baru + "\n", encoding="utf-8")
    return baru


def hapus() -> None:
    FILE.unlink(missing_ok=True)


def form(pesan: str = "") -> str:
    return f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kosmate — masuk</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;min-height:100dvh;display:grid;place-items:center;
background:#0b0d10;color:#e6e8ec;font:15px/1.5 Inter,system-ui,sans-serif;padding:24px}}
form{{width:100%;max-width:320px;border:1px solid #262a31;background:#15171b;border-radius:10px;padding:20px}}
h1{{font-size:15px;font-weight:600;margin:0 0 4px}}p{{margin:0 0 14px;color:#6b7280;font-size:12.5px}}
input{{width:100%;height:44px;padding:0 12px;border:1px solid #262a31;border-radius:8px;
background:#0b0d10;color:#e6e8ec;font:inherit;letter-spacing:.18em;text-align:center}}
button{{width:100%;height:44px;margin-top:10px;border:1px solid #6f79dd;border-radius:8px;
background:#5e6ad2;color:#fff;font:inherit;font-weight:500;cursor:pointer}}
.err{{color:#e05561;font-size:12.5px;margin:0 0 10px}}
</style></head><body><form method="get" action="/">
<h1>Kosmate</h1><p>Masukkan PIN buat lanjut.</p>
{"<p class='err'>" + pesan + "</p>" if pesan else ""}
<input name="pin" inputmode="numeric" autocomplete="one-time-code" placeholder="••••••" autofocus>
<button type="submit">Masuk</button></form></body></html>"""
