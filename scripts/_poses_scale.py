"""Normalisasi pose maskot pakai crop proporsional TETAP.

Kenapa bukan bbox: pose "speaking" tidak punya tunggul, jadi bbox-nya lebih kecil
dan ikut ter-zoom -> karakter terlihat lebih besar dari pose lain.
Crop tetap relatif ke kanvas asli menjaga skala karakter konsisten.
"""
import glob
from pathlib import Path

from PIL import Image, ImageStat

CACHE = Path("/root/.hermes/cache/images")
OUT = Path("/root/kosmate/web/assets")
TARGET = (251, 244, 228)

POSES = [
    ("mascot.webp", "*062936_9c0892f3.png", 0.86),
    ("mascot-listen.webp", "*074326_176f9a40.png", 0.86),
    ("mascot-think.webp", "*072112_413b80b6.png", 0.86),
    # speaking digambar tanpa tunggul -> tampak lebih besar; ambil crop lebih lebar
    ("mascot-speak.webp", "*072019_88d298f1.png", 0.97),
]

# fraksi area yang diambil, relatif ke gambar asli (biar skala seragam)
CROP_W = 0.86   # lebar
CROP_H = 0.80   # tinggi
OFFSET_Y = 0.55 # pusat vertikal sedikit di bawah tengah (objek duduk di bawah)


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


for nama, pola, cw_frac in POSES:
    f = sorted(glob.glob(str(CACHE / pola)))[-1]
    im = ke_target(Image.open(f).convert("RGB"))
    w, h = im.size
    cw, ch = round(w * cw_frac), round(h * CROP_H)
    cx, cy = w / 2, h * OFFSET_Y
    x0 = max(0, round(cx - cw / 2)); y0 = max(0, round(cy - ch / 2))
    x1 = min(w, x0 + cw); y1 = min(h, y0 + ch)
    im = im.crop((x0, y0, x1, y1))
    # kotak persegi di tengah crop, latar target
    s = max(im.size)
    kanvas = Image.new("RGB", (s, s), TARGET)
    kanvas.paste(im, ((s - im.width) // 2, (s - im.height) // 2))
    kanvas = kanvas.resize((480, 480), Image.LANCZOS)
    kanvas.save(OUT / nama, "WEBP", quality=88, method=5)
    print(f"{nama:20s} crop {cw}x{ch} -> 480  latar {sudut(kanvas)}  {(OUT/nama).stat().st_size//1024} KB")
