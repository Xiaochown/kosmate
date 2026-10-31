"""Cek konsistensi: .env.example <-> config.py <-> script yang dirujuk tutor."""
import re
from pathlib import Path

root = Path("/root/kosmate")
env = (root / ".env.example").read_text()
cfg = (root / "kos/config.py").read_text()

env_keys = set(re.findall(r"^([A-Z_]+)=", env, re.M))
cfg_keys = set(re.findall(r'get\("([A-Z_]+)"', cfg))

print("key di .env.example :", len(env_keys))
print("key dipakai config  :", len(cfg_keys))
print("dipakai tapi GAK ada di contoh:", sorted(cfg_keys - env_keys) or "tidak ada")
print("ada di contoh tapi GAK dipakai:", sorted(env_keys - cfg_keys) or "tidak ada")

print()
scripts = ["scripts/install.sh", "scripts/termux-start.sh", "scripts/termux-boot.sh",
           "scripts/kiosk.sh", "scripts/smoke.sh", "run.sh"]
for s in scripts:
    p = root / s
    print(f"{s:34s}", "ada" if p.exists() else "HILANG")

print()
# endpoint yang disebut di README/tutor harus beneran ada di app
app = (root / "kos/app.py").read_text()
routes = set(re.findall(r'@app\.(get|post|delete)\("([^"]+)"', app))
print("routes:", sorted(r[1] for r in routes))

for extra in ["docs/BLUEPRINT.html", "docs/TUTORIAL.html", ".gitignore", "README.md"]:
    print(f"{extra:34s}", "ada" if (root / extra).exists() else "belum ada")
