"""Bangun single.html: semua CSS/JS/gambar di-inline, jadi tidak butuh request lain."""
import base64
import pathlib
import re

ROOT = pathlib.Path("/root/kosmate/demo")
html = (ROOT / "index.html").read_text()
css = (ROOT / "style.css").read_text()
demo = (ROOT / "demo.js").read_text()
app = (ROOT / "app.js").read_text()
extras = (ROOT / "extras.js").read_text()
wake = (ROOT / "wake.js").read_text()


def data_uri(path: pathlib.Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


# inline gambar
for nama, mime in (("story.webp", "image/webp"), ("focus.webp", "image/webp"),
                   ("remind.webp", "image/webp"), ("journal.webp", "image/webp"),
                   ("banner.webp", "image/webp"), ("mascot.webp", "image/webp"),
                   ("mascot-listen.webp", "image/webp"), ("mascot-think.webp", "image/webp"),
                   ("mascot-speak.webp", "image/webp"), ("tex-paper.webp", "image/webp"),
                   ("tex-wood-dark.webp", "image/webp"), ("icon-192.png", "image/png")):
    f = ROOT / "assets" / nama
    if f.exists():
        uri = data_uri(f, mime)
        html = re.sub(rf'(src|href)="assets/{re.escape(nama)}[^"]*"', lambda m, u=uri: f'{m.group(1)}="{u}"', html)

# buang manifest + stylesheet eksternal, sisip CSS
html = re.sub(r'\s*<link rel="manifest"[^>]*>', "", html)
html = re.sub(r'\s*<link rel="preconnect"[^>]*>', "", html)
html = re.sub(r'\s*<link href="https://fonts\.googleapis\.com[^>]*>', "", html)
html = re.sub(r'<link rel="stylesheet" href="style\.css[^"]*">', lambda m: f"<style>\n{css}\n</style>", html)

# data: URI di dalam CSS juga (tekstur latar)
for nama in ("tex-paper.webp", "tex-wood-dark.webp", "tex-wood.webp", "orn-wood-edge.webp"):
    f = ROOT / "assets" / nama
    if f.exists():
        mime = "image/webp" if nama.endswith(".webp") else "image/png"
        html = html.replace(f"assets/{nama}", data_uri(f, mime))

# sisip JS inline, buang tag eksternal (toleran terhadap ?v=)
for src, isi in (("demo.js", demo), ("app.js", app), ("extras.js", extras), ("wake.js", wake)):
    html = re.sub(rf'<script src="{re.escape(src)}[^"]*"></script>', lambda m, i=isi: f"<script>\n{i}\n</script>", html)

(ROOT / "single.html").write_text(html)
print("single.html:", len(html), "byte")
sisa = re.findall(r'(?:src|href)="(?!data:)([^"]+)"', html)
print("masih ada request eksternal:", sisa or "tidak ada")
