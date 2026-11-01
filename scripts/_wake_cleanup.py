import pathlib
import re

p = pathlib.Path("/root/kosmate/web/extras.js")
s = p.read_text()

# 1) buang blok WAKE WORD lama (dipindah ke wake.js)
awal = s.find("/* ------------------------------- WAKE WORD")
akhir = s.find("/* ------------------------------- util")
if awal != -1 and akhir != -1 and akhir > awal:
    s = s[:awal] + s[akhir:]
    print("blok wake lama dihapus")
else:
    print("PERINGATAN: blok wake lama tidak ketemu")

# 2) binding toggle -> delegasi ke wake.js
s = re.sub(
    r'  // wake word\r?\n  on\("setWake",\s*\(\)\s*=>\s*\{[^}]*\}\);\r?\n',
    '  // wake word (logikanya di wake.js)\n  on("setWake", () => { if (EX.toggleWake) EX.toggleWake(); });\n',
    s,
)

# kalau pola di atas tidak kena (format beda), ganti manual
if 'EX.toggleWake' not in s:
    lama = 'on("setWake", () => {\n    if (EX.wake) { stopWake(); setStatus("Wake word off"); }\n    else startWake();\n  });'
    if lama in s:
        s = s.replace(lama, 'on("setWake", () => { if (EX.toggleWake) EX.toggleWake(); });')
        print("toggle diganti (manual)")
    else:
        print("PERINGATAN: binding toggle tidak ketemu")

p.write_text(s)
print("EX.toggleWake dipakai:", "EX.toggleWake" in s)
print("sisa startWake/stopWake lokal:", s.count("function startWake"), s.count("function stopWake"))
