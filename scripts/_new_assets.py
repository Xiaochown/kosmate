"""Konversi 6 ilustrasi baru ke webp + bikin ikon dari maskot."""
import subprocess
from pathlib import Path

from PIL import Image

CACHE = Path("/root/.hermes/cache/images")
OUT = Path("/root/kosmate/web/assets")
OUT.mkdir(parents=True, exist_ok=True)

JOBS = [
    ("teamorouter_gpt-img-2.5-sunburst_20261101_062936_9c0892f3.png", "mascot.webp", 520),
    ("teamorouter_gpt-img-2.5-sunburst_20261101_062958_cecbd875.png", "banner.webp", 1000),
    ("teamorouter_gpt-img-2.5-sunburst_20261101_063022_9fde46d0.png", "story.webp", 640),
    ("teamorouter_gpt-img-2.5-sunburst_20261101_063050_fbe439f2.png", "focus.webp", 640),
    ("teamorouter_gpt-img-2.5-sunburst_20261101_063123_0e5c2cad.png", "remind.webp", 640),
    ("teamorouter_gpt-img-2.5-sunburst_20261101_063145_16558658.png", "journal.webp", 640),
]

for src, dst, lebar in JOBS:
    f = CACHE / src
    if not f.exists():
        print("HILANG:", src)
        continue
    im = Image.open(f).convert("RGB")
    h = round(im.height * lebar / im.width)
    im = im.resize((lebar, h), Image.LANCZOS)
    im.save(OUT / dst, "WEBP", quality=84, method=4)
    print(f"{dst:14s} {lebar}x{h} {(OUT / dst).stat().st_size // 1024} KB")

# ikon dari maskot (persegi, crop tengah)
m = Image.open(CACHE / JOBS[0][0]).convert("RGB")
s = min(m.size)
m = m.crop(((m.width - s) // 2, (m.height - s) // 2, (m.width + s) // 2, (m.height + s) // 2))
for ukuran in (192, 512):
    m.resize((ukuran, ukuran), Image.LANCZOS).save(OUT / f"icon-{ukuran}.png", optimize=True)

navy = Image.new("RGB", (512, 512), (74, 44, 23))
inner = int(512 * 0.78)
navy.paste(m.resize((inner, inner), Image.LANCZOS), ((512 - inner) // 2, (512 - inner) // 2))
navy.save(OUT / "icon-maskable-512.png", optimize=True)
print("ikon 192/512/maskable dibuat ulang dari maskot")
