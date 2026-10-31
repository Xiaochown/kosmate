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


def data_uri(path: pathlib.Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


# inline gambar
for nama, mime in (("story.webp", "image/webp"), ("focus.webp", "image/webp"),
                   ("remind.webp", "image/webp"), ("journal.webp", "image/webp"),
                   ("banner.webp", "image/webp"), ("mascot.webp", "image/webp"),
                   ("icon-192.png", "image/png")):
    f = ROOT / "assets" / nama
    if f.exists():
        html = html.replace(f'src="assets/{nama}"', f'src="{data_uri(f, mime)}"')
        html = html.replace(f'href="assets/{nama}"', f'href="{data_uri(f, mime)}"')

# buang manifest + stylesheet eksternal, sisip CSS
html = re.sub(r'\s*<link rel="manifest"[^>]*>', "", html)
html = re.sub(r'\s*<link rel="preconnect"[^>]*>', "", html)
html = re.sub(r'\s*<link href="https://fonts\.googleapis\.com[^>]*>', "", html)
html = html.replace('<link rel="stylesheet" href="style.css">', f"<style>\n{css}\n</style>")

# sisip JS inline, buang tag eksternal
for src, isi in (("demo.js", demo), ("app.js", app), ("extras.js", extras)):
    html = html.replace(f'<script src="{src}"></script>', f"<script>\n{isi}\n</script>")

(ROOT / "single.html").write_text(html)
print("single.html:", len(html), "byte")
sisa = re.findall(r'(?:src|href)="(?!data:)([^"]+)"', html)
print("masih ada request eksternal:", sisa or "tidak ada")
