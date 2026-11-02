"""Aset kartu nyanyi: crop 16:10, latar disamakan dengan --card."""
import glob
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

CARD = (251, 244, 228)
CACHE = Path("/root/.hermes/cache/images")
OUT = Path("/root/kosmate/web/assets")

src = sorted(glob.glob(str(CACHE / "*213205_458fd474.png")))[-1]
im = Image.open(src).convert("RGB")


def sudut(x):
    w, h = x.size
    k = 10
    pts = [ImageStat.Stat(x.crop(b)).mean for b in ((0, 0, k, k), (w - k, 0, w, k), (0, h - k, k, h), (w - k, h - k, w, h))]
    return tuple(round(sum(p[i] for p in pts) / 4) for i in range(3))


bg = sudut(im)
lut = []
for i in range(3):
    f = CARD[i] / max(1, bg[i])
    lut += [min(255, round(v * f)) for v in range(256)]
im = im.point(lut)

# bbox objek -> crop rapi
d = ImageChops.difference(im, Image.new("RGB", im.size, sudut(im))).convert("L")
box = d.point(lambda v: 255 if v > 14 else 0).getbbox()
if box:
    x0, y0, x1, y1 = box
    px, py = round((x1 - x0) * 0.08), round((y1 - y0) * 0.08)
    im = im.crop((max(0, x0 - px), max(0, y0 - py), min(im.width, x1 + px), min(im.height, y1 + py)))

w, h = im.size
if w / h > 1.6:
    im = im.resize((w, round(w / 1.6)), Image.LANCZOS)
else:
    im = im.resize((round(h * 1.6), h), Image.LANCZOS)
kanvas = Image.new("RGB", (640, 400), CARD)
skala = min(640 / im.width, 400 / im.height)
kecil = im.resize((round(im.width * skala), round(im.height * skala)), Image.LANCZOS)
kanvas.paste(kecil, ((640 - kecil.width) // 2, (400 - kecil.height) // 2))
kanvas.save(OUT / "sing.webp", "WEBP", quality=87, method=5)
print("sing.webp:", kanvas.size, (OUT / "sing.webp").stat().st_size // 1024, "KB", "latar", sudut(kanvas))
