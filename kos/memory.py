"""Memori Kosmate: episodic log + fakta berstruktur + FTS5 (RAG hybrid).

Kenapa bukan vector-only: retrieval vektor murni lemah untuk memori personal
yang punya waktu (fakta berubah: kos lama, jadwal kuliah baru). Kombinasi
FTS5 (lexical) + tabel fakta bertanggal + recency boost jauh lebih akurat
dan jalan tanpa API embedding / tanpa GPU.
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import CFG

_FTS_OK: bool | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(CFG.db_path, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def has_fts(con: sqlite3.Connection) -> bool:
    global _FTS_OK
    if _FTS_OK is None:
        try:
            con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _fts_probe USING fts5(x)")
            con.execute("DROP TABLE IF EXISTS _fts_probe")
            _FTS_OK = True
        except sqlite3.OperationalError:
            _FTS_OK = False
    return _FTS_OK


def init() -> None:
    con = connect()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            session TEXT,
            role TEXT NOT NULL,
            text TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            subject TEXT NOT NULL,
            predicate TEXT NOT NULL,
            object TEXT NOT NULL,
            confidence REAL DEFAULT 0.7,
            active INTEGER DEFAULT 1,
            source_ep INTEGER
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            kind TEXT DEFAULT 'note',
            text TEXT NOT NULL,
            pinned INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
        CREATE INDEX IF NOT EXISTS idx_ep_ts ON episodes(ts);
        CREATE INDEX IF NOT EXISTS idx_fact_subj ON facts(subject);
        """
    )
    if has_fts(con):
        _ensure_fts(con)
    con.commit()
    con.close()


FTS_VERSION = "2"  # 2 = tabel FTS standalone (bukan external-content)


