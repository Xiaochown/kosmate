"""Ornamen prosedural bergaya game: pemisah kayu, sudut panel, dan bingkai.

Dibuat vektor-lewat-PIL supaya ringan (beberapa KB) dan bisa diwarnai CSS.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path("/root/kosmate/web/assets")
OUT.mkdir(exist_ok=True)

WOOD_D = (74, 45, 23)
WOOD = (125, 79, 44)
WOOD_L = (169, 122, 69)
WOOD_HI = (201, 154, 95)
AMBER = (233, 166, 60)
LEAF = (111, 156, 58)


def kayu_tepi(w=64, h=20, seed=3):
    """Ubin pemisah bergaya papan kayu, bisa diulang horizontal."""
    rnd = random.Random(seed)
    im = Image.new("RGB", (w, h), WOOD)
    d = ImageDraw.Draw(im)
    for i in range(h):
        t = i / (h - 1)
        c = tuple(round(WOOD[i] + (WOOD_D[i] - WOOD[i]) * (t ** 1.3)) for i in range(3))
        d.line([(0, i), (w, i)], fill=c)
    # highlight atas
    d.line([(0, 1), (w, 1)], fill=WOOD_HI)
    d.line([(0, 2), (w, 2)], fill=WOOD_L)
    # garis serat
    for _ in range(3):
        y = rnd.randint(4, h - 5)
        d.line([(rnd.randint(0, w // 3), y), (rnd.randint(w // 2, w), y)],
               fill=tuple(max(0, c - 14) for c in WOOD))
    return im


def tombol_bulat(ukuran=44, warna=LEAF, tepi=(71, 105, 31)):
    """Bukan aset: tombol dibuat CSS. Dilewati."""
    return None


def daun(w=48, h=48, seed=5):
    """Ikon daun kecil buat ornamen judul."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([w * 0.18, h * 0.18, w * 0.82, h * 0.82], fill=LEAF + (255,), outline=WOOD_D + (255,), width=2)
    d.line([(w * 0.5, h * 0.2), (w * 0.5, h * 0.8)], fill=WOOD_D + (255,), width=2)
    return im


def bintang(w=32, h=32):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, r = w / 2, h / 2, w * 0.36
    pts = []
    for i in range(8):
        ang = math.pi * i / 4 - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.34
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    d.polygon(pts, fill=AMBER + (255,), outline=WOOD_D + (255,))
    return im


def sudut(ukuran=18, seed=1):
    """Potongan sudut kayu (dipakai sebagai border-image sudut panel)."""
    im = Image.new("RGBA", (ukuran, ukuran), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, ukuran - 1, ukuran - 1], radius=5, fill=WOOD + (255,), outline=WOOD_D + (255,), width=2)
    d.line([(3, 3), (ukuran - 6, 3)], fill=WOOD_HI + (255,), width=1)
    return im


tepi = kayu_tepi()
tepi.save(OUT / "orn-wood-edge.webp", "WEBP", quality=90, method=6)
daun(48, 48).save(OUT / "orn-leaf.png")
bintang(32, 32).save(OUT / "orn-star.png")
sudut(18).save(OUT / "orn-corner.png")
for f in ("orn-wood-edge.webp", "orn-leaf.png", "orn-star.png", "orn-corner.png"):
    print(f"{f:22s} {(OUT/f).stat().st_size/1024:.1f} KB")
