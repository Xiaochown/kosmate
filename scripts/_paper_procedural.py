"""Tekstur kertas dibuat prosedural: krem bersih + grain sangat halus.

Pelajaran: tekstur hasil AI punya noda yang jadi bintik kontras waktu dipakai
sebagai latar. Untuk latar UI, grain harus hampir tak terlihat (<= 5 level).
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat

OUT = Path("/root/kosmate/web/assets")
W = H = 256
BASE = (247, 234, 208)  # krem terang

rnd = random.Random(11)
img = Image.new("RGB", (W, H))
px = img.load()

for y in range(H):
    for x in range(W):
        # gelombang sangat lembut (skala besar) + grain halus
        blotch = math.sin(x / 37.0) * math.cos(y / 43.0) * 1.6
        grain = rnd.uniform(-1.8, 1.8)
        d = blotch + grain
        px[x, y] = (
            max(0, min(255, round(BASE[0] + d))),
            max(0, min(255, round(BASE[1] + d))),
            max(0, min(255, round(BASE[2] + d))),
        )

img = img.filter(ImageFilter.GaussianBlur(radius=0.35))
img.save(OUT / "tex-paper.webp", "WEBP", quality=90, method=6)

st = ImageStat.Stat(img.convert("L"))
print(f"tex-paper.webp {W}x{H}  mean {st.mean[0]:.1f}  range {st.extrema[0]}  {(OUT/'tex-paper.webp').stat().st_size//1024} KB")

# pratinjau: bandingkan dengan versi lama (kalau ada cadangan)
prev = Image.new("RGB", (W * 2 + 16, H), (255, 255, 255))
prev.paste(img, (0, 0))
lama = Path("/root/kosmate/screens/paper_lama.webp")
if lama.exists():
    prev.paste(Image.open(lama).convert("RGB").resize((W, H)), (W + 16, 0))
prev.save("/tmp/paper-preview.png")
print("preview /tmp/paper-preview.png (kiri baru)")