def _ensure_fts(con: sqlite3.Connection) -> None:
    """Bikin/upgrade tabel FTS.

    Versi 1 dulu memakai `content='facts'` yang kolomnya beda nama ("obj" vs
    "object") -> DELETE dan rebuild gagal dengan `no such column: T.obj`.
    Versi 2 pakai tabel FTS standalone yang diisi manual.
    """
    row = con.execute("SELECT v FROM meta WHERE k='fts_version'").fetchone()
    ver = row["v"] if row else None
    if ver == FTS_VERSION:
        con.executescript(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(text, tokenize='unicode61');
            CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts
                USING fts5(subject, predicate, object, tokenize='unicode61');
            """
        )
        return

    con.executescript(
        """
        DROP TABLE IF EXISTS episodes_fts;
        DROP TABLE IF EXISTS facts_fts;
        CREATE VIRTUAL TABLE episodes_fts USING fts5(text, tokenize='unicode61');
        CREATE VIRTUAL TABLE facts_fts
            USING fts5(subject, predicate, object, tokenize='unicode61');
        """
    )
    _rebuild_fts(con)
    con.execute(
        "INSERT INTO meta(k, v) VALUES('fts_version', ?) "
        "ON CONFLICT(k) DO UPDATE SET v=excluded.v",
        (FTS_VERSION,),
    )
    print("[memory] index pencarian di-rebuild")


def _rebuild_fts(con: sqlite3.Connection) -> None:
    con.execute("DELETE FROM episodes_fts")
    con.execute("DELETE FROM facts_fts")
    con.execute("INSERT INTO episodes_fts(rowid, text) SELECT id, text FROM episodes")
    con.execute(
        "INSERT INTO facts_fts(rowid, subject, predicate, object) "
        "SELECT id, subject, predicate, object FROM facts"
    )


# ---------------------------------------------------------------- episodes
def add_episode(role: str, text: str, session: str = "default") -> int:
    con = connect()
    cur = con.execute(
        "INSERT INTO episodes(ts, session, role, text) VALUES (?,?,?,?)",
        (_now(), session, role, text.strip()),
    )
    eid = int(cur.lastrowid)
    if has_fts(con):
        con.execute(
            "INSERT INTO episodes_fts(rowid, text) VALUES (?,?)", (eid, text.strip())
        )
    con.commit()
    con.close()
    return eid


def recent(limit: int = 10, session: str | None = None) -> list[dict[str, Any]]:
    con = connect()
    if session:
        rows = con.execute(
            "SELECT * FROM episodes WHERE session=? ORDER BY id DESC LIMIT ?",
            (session, limit),
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT * FROM episodes ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    con.close()
    return [dict(r) for r in reversed(rows)]


# ------------------------------------------------------------------- facts
def add_fact(
    subject: str,
    predicate: str,
    obj: str,
    confidence: float = 0.7,
    source_ep: int | None = None,
) -> int | None:
    subject, predicate, obj = subject.strip(), predicate.strip(), obj.strip()
    if not obj or not predicate:
        return None
    con = connect()
    dup = con.execute(
        "SELECT id FROM facts WHERE lower(subject)=lower(?) AND lower(predicate)=lower(?) "
        "AND lower(object)=lower(?) AND active=1",
        (subject, predicate, obj),
    ).fetchone()
    if dup:
        con.close()
        return None
    cur = con.execute(
        "INSERT INTO facts(ts, subject, predicate, object, confidence, source_ep) "
        "VALUES (?,?,?,?,?,?)",
        (_now(), subject, predicate, obj, confidence, source_ep),
    )
    fid = int(cur.lastrowid)
    if has_fts(con):
        con.execute(
            "INSERT INTO facts_fts(rowid, subject, predicate, object) VALUES (?,?,?,?)",
            (fid, subject, predicate, obj),
        )
    con.commit()
    con.close()
    return fid


def list_facts(limit: int = 200, active_only: bool = True) -> list[dict[str, Any]]:
    con = connect()
    q = "SELECT * FROM facts" + (" WHERE active=1" if active_only else "") + " ORDER BY id DESC LIMIT ?"
    rows = con.execute(q, (limit,)).fetchall()
    con.close()
    return [dict(r) for r in rows]


def delete_fact(fid: int) -> bool:
    con = connect()
    row = con.execute("SELECT id FROM facts WHERE id=?", (fid,)).fetchone()
    if not row:
        con.close()
        return False
    con.execute("DELETE FROM facts WHERE id=?", (fid,))
    if has_fts(con):
        con.execute("DELETE FROM facts_fts WHERE rowid=?", (fid,))
    con.commit()
    con.close()
    return True


# ------------------------------------------------------------------- notes
def add_note(text: str, kind: str = "note", pinned: int = 0) -> int:
    con = connect()
    cur = con.execute(
        "INSERT INTO notes(ts, kind, text, pinned) VALUES (?,?,?,?)",
        (_now(), kind, text.strip(), pinned),
    )
    nid = int(cur.lastrowid)
    con.commit()
    con.close()
    return nid


def list_notes(pinned_only: bool = False, limit: int = 50) -> list[dict[str, Any]]:
    con = connect()
    q = "SELECT * FROM notes" + (" WHERE pinned=1" if pinned_only else "") + " ORDER BY id DESC LIMIT ?"
    rows = con.execute(q, (limit,)).fetchall()
    con.close()
    return [dict(r) for r in rows]


# --------------------------------------------------------------- retrieval
def _fts_query(q: str) -> str:
    terms = [t for t in re.findall(r"[0-9A-Za-z\u00C0-\u024F]{3,}", q.lower())]
    if not terms:
        return ""
    return " OR ".join(f'"{t}"' for t in terms[:12])


def search_episodes(q: str, k: int = 6) -> list[dict[str, Any]]:
    con = connect()
    fq = _fts_query(q)
    rows: list[sqlite3.Row] = []
    if fq and has_fts(con):
        try:
            rows = con.execute(
                "SELECT e.*, bm25(episodes_fts) AS score FROM episodes_fts f "
                "JOIN episodes e ON e.id=f.rowid WHERE episodes_fts MATCH ? "
                "ORDER BY score LIMIT ?",
                (fq, k),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
    if not rows:
        like = "%" + (q.strip()[:60] or "x") + "%"
        rows = con.execute(
            "SELECT * FROM episodes WHERE text LIKE ? ORDER BY id DESC LIMIT ?", (like, k)
        ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def search_facts(q: str, k: int = 10) -> list[dict[str, Any]]:
    con = connect()
    fq = _fts_query(q)
    rows: list[sqlite3.Row] = []
    if fq and has_fts(con):
        try:
            rows = con.execute(
                "SELECT fa.*, bm25(facts_fts) AS score FROM facts_fts f "
                "JOIN facts fa ON fa.id=f.rowid WHERE facts_fts MATCH ? AND fa.active=1 "
                "ORDER BY score LIMIT ?",
                (fq, k),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
    if not rows:
        like = "%" + (q.strip()[:60] or "x") + "%"
        rows = con.execute(
            "SELECT * FROM facts WHERE active=1 AND (object LIKE ? OR subject LIKE ? OR predicate LIKE ?) "
            "ORDER BY id DESC LIMIT ?",
            (like, like, like, k),
        ).fetchall()
    con.close()
    return [dict(r) for r in rows]


_PRONOUNS = {"gue", "gua", "aku", "saya", "gw", "lu", "kamu", "elo", "kau", "dia"}


def context_block(query: str = "", max_chars: int = 1400) -> str:
    """Bangun blok memori untuk system prompt: fakta relevan + pinned + episode terkait."""
    lines: list[str] = []

    pinned = list_notes(pinned_only=True, limit=8)
    if pinned:
        lines.append("[Catatan penting]")
        lines += [f"- {n['text']}" for n in pinned]

    facts_seen: set[int] = set()
    if query.strip():
        for f in search_facts(query, k=8):
            if f["id"] in facts_seen:
                continue
            facts_seen.add(f["id"])
            subj = "" if f["subject"].lower() in _PRONOUNS else f"{f['subject']} — "
            lines.append(f"- {subj}{f['predicate']} {f['object']}")
        for e in search_episodes(query, k=3):
            snippet = re.sub(r"\s+", " ", e["text"])[:160]
            who = "user" if e["role"] == "user" else CFG.assistant_name
            lines.append(f"- (obrolan lalu, {who}) {snippet}")

    if not facts_seen and not pinned and not query.strip():
        for f in list_facts(limit=10):
            subj = "" if f["subject"].lower() in _PRONOUNS else f"{f['subject']} — "
            lines.append(f"- {subj}{f['predicate']} {f['object']}")

    out = "\n".join(lines)
    return out[:max_chars]


# ------------------------------------------------------------ extract facts
EXTRACT_PROMPT = """Kamu mesin ekstraksi memori. Dari percakapan, ambil FAKTA TAHAN LAMA tentang user
(nama, kampus, jadwal, kebiasaan, preferensi, target, kondisi, orang penting, hal yang sedang dikerjakan).
JANGAN ambil hal sementara seperti "lapar sekarang" atau basa-basi.

Balas HANYA JSON array, tiap item: {"subject":"user","predicate":"...","object":"...","confidence":0.0-1.0}
predicate dalam bahasa Indonesia, singkat, bentuk kata kerja/keadaan (mis. "kuliah di", "alergi", "target", "suka").
Kalau tidak ada fakta baru: [].

CONTOH:
User: "besok gue ada ujian logika jam 8 pagi di gedung C"
Output: [{"subject":"user","predicate":"ujian","object":"logika informatika, besok jam 8 pagi, gedung C","confidence":0.9}]

PERCAKAPAN:
{conversation}

JSON:"""


def parse_facts_json(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    m = re.search(r"\[.*\]", raw, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    for item in data if isinstance(data, list) else []:
        if not isinstance(item, dict):
            continue
        obj = str(item.get("object", "")).strip()
        pred = str(item.get("predicate", "")).strip()
        if not obj or not pred:
            continue
        out.append(
            {
                "subject": str(item.get("subject", "user")).strip() or "user",
                "predicate": pred[:120],
                "object": obj[:300],
                "confidence": float(item.get("confidence", 0.7) or 0.7),
            }
        )
    return out[:8]


def stats() -> dict[str, int]:
    con = connect()
    ep = con.execute("SELECT COUNT(*) c FROM episodes").fetchone()["c"]
    fa = con.execute("SELECT COUNT(*) c FROM facts WHERE active=1").fetchone()["c"]
    no = con.execute("SELECT COUNT(*) c FROM notes").fetchone()["c"]
    con.close()
    return {"episodes": ep, "facts": fa, "notes": no}


def export_all() -> dict[str, Any]:
    con = connect()
    data = {
        "episodes": [dict(r) for r in con.execute("SELECT * FROM episodes ORDER BY id").fetchall()],
        "facts": [dict(r) for r in con.execute("SELECT * FROM facts ORDER BY id").fetchall()],
        "notes": [dict(r) for r in con.execute("SELECT * FROM notes ORDER BY id").fetchall()],
        "exported_at": _now(),
    }
    con.close()
    return data


if __name__ == "__main__":
    init()
    add_fact("user", "kuliah di", "UDINUS Semarang, semester 4")
    add_fact("user", "suka", "kopi hitam tanpa gula")
    add_fact("user", "target", "jadi network engineer")
    add_note("Ujian Logika Informatika tiap Senin jam 8 pagi", kind="jadwal", pinned=1)
    print(json.dumps(stats(), indent=2))
    print("--- konteks ---")
    print(context_block("ujian logika kapan"))
