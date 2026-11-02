"""Rapikan judul grup dua bahasa + tambah metrik latency (Sprint C)."""
import pathlib

# 1) judul grup: pakai EN sebagai kunci, dipetakan ke ID (dua arah)
h = pathlib.Path("/root/kosmate/web/index.html")
s = h.read_text()
s = s.replace('<h3 class="group-title">Tampilan &amp; Bahasa</h3>',
              '<h3 class="group-title">Display &amp; language</h3>')
h.write_text(s)

i = pathlib.Path("/root/kosmate/web/i18n.js")
t = i.read_text()
t = t.replace('    Memory: "Ingatan",',
              '    Memory: "Ingatan",\n    "Display & language": "Tampilan & Bahasa",')
i.write_text(t)
print("judul dua bahasa:", "Display & language" in t and "Display &amp; language" in s)
