import pathlib
import re

p = pathlib.Path("/root/kosmate/web/index.html")
t = p.read_text()
t = re.sub(r'href="style\.css[^"]*"', 'href="style.css?v=2"', t)
t = re.sub(r'src="app\.js[^"]*"', 'src="app.js?v=2"', t)
t = re.sub(r'src="extras\.js[^"]*"', 'src="extras.js?v=2"', t)
p.write_text(t)
print("versi query di index.html:", t.count("?v=2"))

b = pathlib.Path("/root/kosmate/scripts/build_single.py")
s = b.read_text()
s = s.replace(
    'html = html.replace(\'<link rel="stylesheet" href="style.css">\', f"<style>\\n{css}\\n</style>")',
    'html = re.sub(r\'<link rel="stylesheet" href="style\\.css[^"]*">\', lambda m: f"<style>\\n{css}\\n</style>", html)',
)
s = s.replace(
    'html = html.replace(f\'<script src="{nama}"></script>\', f"<script>\\n{js}\\n</script>")',
    'html = re.sub(rf\'<script src="{re.escape(nama)}[^"]*"></script>\', lambda m: f"<script>\\n{js}\\n</script>", html)',
)
b.write_text(s)
print("build_single pakai regex:", "style\\\\.css" in s)
