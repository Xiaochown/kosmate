"""Proses 4 pose maskot: crop persegi, latar disamakan ke --card (#fbf4e4)."""
import glob
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

CACHE = Path("/root/.hermes/cache/images")
OUT = Path("/root/kosmate/web/assets")
TARGET = (251, 244, 228)  # --card

POSES = [
    ("mascot.webp", "*062936_9c0892f3.png"),
    ("mascot-listen.webp", "*074326_176f9a40.png"),
    ("mascot-think.webp", "*072112_413b80b6.png"),
    ("mascot-speak.webp", "*072019_88d298f1.png"),
]


def sudut(im):
    w, h = im.size
    k = 10
    pts = [ImageStat.Stat(im.crop(b)).mean for b in
           ((0, 0, k, k), (w - k, 0, w, k), (0, h - k, k, h), (w - k, h - k, w, h))]
    return tuple(round(sum(p[i] for p in pts) / 4) for i in range(3))


def ke_target(im):
    bg = sudut(im)
    f = [TARGET[i] / max(1, bg[i]) for i in range(3)]
    lut = []
    for i in range(3):
        lut += [min(255, round(v * f[i])) for v in range(256)]
    return im.point(lut)


def bbox(im, tol=15):
    bg = sudut(im)
    d = ImageChops.difference(im, Image.new("RGB", im.size, bg)).convert("L")
    return d.point(lambda v: 255 if v > tol else 0).getbbox()


for nama, pola in POSES:
    f = sorted(glob.glob(str(CACHE / pola)))[-1]
    im = Image.open(f).convert("RGB")
    im = ke_target(im)
    b = bbox(im)
    if b:
        x0, y0, x1, y1 = b
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        sisi = max(x1 - x0, y1 - y0) * 1.16  # margin ~8% tiap sisi
        x0 = max(0, round(cx - sisi / 2)); y0 = max(0, round(cy - sisi / 2))
        x1 = min(im.width, round(cx + sisi / 2)); y1 = min(im.height, round(cy + sisi / 2))
        im = im.crop((x0, y0, x1, y1))
    # tempel ke kanvas persegi dengan latar target
    s = max(im.size)
    kanvas = Image.new("RGB", (s, s), TARGET)
    kanvas.paste(im, ((s - im.width) // 2, (s - im.height) // 2))
    kanvas = kanvas.resize((480, 480), Image.LANCZOS)
    kanvas.save(OUT / nama, "WEBP", quality=88, method=5)
    print(f"{nama:20s} 480x480  latar {sudut(kanvas)}  {(OUT/nama).stat().st_size//1024} KB")
