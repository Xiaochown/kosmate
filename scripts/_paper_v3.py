"""Bangun ulang tekstur & aset dengan palet oat yang baru."""
import math
import random
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

OUT = Path("/root/kosmate/web/assets")
W = H = 256
BASE = (246, 236, 216)  # oat terang, cocok dengan --parch #f3e9d5

rnd = random.Random(11)
img = Image.new("RGB", (W, H))
px = img.load()
for y in range(H):
    for x in range(W):
        blotch = math.sin(x / 41.0) * math.cos(y / 47.0) * 1.4
        grain = rnd.uniform(-1.6, 1.6)
        d = blotch + grain
        px[x, y] = (
            max(0, min(255, round(BASE[0] + d))),
            max(0, min(255, round(BASE[1] + d))),
            max(0, min(255, round(BASE[2] + d))),
        )
img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
img.save(OUT / "tex-paper.webp", "WEBP", quality=90, method=6)
st = ImageStat.Stat(img.convert("L"))
print(f"tex-paper.webp mean {st.mean[0]:.1f} range {st.extrema[0]}")
