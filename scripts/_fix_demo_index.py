import pathlib

p = pathlib.Path("/root/kosmate/demo/index.html")
h = p.read_text()
h = h.replace("<title>Companion</title>", "<title>Kai — demo</title>")
if 'src="demo.js"' not in h:
    h = h.replace('  <script src="app.js"></script>', '  <script src="demo.js"></script>\n  <script src="app.js"></script>')
p.write_text(h)
print("demo/index.html: demo.js", "ada" if 'src="demo.js"' in h else "TIDAK ADA")

# single.html ikut dibangun ulang dari sumber yang benar
import subprocess
print(subprocess.run(["python3", "/root/kosmate/scripts/build_single.py"], capture_output=True, text=True).stdout.strip())
