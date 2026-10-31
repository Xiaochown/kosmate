import pathlib
import re

p = pathlib.Path("/root/kosmate/web/app.js")
lines = p.read_text().splitlines()
KW = ("denger", "ngomong", "ketuk", "dipotong", "fakta", "mic", "suara", "coba lagi",
      "gagal", "belum", "buka", "izin", "kirim", "sebentar", "mikir", "putus")
for i, l in enumerate(lines, 1):
    if '"' not in l:
        continue
    if l.strip().startswith("//") or "console." in l or 'diag("' in l or "diag('" in l:
        continue
    if any(k in l.lower() for k in KW):
        print(f"{i}: {l.strip()[:150]}")
