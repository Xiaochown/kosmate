"""Samakan latar ilustrasi kartu dengan krem UI (#fdf3dd) + objek dibuat lebih besar.

Masalah: latar gambar hasil generate putih murni, jadi terlihat seperti gambar
tempelan. Solusi: ambil warna sudut tiap gambar, geser ke krem UI, lalu crop
lebih ketat supaya objek mengisi frame.
"""
import glob
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageStat

CACHE = Path("/root/.hermes/cache/images")
OUT = Path("/root/kosmate/web/assets")
TARGET = (253, 243, 221)  # --card

JOBS = [
    ("story.webp", "*071619_0d168ed6.png"),
    ("focus.webp", "*071854_1240a585.png"),
    ("remind.webp", "*071910_19af0342.png"),
    ("journal.webp", "*071959_1fd52630.png"),
    ("mascot.webp", "*062936_9c0892f3.png"),
    ("mascot-listen.webp", "*071705_03d34b6a.png"),
    ("mascot-think.webp", "*072112_413b80b6.png"),
    ("mascot-speak.webp", "*072019_88d298f1.png"),
]


def sudut_warna(im: Image.Image) -> tuple:
    """Ambil warna latar dari 4 sudut."""
    w, h = im.size
    k = 10
    pts = []
    for box in ((0, 0, k, k), (w - k, 0, w, k), (0, h - k, k, h), (w - k, h - k, w, h)):
        pts.append(ImageStat.Stat(im.crop(box)).mean)
    return tuple(round(sum(p[i] for p in pts) / 4) for i in range(3))


def bbox_objek(im: Image.Image, toleransi: int = 16):
    """Cari kotak objek: piksel yang beda dari warna latar."""
    bg = sudut_warna(im)
    latar = Image.new("RGB", im.size, bg)
    diff = ImageChops.difference(im, latar).convert("L")
    mask = diff.point(lambda v: 255 if v > toleransi else 0)
    return mask.getbbox()


def ke_krem(im: Image.Image) -> Image.Image:
    """Geser seluruh gambar supaya warna latar == TARGET."""
    bg = sudut_warna(im)
    # rasio per kanal -> latar jadi TARGET, sisanya ikut bergeser (white balance)
    faktor = [TARGET[i] / max(1, bg[i]) for i in range(3)]
    lut = []
    for i in range(3):
        lut += [min(255, round(v * faktor[i])) for v in range(256)]
    return im.point(lut)


print("--- kartu (latar disamakan + objek diperbesar) ---")
for nama, pola in JOBS:
    src = sorted(glob.glob(str(CACHE / pola)))[-1]
    im = Image.open(src).convert("RGB")
    im = ke_krem(im)

    if nama.startswith("mascot"):
        # maskot: persegi, objek di tengah, margin 8%
        w, h = im.size
        s = min(w, h)
        im = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
        lebar = 480
        im = im.resize((lebar, lebar), Image.LANCZOS)
    else:
        box = bbox_objek(im, 14)
        if box:
            x0, y0, x1, y1 = box
            # beri napas 7% tiap sisi
            px = round((x1 - x0) * 0.07)
            py = round((y1 - y0) * 0.07)
            x0 = max(0, x0 - px); y0 = max(0, y0 - py)
            x1 = min(im.width, x1 + px); y1 = min(im.height, y1 + py)
            im = im.crop((x0, y0, x1, y1))
        # paksa 16:10 lalu skala
        w, h = im.size
        rasio = 1.6
        if w / h > rasio:
            nh = round(w / rasio)
            im = im.resize((w, nh), Image.LANCZOS)
        else:
            nw = round(h * rasio)
            im = im.resize((nw, h), Image.LANCZOS)
        im = im.resize((640, 400), Image.LANCZOS)
        lebar = 640

    im = ImageEnhance.Color(im).enhance(1.0)
    im.save(OUT / nama, "WEBP", quality=87, method=5)
    bg = sudut_warna(im)
    print(f"{nama:20s} {im.width}x{im.height}  latar {bg}  {(OUT/nama).stat().st_size//1024} KB")
