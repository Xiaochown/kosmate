"""Screenshot halaman sepenuhnya offline: semua aset inline base64, nol request jaringan.

Chromium di proot ini hang kalau ada request apa pun -> semua harus di-inline.
"""
import base64
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

WEB = pathlib.Path("/root/kosmate/web")
OUT = pathlib.Path("/root/kosmate/screens")
OUT.mkdir(exist_ok=True)

TARGET = sys.argv[1] if len(sys.argv) > 1 else "idle"
STATE = sys.argv[2] if len(sys.argv) > 2 else ""


def build_html() -> str:
    html = (WEB / "index.html").read_text()
    css = (WEB / "style.css").read_text()
    html = html.replace('<link rel="stylesheet" href="style.css">', f"<style>{css}</style>")
    html = re.sub(r'\s*<link rel="manifest"[^>]*>', "", html)
    html = re.sub(r'\s*<link rel="preconnect"[^>]*>', "", html)
    html = re.sub(r'\s*<link href="https://fonts\.googleapis\.com[^>]*>', "", html)
    html = re.sub(r'\s*<link rel="icon"[^>]*>', "", html)
    html = re.sub(r'\s*<link rel="apple-touch-icon"[^>]*>', "", html)
    html = re.sub(r'\s*<script src="[^"]*"[^>]*></script>', "", html)  # tanpa JS app (offline)

    def inline(m):
        src = m.group(1)
        p = WEB / src
        if not p.exists():
            return m.group(0)
        mime = "image/webp" if p.suffix == ".webp" else "image/png"
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f'src="data:{mime};base64,{b64}"'

    html = re.sub(r'src="(assets/[^"]+)"', inline, html)
    return html


html = build_html()
assert "http" not in re.sub(r"<meta[^>]*>", "", html).split("<body")[0], "masih ada resource eksternal"

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
    page = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    page.set_content(html, wait_until="domcontentloaded", timeout=20000)
    page.wait_for_timeout(400)
    if STATE:
        page.evaluate(f"document.body.dataset.state = '{STATE}'")
    if TARGET == "actions":
        page.evaluate("document.getElementById('actSheet').classList.add('open')")
    elif TARGET in ("settings", "memory"):
        page.evaluate("document.getElementById('sheet').classList.add('open')")
    elif TARGET == "reply":
        page.evaluate("""() => {
            document.getElementById('reply').classList.add('show');
            document.getElementById('replyYou').textContent = 'you';
            document.getElementById('replyText').textContent =
              'Malam ini gue temenin ya. Kalau mau cerita, bilang aja mau cerita soal apa.';
        }""")
    page.wait_for_timeout(350)
    f = OUT / f"{TARGET}{('-' + STATE) if STATE else ''}.png"
    page.screenshot(path=str(f))
    print("screenshot:", f, f.stat().st_size // 1024, "KB")
    b.close()
