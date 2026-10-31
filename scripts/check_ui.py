import re
from pathlib import Path

root = Path("/root/kosmate/web")
html = (root / "index.html").read_text()
js = (root / "app.js").read_text()

ids = set(re.findall(r'id="([^"]+)"', html))
used = set(re.findall(r'\$\("([^"]+)"\)', js))
missing = sorted(used - ids)
print("id di html :", len(ids))
print("id dipakai js:", len(used))
print("HILANG (js minta, html gak punya):", missing or "tidak ada")

# handler wajib
for fn in ["boot()", "sendMessage", "enqueueSpeech", "feedDelta", "startListening"]:
    print(f"{fn:18s}", "ada" if fn.split("(")[0] in js else "TIDAK ADA")

# css classes referenced
css = (root / "style.css").read_text()
for sel in ["body[data-state=\"listening\"]", ".orb", ".sheet.open", ".fact"]:
    print(f"css {sel:28s}", "ok" if sel in css else "TIDAK ADA")

# endpoint yang dipanggil client vs yang ada di app
app = Path("/root/kosmate/kos/app.py").read_text()
ep_js = set(re.findall(r'fetch\("(/api/[a-z/]+)', js))
ep_py = set(re.findall(r'@app\.(?:get|post|delete)\("(/api/[a-z/{}]+)"', app))
norm = lambda s: re.sub(r"\{[^}]+\}", "{}", s)
ep_py_n = {norm(p) for p in ep_py}
print("endpoint dipanggil client:", sorted(ep_js))
print("endpoint tidak ada di app:", sorted(e for e in ep_js if norm(e) not in ep_py_n) or "tidak ada")
