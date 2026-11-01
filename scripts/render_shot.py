"""Render preview UI ke PNG via WeasyPrint, lalu dinilai pakai vision.

WeasyPrint punya keterbatasan (flex/grid modern terbatas), jadi hasilnya dipakai
untuk menilai WARNA, TEKSTUR, GAMBAR, dan PROPORS I kasar saja — bukan layout final.
"""
import re
import subprocess
import sys
from pathlib import Path

from weasyprint import HTML

WEB = Path("/root/kosmate/web")
OUT = Path("/root/kosmate/screens")
OUT.mkdir(exist_ok=True)

TARGET = sys.argv[1] if len(sys.argv) > 1 else "idle"
STATE = sys.argv[2] if len(sys.argv) > 2 else ""

html = (WEB / "index.html").read_text()
html = re.sub(r'\s*<link rel="manifest"[^>]*>', "", html)
html = re.sub(r'\s*<link rel="preconnect"[^>]*>', "", html)
html = re.sub(r'\s*<link href="https://fonts[^>]*>', "", html)
html = re.sub(r'\s*<script src="[^"]*"[^>]*></script>', "", html)

if TARGET == "actions":
    html = html.replace('class="sheet" id="actSheet"', 'class="sheet open" id="actSheet"')
elif TARGET in ("settings", "memory"):
    html = html.replace('class="sheet" id="sheet"', 'class="sheet open" id="sheet"')
elif TARGET == "reply":
    html = html.replace('class="reply"', 'class="reply show"')
    html = html.replace(
        '<p class="reply-text" id="replyText"></p>',
        '<p class="reply-text" id="replyText">Malam ini gue temenin ya. '
        "Kalau mau cerita, bilang aja mau cerita soal apa.</p>",
    )

st = STATE or "idle"
html = html.replace('<body data-state="idle">', f'<body data-state="{st}">')
# ganti pose maskot sesuai state
pose = {"listening": "mascot-listen.webp", "thinking": "mascot-think.webp", "speaking": "mascot-speak.webp"}.get(st)
if pose:
    html = html.replace('src="assets/mascot.webp"', f'src="assets/{pose}"')

html = html.replace("</head>", """<style>
@page { size: 390px 844px; margin: 0; }
html, body { width: 390px; height: 844px; overflow: hidden; }
.sheet { position: static !important; transform: none !important; visibility: visible !important;
         height: 844px; overflow: hidden; }
.sheet:not(.open) { display: none !important; }
</style></head>""")

pdf = OUT / f"{TARGET}{'-'+st if STATE else ''}.pdf"
HTML(string=html, base_url=str(WEB) + "/").write_pdf(str(pdf))
stem = f"{TARGET}{'-'+st if STATE else ''}"
for lama in OUT.glob(stem + "-*.png"):
    lama.unlink()
subprocess.run(["pdftoppm", "-png", "-r", "160", "-f", "1", "-l", "1", str(pdf), str(OUT / stem)], check=True)
hasil = sorted(OUT.glob(stem + "-*.png"))
print("hasil:", hasil[-1] if hasil else "GAGAL")
