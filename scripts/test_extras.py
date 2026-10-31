"""Uji fitur baru: reminder, usage, notes(RAG), journal, import."""
import json
import time
import urllib.request

B = "http://127.0.0.1:8080"


def req(method, path, body=None, raw=False):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(B + path, data=data, method=method,
                               headers={"content-type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            out = resp.read()
            return resp.status, (out if raw else json.loads(out or b"{}"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:200]


print("== usage ==")
print("  ", req("GET", "/api/usage")[1])

print("== reminder ==")
st, r1 = req("POST", "/api/reminders", {"teks": "minum air", "kapan": "10 menit"})
print("  tambah:", st, r1)
st, r2 = req("POST", "/api/reminders", {"teks": "kelas SBD", "kapan": "jam 9"})
print("  jam 9 :", st, {k: r2.get(k) for k in ("id", "teks")} if isinstance(r2, dict) else r2)
print("  list  :", len(req("GET", "/api/reminders")[1].get("items", [])))
print("  due   :", req("GET", "/api/reminders/due")[1])

print("== notes / RAG ==")
catatan = ("Relasi basis data: entitas dan relasi. Kunci primer unik, kunci asing merujuk entitas lain. "
           "Normalisasi 1NF menghilangkan atribut multinilai, 2NF menghapus ketergantungan parsial, "
           "3NF menghapus ketergantungan transitif. Resolusi adalah metode inferensi yang menambahkan "
           "negasi kesimpulan lalu mencari kontradiksi sampai muncul klausa kosong.")
print("  tambah:", req("POST", "/api/notes", {"judul": "SBD + Logika", "teks": catatan})[1])
print("  list  :", req("GET", "/api/notes")[1])

print("== journal ==")
st, j = req("POST", "/api/journal", {"period": "day"})
print("  status:", st)
print("  isi   :", (j.get("teks", "")[:180] if isinstance(j, dict) else j))

print("== import (round-trip export) ==")
st, exp = req("GET", "/api/export")
print("  export:", st, len(exp.get("episodes", [])), "episode,", len(exp.get("facts", [])), "fakta")
print("  import:", req("POST", "/api/import", exp)[1])
print("== usage setelah aktivitas ==")
print("  ", req("GET", "/api/usage")[1])
