"""Ukur layout lewat set_content (tanpa navigasi/network) -> hindari hang di proot."""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

WEB = pathlib.Path("/root/kosmate/web")
html = (WEB / "index.html").read_text()
css = (WEB / "style.css").read_text()
html = html.replace('<link rel="stylesheet" href="style.css">', f"<style>{css}</style>")
# buang font & manifest (biar nol request jaringan)
html = html.replace('<link rel="manifest" href="manifest.json">', "")
for tag in ('<link rel="preconnect" href="https://fonts.googleapis.com">',
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
            '<link href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400..700&family=Nunito:wght@400;600;700&display=swap" rel="stylesheet">'):
    html = html.replace(tag, "")

VIEWPORTS = [(360, 780), (390, 844), (414, 896)]

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
    for w, h in VIEWPORTS:
        page = browser.new_page(viewport={"width": w, "height": h})
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)[:100]))
        page.set_content(html, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(400)
        data = page.evaluate("""() => {
          const R = (s) => { const e = document.querySelector(s); if (!e) return null;
            const r = e.getBoundingClientRect();
            return [Math.round(r.width), Math.round(r.height), Math.round(r.x), Math.round(r.y)]; };
          const vw = innerWidth;
          const over = [...document.querySelectorAll('body *')].map(e => {
            const r = e.getBoundingClientRect();
            return {t: e.tagName.toLowerCase() + '.' + String(e.className).split(' ')[0], w: Math.round(r.width), right: Math.round(r.right)};
          }).filter(o => o.w > vw + 1 || o.right > vw + 1).slice(0, 5);
          return {
            vw, vh: innerHeight, scrollW: document.documentElement.scrollWidth, docH: document.body.scrollHeight,
            header: R('.topbar'), nav: R('.topnav'), banner: R('.banner img'), modeRow: R('.mode-row'),
            orb: R('.orb'), mascot: R('.orb .mascot'), status: R('#status'), voice: R('.voicechip'),
            composer: R('.composer'), over,
          };
        }""")
        data["errors"] = errs
        print(f"--- viewport {w}x{h} ---")
        print("  scrollWidth:", data["scrollW"], "| docHeight:", data["docH"], "| luber:", data["over"] or "tidak ada")
        for k in ("header", "nav", "banner", "modeRow", "orb", "mascot", "status", "voice", "composer"):
            v = data[k]
            if v:
                print(f"  {k:10s} w={v[0]:4d} h={v[1]:4d}  x={v[2]:4d} y={v[3]:4d}")
        if errs:
            print("  ERROR:", errs)
        page.close()
    browser.close()
