"""Penjadwal pengingat di sisi SERVER.

Kenapa di server: pengingat harus tetap bunyi walau tab Chrome ditutup.
Caranya: cek DB tiap 20 detik -> kirim notifikasi Android lewat `termux-notification`
-> catat ke tabel `announce` supaya saat Chrome dibuka lagi, Kai membacakannya.
"""
from __future__ import annotations

import asyncio
import shutil
import subprocess
import time

from . import extras

TERMUX_NOTIF = shutil.which("termux-notification")
TERMUX_VIBRATE = shutil.which("termux-vibrate")

_task: asyncio.Task | None = None
_notif_gagal = 0


def _kirim_notifikasi(teks: str) -> bool:
    global _notif_gagal
    if not TERMUX_NOTIF or _notif_gagal >= 3:
        return False
    try:
        subprocess.run(
            [TERMUX_NOTIF, "--title", "Kai · pengingat", "--content", teks,
             "--priority", "high", "--id", "kosmate-reminder"],
            timeout=3, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:  # noqa: BLE001
        _notif_gagal += 1
        if _notif_gagal == 3:
            print("[scheduler] termux-notification tidak merespons — dimatikan")
        return False


def _getar() -> None:
    if TERMUX_VIBRATE:
        try:
            subprocess.run([TERMUX_VIBRATE, "-d", "300"], timeout=10, check=False)
        except Exception:  # noqa: BLE001
            pass


async def _detak() -> None:
    """Satu putaran: ambil yang jatuh tempo, notifikasi, catat untuk diucapkan."""
    try:
        jatuh = extras.ambil_jatuh_tempo()
    except Exception as e:  # noqa: BLE001
        print("[scheduler] gagal baca reminder:", e)
        return

    for r in jatuh:
        teks = str(r.get("teks", "")).strip()
        if not teks:
            continue
        # jalankan di thread supaya event loop server tidak pernah tersendat
        terkirim = await asyncio.to_thread(_kirim_notifikasi, teks)
        await asyncio.to_thread(_getar)
        # selalu dicatat supaya bisa diucapkan saat Chrome dibuka
        extras.tambah_announce(teks, kind="reminder")
        print(f"[scheduler] pengingat: {teks!r} (notifikasi={'ya' if terkirim else 'tidak'})")


async def _loop() -> None:
    # beri jeda awal biar server siap dulu
    await asyncio.sleep(5)
    while True:
        await _detak()
        await asyncio.sleep(20)


def mulai() -> None:
    global _task
    if _task and not _task.done():
        return
    _task = asyncio.create_task(_loop())
    print(f"[scheduler] aktif · termux-notification={'ada' if TERMUX_NOTIF else 'TIDAK ADA'}")


async def berhenti() -> None:
    global _task
    if _task:
        _task.cancel()
        _task = None
