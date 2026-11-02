"""Tambah tabel `announce` (antrean ucapan dari server) di extras.py."""
import pathlib

p = pathlib.Path("/root/kosmate/kos/extras.py")
s = p.read_text()

# 1) tambah tabel di init()
if "CREATE TABLE IF NOT EXISTS announce" not in s:
    s = s.replace(
        "        CREATE TABLE IF NOT EXISTS rag_docs (",
        """        CREATE TABLE IF NOT EXISTS announce (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teks TEXT NOT NULL,
            kind TEXT DEFAULT 'reminder',
            created REAL NOT NULL,
            spoken INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS rag_docs (""",
    )

# 2) fungsi antrean ucapan
if "def tambah_announce" not in s:
    s = s.rstrip() + '''


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
'''
p.write_text(s)

print("tabel announce:", "CREATE TABLE IF NOT EXISTS announce" in s)
print("fungsi announce:", "def ambil_announce" in s)
