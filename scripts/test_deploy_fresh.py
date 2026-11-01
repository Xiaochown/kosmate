"""Simulasi deploy di HP: unduh ZIP dari GitHub, ekstrak ke folder bersih, cek isinya.

Tidak menyentuh instalasi /root/kosmate yang sedang jalan.
"""
import io
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

DEST = Path("/tmp/ktest")
ZIP = "https://codeload.github.com/Xiaochown/kosmate/zip/refs/heads/main"

if DEST.exists():
    shutil.rmtree(DEST)
DEST.mkdir(parents=True)

print("mengunduh ZIP…")
data = urllib.request.urlopen(ZIP, timeout=120).read()
print(f"  {len(data)//1024} KB")
z = zipfile.ZipFile(io.BytesIO(data))
z.extractall(DEST)
root = next(DEST.iterdir())
print("  akar:", root.name)

wajib = [
    "web/index.html", "web/style.css", "web/app.js", "web/extras.js",
    "web/sw.js", "web/manifest.json",
    "web/assets/mascot.webp", "web/assets/mascot-listen.webp",
    "web/assets/mascot-think.webp", "web/assets/mascot-speak.webp",
    "web/assets/banner.webp", "web/assets/tex-paper.webp",
    "web/assets/tex-wood-dark.webp", "web/assets/story.webp",
    "web/assets/icon-192.png", "web/assets/icon-maskable-512.png",
    "kos/app.py", "kos/extras.py", "kos/tts.py", "kos/llm.py",
    "scripts/restart.sh", "scripts/set_key.sh", "go.sh", "VERSION",
]
hilang = [f for f in wajib if not (root / f).exists()]
print("\nberkas wajib:")
print("  lengkap" if not hilang else "  HILANG: " + ", ".join(hilang))

v = (root / "VERSION").read_text().strip() if (root / "VERSION").exists() else "?"
print("  VERSION:", v)

css = (root / "web/style.css").read_text()
print("  tema farm (palet oat):", "#f3e9d5" in css)
print("  maskot 4 pose di CSS :", "mascot-listen" in (root / "web/app.js").read_text())
sw = (root / "web/sw.js").read_text()
print("  service worker v2    :", "kai-shell-v2" in sw)

# jalankan server dari folder bersih di port lain, cek endpoint
print("\nmenjalankan server dari folder bersih (port 8099)…")
env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "PORT": "8099", "HOME": "/root"}
proc = subprocess.Popen(
    ["bash", "scripts/restart.sh"], cwd=str(root), env=env,
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
)
out, _ = proc.communicate(timeout=180)
akhir = "\n".join(out.strip().splitlines()[-6:])
print("  hasil restart (6 baris akhir):")
for ln in akhir.splitlines():
    print("    " + ln)

time.sleep(1)
try:
    r = urllib.request.urlopen("http://127.0.0.1:8099/api/health", timeout=15)
    print("  /api/health:", r.status)
    h = urllib.request.urlopen("http://127.0.0.1:8099/", timeout=15)
    body = h.read().decode()
    print("  /:", h.status, len(body), "byte | maskot di HTML:", "mascot.webp" in body)
    for a in ("/assets/mascot-listen.webp", "/assets/tex-wood-dark.webp", "/style.css?v=2"):
        rr = urllib.request.urlopen("http://127.0.0.1:8099" + a, timeout=15)
        print(f"  {a:34s}", rr.status, len(rr.read()) // 1024, "KB")
except Exception as e:  # noqa: BLE001
    print("  GAGAL cek endpoint:", type(e).__name__, str(e)[:120])

subprocess.run(["pkill", "-f", "PORT=8099"], check=False)
print("\nselesai. folder uji:", root)
