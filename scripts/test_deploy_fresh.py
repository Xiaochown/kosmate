"""Simulasi deploy di HP: ZIP GitHub -> folder bersih -> server benar-benar hidup.

Memakai python milik instalasi utama (dependency sudah ada) supaya tidak perlu
install ulang; yang diuji adalah ISI PAKET dan kemampuan boot, bukan pip.
"""
import io
import shutil
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

DEST = Path("/tmp/ktest")
ZIP = "https://codeload.github.com/Xiaochown/kosmate/zip/refs/heads/main"
PY = "/root/kosmate/.venv/bin/python"
if not Path(PY).exists():
    PY = shutil.which("python3") or "python3"
PORT = "8099"

if DEST.exists():
    shutil.rmtree(DEST)
DEST.mkdir(parents=True)

print("mengunduh ZIP…")
data = urllib.request.urlopen(ZIP, timeout=120).read()
print(f"  {len(data)//1024} KB")
zipfile.ZipFile(io.BytesIO(data)).extractall(DEST)
root = next(DEST.iterdir())

wajib = [
    "web/index.html", "web/style.css", "web/app.js", "web/extras.js",
    "web/sw.js", "web/manifest.json",
    "web/assets/mascot.webp", "web/assets/mascot-listen.webp",
    "web/assets/mascot-think.webp", "web/assets/mascot-speak.webp",
    "web/assets/banner.webp", "web/assets/tex-paper.webp",
    "web/assets/tex-wood-dark.webp", "web/assets/story.webp",
    "web/assets/icon-192.png", "web/assets/icon-maskable-512.png",
    "kos/app.py", "kos/extras.py", "go.sh", "VERSION",
]
hilang = [f for f in wajib if not (root / f).exists()]
print("berkas wajib:", "lengkap" if not hilang else "HILANG: " + ", ".join(hilang))
print("VERSION:", (root / "VERSION").read_text().strip())
print("tema oat:", "#f3e9d5" in (root / "web/style.css").read_text())
print("sw v2   :", "kai-shell-v2" in (root / "web/sw.js").read_text())

# .env: pakai punya instalasi utama (di HP ini sudah ada)
shutil.copy("/root/kosmate/.env", root / ".env")
(root / ".kosmate-runtime").write_text(PY + "\n")

print(f"\nboot dari folder bersih di :{PORT} pakai {PY}")
proc = subprocess.run(["bash", "scripts/restart.sh", PORT], cwd=str(root),
                      capture_output=True, text=True, timeout=180)
for ln in proc.stdout.strip().splitlines()[-5:]:
    print("   " + ln)

ok = True
try:
    h = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=20)
    print("\n  /api/health:", h.status)
    body = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=20).read().decode()
    print("  /          :", len(body), "byte | mascot:", "mascot.webp" in body, "| v=2:", "style.css?v=2" in body)
    for a in ("/assets/mascot-listen.webp", "/assets/tex-wood-dark.webp", "/assets/banner.webp"):
        r = urllib.request.urlopen(f"http://127.0.0.1:{PORT}{a}", timeout=20)
        print(f"  {a:34s}", r.status, len(r.read()) // 1024, "KB")
except Exception as e:  # noqa: BLE001
    ok = False
    print("  GAGAL:", type(e).__name__, str(e)[:150])

# matikan server uji
for pid in subprocess.run(["pgrep", "-f", "uvicorn kos.app"], capture_output=True, text=True).stdout.split():
    try:
        subprocess.run(["kill", pid], check=False)
    except Exception:
        pass
print("\nHASIL:", "LOLOS" if (ok and not hilang) else "ADA MASALAH")
