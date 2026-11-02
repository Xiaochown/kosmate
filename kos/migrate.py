"""Migrasi database berversi + backup otomatis.

Masalah yang diselesaikan: update lewat `go.sh` menumpuk kode baru di atas DB lama.
Dulu skema hanya `CREATE TABLE IF NOT EXISTS`, jadi perubahan kolom bisa membuat
data user (jurnal, fakta, catatan) hilang tanpa jejak.

Sekarang:
  - versi skema disimpan di `PRAGMA user_version`
  - sebelum migrasi apa pun, file DB dicopy ke data/backups/ (5 terakhir disimpan)
  - setiap migrasi dijalankan sekali, berurutan, dalam transaksi
"""
from __future__ import annotations

import shutil
import sqlite3
import time
from pathlib import Path

from .config import CFG

BACKUP_DIR = CFG.data_dir / "backups"
SIMPAN_BACKUP = 5


def _konek() -> sqlite3.Connection:
    con = sqlite3.connect(CFG.db_path)
    con.row_factory = sqlite3.Row
    return con


def versi(con: sqlite3.Connection) -> int:
    return int(con.execute("PRAGMA user_version").fetchone()[0])


def _backup() -> Path | None:
    db = Path(CFG.db_path)
    if not db.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    nama = "kosmate-" + time.strftime("%Y%m%d-%H%M%S") + ".db"
    tujuan = BACKUP_DIR / nama
    try:
        src = sqlite3.connect(str(db))
        dst = sqlite3.connect(str(tujuan))
        with dst:
            src.backup(dst)          # backup yang aman walau DB sedang dipakai
        dst.close()
        src.close()
    except Exception:  # noqa: BLE001
        shutil.copy2(db, tujuan)
    # simpan hanya N terakhir
    lama = sorted(BACKUP_DIR.glob("kosmate-*.db"))
    for f in lama[:-SIMPAN_BACKUP]:
        try:
            f.unlink()
        except OSError:
            pass
    return tujuan


# setiap migrasi: (versi, keterangan, list SQL)
MIGRASI: list[tuple[int, str, list[str]]] = [
    (1, "baseline: tandai skema yang sudah ada", []),
    (
        2,
        "tabel announce (antrean ucapan dari server)",
        [
            """CREATE TABLE IF NOT EXISTS announce (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   teks TEXT NOT NULL,
                   kind TEXT DEFAULT 'reminder',
                   created REAL NOT NULL,
                   spoken INTEGER DEFAULT 0
               )""",
            "CREATE INDEX IF NOT EXISTS idx_announce_spoken ON announce(spoken, id)",
        ],
    ),
    (
        3,
        "index pengingat + jurnal",
        [
            "CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(fired, due_ts)",
            "CREATE INDEX IF NOT EXISTS idx_journal_hari ON journal(hari)",
        ],
    ),
]


def jalankan() -> int:
    """Jalankan migrasi yang belum diterapkan. Kembalikan versi akhir."""
    con = _konek()
    awal = versi(con)
    belum = [m for m in MIGRASI if m[0] > awal]
    if not belum:
        con.close()
        return awal

    cadangan = _backup()
    if cadangan:
        print(f"[migrate] backup DB -> {cadangan.name}")

    for v, ket, sqls in belum:
        try:
            with con:
                for q in sqls:
                    con.execute(q)
                con.execute(f"PRAGMA user_version={v}")
            print(f"[migrate] v{v} ok · {ket}")
        except Exception as e:  # noqa: BLE001
            print(f"[migrate] v{v} GAGAL: {e} — berhenti, data lama tidak disentuh")
            break

    akhir = versi(con)
    con.close()
    print(f"[migrate] skema v{awal} -> v{akhir}")
    return akhir
