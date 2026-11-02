"""Fitur tambahan Kosmate: pengingat, jurnal/ringkasan, kuota, RAG catatan.

Semua memakai satu file SQLite yang sama (CFG.db_path) supaya backup cukup
satu file. Tidak ada dependency baru.
"""
from __future__ import annotations

import re
import sqlite3
import time
from datetime import datetime, timedelta

from .config import CFG
from .memory import connect


def init() -> None:
    con = connect()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            teks     TEXT NOT NULL,
            due_ts   INTEGER NOT NULL,
            fired    INTEGER NOT NULL DEFAULT 0,
            dibuat   INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_rem_due ON reminders(fired, due_ts);

        CREATE TABLE IF NOT EXISTS usage (
            hari       TEXT PRIMARY KEY,
            llm_tokens INTEGER NOT NULL DEFAULT 0,
            tts_chars  INTEGER NOT NULL DEFAULT 0,
            tts_calls  INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS journal (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            hari  TEXT NOT NULL,
            teks  TEXT NOT NULL,
            pilih TEXT NOT NULL DEFAULT 'day',
            dibuat INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS announce (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teks TEXT NOT NULL,
            kind TEXT DEFAULT 'reminder',
            created REAL NOT NULL,
            spoken INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS rag_docs (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            judul  TEXT NOT NULL,
            dibuat INTEGER NOT NULL
        );
        """
    )
    # FTS5 untuk catatan; kalau tidak tersedia, fallback LIKE
    try:
        con.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks USING fts5("
            "isi, judul UNINDEXED, doc_id UNINDEXED, urut UNINDEXED, tokenize='unicode61')"
        )
        con.execute("SELECT count(*) FROM rag_chunks").fetchone()
    except sqlite3.OperationalError:
        pass
    con.commit()
    con.close()


def _hari() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ------------------------------- pengingat -------------------------------
_SATUAN = {"menit": 60, "mnt": 60, "jam": 3600, "detik": 1, "hari": 86400}


def parse_kapan(kata: str) -> int | None:
    """Parse bahasa santai: '10 menit', 'dalam 2 jam', 'jam 5', 'besok jam 9'."""
    t = (kata or "").lower()
    m = re.search(r"(\d+)\s*(menit|mnt|jam|detik|hari)", t)
    if m:
        return int(time.time()) + int(m.group(1)) * _SATUAN[m.group(2)]
    m = re.search(r"jam\s*(\d{1,2})(?:[:.](\d{2}))?", t)
    if m:
        sekarang = datetime.now()
        target = sekarang.replace(
            hour=int(m.group(1)) % 24, minute=int(m.group(2) or 0), second=0, microsecond=0
        )
        if "besok" in t:
            target = target + timedelta(days=1)
        elif target <= sekarang:
            target = target + timedelta(days=1)  # jam yang sudah lewat -> besok
        return int(target.timestamp())
    return None


def tambah_reminder(teks: str, due_ts: int) -> dict:
    con = connect()
    cur = con.execute(
        "INSERT INTO reminders (teks, due_ts, dibuat) VALUES (?,?,?)",
        (teks.strip(), int(due_ts), int(time.time())),
    )
    con.commit()
    rid = cur.lastrowid
    con.close()
    return {"id": rid, "teks": teks.strip(), "due_ts": int(due_ts)}


def daftar_reminder(limit: int = 50) -> list[dict]:
    con = connect()
    rows = con.execute(
        "SELECT id, teks, due_ts, fired FROM reminders WHERE fired=0 ORDER BY due_ts LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def hapus_reminder(rid: int) -> None:
    con = connect()
    con.execute("DELETE FROM reminders WHERE id=?", (rid,))
    con.commit()
    con.close()


def ambil_jatuh_tempo() -> list[dict]:
    con = connect()
    rows = con.execute(
        "SELECT id, teks, due_ts FROM reminders WHERE fired=0 AND due_ts<=? ORDER BY due_ts LIMIT 5",
        (int(time.time()),),
    ).fetchall()
    if rows:
        con.executemany("UPDATE reminders SET fired=1 WHERE id=?", [(r["id"],) for r in rows])
        con.commit()
    con.close()
    return [dict(r) for r in rows]


# ------------------------------- kuota -------------------------------
def catat_pakai(llm_tokens: int = 0, tts_chars: int = 0, tts_calls: int = 0) -> None:
    if not (llm_tokens or tts_chars or tts_calls):
        return
    con = connect()
    con.execute(
        "INSERT INTO usage (hari, llm_tokens, tts_chars, tts_calls) VALUES (?,?,?,?) "
        "ON CONFLICT(hari) DO UPDATE SET "
        "llm_tokens=llm_tokens+excluded.llm_tokens, "
        "tts_chars=tts_chars+excluded.tts_chars, "
        "tts_calls=tts_calls+excluded.tts_calls",
        (_hari(), int(llm_tokens), int(tts_chars), int(tts_calls)),
    )
    con.commit()
    con.close()


def pakai_hari_ini() -> dict:
    con = connect()
    row = con.execute("SELECT llm_tokens, tts_chars, tts_calls FROM usage WHERE hari=?", (_hari(),)).fetchone()
    con.close()
    if not row:
        return {"hari": _hari(), "llm_tokens": 0, "tts_chars": 0, "tts_calls": 0}
    return {"hari": _hari(), **dict(row)}


# ------------------------------- jurnal -------------------------------
def simpan_jurnal(teks: str, pilih: str = "day") -> dict:
    con = connect()
    cur = con.execute(
        "INSERT INTO journal (hari, teks, pilih, dibuat) VALUES (?,?,?,?)",
        (_hari(), teks.strip(), pilih, int(time.time())),
    )
    con.commit()
    jid = cur.lastrowid
    con.close()
    return {"id": jid, "hari": _hari(), "pilih": pilih, "teks": teks.strip()}


def daftar_jurnal(limit: int = 14) -> list[dict]:
    con = connect()
    rows = con.execute(
        "SELECT id, hari, teks, pilih FROM journal ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def episode_terakhir(limit: int = 80) -> list[dict]:
    con = connect()
    rows = con.execute(
        "SELECT role, text FROM episodes ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    return [dict(r) for r in reversed(rows)]


# ------------------------------- RAG -------------------------------
def _potong(teks: str, ukuran: int = 900, tumpang: int = 120) -> list[str]:
    teks = re.sub(r"\s+", " ", teks or "").strip()
    if not teks:
        return []
    out, i = [], 0
    while i < len(teks):
        out.append(teks[i : i + ukuran])
        i += max(1, ukuran - tumpang)
    return out


def tambah_catatan(judul: str, teks: str) -> dict:
    con = connect()
    cur = con.execute("INSERT INTO rag_docs (judul, dibuat) VALUES (?,?)", (judul.strip()[:200], int(time.time())))
    did = cur.lastrowid
    potongan = _potong(teks)
    for i, p in enumerate(potongan):
        con.execute(
            "INSERT INTO rag_chunks (isi, judul, doc_id, urut) VALUES (?,?,?,?)",
            (p, judul.strip()[:200], did, i),
        )
    con.commit()
    con.close()
    return {"id": did, "judul": judul, "potongan": len(potongan)}


def daftar_catatan() -> list[dict]:
    con = connect()
    rows = con.execute(
        "SELECT d.id, d.judul, count(c.rowid) AS potongan FROM rag_docs d "
        "LEFT JOIN rag_chunks c ON c.doc_id=d.id GROUP BY d.id ORDER BY d.id DESC"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def hapus_catatan(did: int) -> None:
    con = connect()
    con.execute("DELETE FROM rag_chunks WHERE doc_id=?", (did,))
    con.execute("DELETE FROM rag_docs WHERE id=?", (did,))
    con.commit()
    con.close()


def cari_catatan(query: str, batas: int = 3) -> list[dict]:
    q = re.sub(r"[^\w\s]", " ", (query or "").lower())
    kata = [w for w in q.split() if len(w) > 3][:6]
    if not kata:
        return []
    con = connect()
    fts_query = " OR ".join(kata)
    try:
        rows = con.execute(
            "SELECT isi, judul FROM rag_chunks WHERE rag_chunks MATCH ? ORDER BY rank LIMIT ?",
            (fts_query, batas),
        ).fetchall()
    except sqlite3.OperationalError:
        like = "%" + kata[0] + "%"
        rows = con.execute(
            "SELECT isi, judul FROM rag_chunks WHERE isi LIKE ? LIMIT ?", (like, batas)
        ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def blok_catatan(query: str) -> str:
    hasil = cari_catatan(query)
    if not hasil:
        return ""
    baris = "\n".join(f"- ({r['judul']}) {r['isi'][:600]}" for r in hasil)
    return f"\nCATATAN KULIAH relevan (pakai kalau nyambung, jangan dibacakan mentah):\n{baris}\n"


# ------------------------------------------------------- antrean ucapan server
def tambah_announce(teks: str, kind: str = "reminder") -> int:
    """Server menitipkan kalimat untuk diucapkan klien saat aktif."""
    teks = (teks or "").strip()
    if not teks:
        return 0
    con = connect()
    cur = con.execute(
        "INSERT INTO announce (teks, kind, created, spoken) VALUES (?,?,?,0)",
        (teks, kind, time.time()),
    )
    con.commit()
    return int(cur.lastrowid or 0)


def ambil_announce(limit: int = 5) -> list[dict]:
    """Ambil yang belum diucapkan, lalu tandai sudah."""
    con = connect()
    rows = con.execute(
        "SELECT id, teks, kind, created FROM announce WHERE spoken=0 ORDER BY id LIMIT ?",
        (limit,),
    ).fetchall()
    out = [dict(r) for r in rows]
    if out:
        con.executemany("UPDATE announce SET spoken=1 WHERE id=?", [(r["id"],) for r in out])
        con.commit()
    return out
