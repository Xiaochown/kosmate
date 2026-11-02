"""Uji Sprint A (versi bersih): pengingat server-side, antrean ucapan, migrasi."""
import json
import sqlite3
import sys
import time
import urllib.request

sys.path.insert(0, "/root/kosmate")
from kos import migrate  # noqa: E402
from kos.config import CFG  # noqa: E402

B = "http://127.0.0.1:8080"


def api(path, body=None, method=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(B + path, data=data, method=method or ("POST" if data else "GET"),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=20))


# kosongkan antrean lama
con = sqlite3.connect(CFG.db_path)
con.execute("UPDATE announce SET spoken=1")
con.execute("DELETE FROM reminders WHERE teks LIKE 'uji sprint%'")
con.commit()
con.close()

print("--- 1. buat pengingat, lalu majukan waktunya ---")
r = api("/api/reminders", {"teks": "uji sprint a: minum air", "kapan": "10 menit"})
print("  id:", r.get("id"))
con = sqlite3.connect(CFG.db_path)
con.execute("UPDATE reminders SET due_ts=? WHERE id=?", (int(time.time()) - 5, r.get("id")))
con.commit()
con.close()

print("  menunggu penjadwal server (detak tiap 20 detik)…")
ketemu = None
for i in range(50):
    time.sleep(1)
    items = api("/api/announce")["items"]
    if any("uji sprint a" in x["teks"] for x in items):
        ketemu = i + 1
        break
print("  antrean muncul setelah:", f"{ketemu} detik" if ketemu else "TIDAK MUNCUL")

print("\n--- 2. antrean hanya diucapkan sekali ---")
lagi = [x for x in api("/api/announce")["items"] if "uji sprint a" in x["teks"]]
print("  panggilan kedua:", lagi or "kosong (benar)")

print("\n--- 3. migrasi & backup ---")
con = sqlite3.connect(CFG.db_path)
print("  user_version:", con.execute("PRAGMA user_version").fetchone()[0])
con.close()
backup = sorted(migrate.BACKUP_DIR.glob("kosmate-*.db"))
print("  backup:", [b.name for b in backup])

print("\n--- 4. klien: polling & jeda ---")
ex = open("/root/kosmate/web/extras.js").read()
app = open("/root/kosmate/web/app.js").read()
print("  polling 20s dibuang :", "setInterval(cekPengingat, 20000)" not in ex)
print("  announce 15s        :", "setInterval(cekAnnounce, 15000)" in ex)
print("  hanya saat visible  :", 'document.visibilityState !== "visible"' in ex)
print("  jeda 2200ms         :", "silenceMs: 2200" in app)

print("\nHASIL:", "LOLOS" if ketemu else "GAGAL")
