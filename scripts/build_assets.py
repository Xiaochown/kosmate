"""Bangun ulang SEMUA aset final dari sumber generate, dengan palet oat.

Satu perintah, hasil deterministik. Dipakai sebelum commit.
"""
import glob
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageStat

CACHE = Path("/root/.hermes/cache/images")
OUT = Path("/root/kosmate/web/assets")
OUT.mkdir(parents=True, exist_ok=True)

CARD = (251, 244, 228)      # --card
PAPER = (246, 236, 216)     # --parch terang


def f(pola):
    return sorted(glob.glob(str(CACHE / pola)))[-1]


def sudut(im):
    w, h = im.size
    k = 10
    pts = [ImageStat.Stat(im.crop(b)).mean for b in
           ((0, 0, k, k), (w - k, 0, w, k), (0, h - k, k, h), (w - k, h - k, w, h))]
    return tuple(round(sum(p[i] for p in pts) / 4) for i in range(3))


def ke_warna(im, target):
    bg = sudut(im)
    faktor = [target[i] / max(1, bg[i]) for i in range(3)]
    lut = []
    for i in range(3):
        lut += [min(255, round(v * faktor[i])) for v in range(256)]
    return im.point(lut)


def bbox(im, tol=15):
    bg = sudut(im)
    d = ImageChops.difference(im, Image.new("RGB", im.size, bg)).convert("L")
    return d.point(lambda v: 255 if v > tol else 0).getbbox()


print("=== MASKOT (4 pose) ===")
for nama, pola, cw_frac in (
    ("mascot.webp", "*062936_9c0892f3.png", 0.86),
    ("mascot-listen.webp", "*074326_176f9a40.png", 0.86),
    ("mascot-think.webp", "*072112_413b80b6.png", 0.86),
    ("mascot-speak.webp", "*072019_88d298f1.png", 0.97),
):
    im = ke_warna(Image.open(f(pola)).convert("RGB"), CARD)
    w, h = im.size
    cw, ch = round(w * cw_frac), round(h * 0.80)
    cx, cy = w / 2, h * 0.55
    x0, y0 = max(0, round(cx - cw / 2)), max(0, round(cy - ch / 2))
    im = im.crop((x0, y0, min(w, x0 + cw), min(h, y0 + ch)))
    s = max(im.size)
    kanvas = Image.new("RGB", (s, s), CARD)
    kanvas.paste(im, ((s - im.width) // 2, (s - im.height) // 2))
    kanvas.resize((480, 480), Image.LANCZOS).save(OUT / nama, "WEBP", quality=88, method=5)
    print(f"  {nama:20s} 480x480 {(OUT/nama).stat().st_size//1024:3d} KB")

print("=== KARTU AKSI (4 gambar 640x400) ===")
for nama, pola in (
    ("story.webp", "*071619_0d168ed6.png"),
    ("focus.webp", "*071854_1240a585.png"),
    ("remind.webp", "*071910_19af0342.png"),
    ("journal.webp", "*071959_1fd52630.png"),
):
    im = ke_warna(Image.open(f(pola)).convert("RGB"), CARD)
    b = bbox(im, 14)
    if b:
        x0, y0, x1, y1 = b
        px, py = round((x1 - x0) * 0.07), round((y1 - y0) * 0.07)
        im = im.crop((max(0, x0 - px), max(0, y0 - py),
                      min(im.width, x1 + px), min(im.height, y1 + py)))
    w, h = im.size
    if w / h > 1.6:
        im = im.resize((w, round(w / 1.6)), Image.LANCZOS)
    else:
        im = im.resize((round(h * 1.6), h), Image.LANCZOS)
    # tempel ke kanvas 16:10 tepat, latar CARD (tidak ada yang terpotong)
    kanvas = Image.new("RGB", (640, 400), CARD)
    skala = min(640 / im.width, 400 / im.height)
    kecil = im.resize((round(im.width * skala), round(im.height * skala)), Image.LANCZOS)
    kanvas.paste(kecil, ((640 - kecil.width) // 2, (400 - kecil.height) // 2))
    kanvas.save(OUT / nama, "WEBP", quality=87, method=5)
    print(f"  {nama:20s} 640x400 latar {sudut(kanvas)} {(OUT/nama).stat().st_size//1024:3d} KB")

print("=== BANNER ===")
ban = Image.open(f("*072130_3d886038.png")).convert("RGB")
w, h = ban.size
th = round(w / (1000 / 300))
top = max(0, (h - th) // 2 - round(h * 0.03))
ban = ban.crop((0, top, w, min(h, top + th))).resize((1000, 300), Image.LANCZOS)
ban = ImageEnhance.Brightness(ban).enhance(1.06)
ban.save(OUT / "banner.webp", "WEBP", quality=86, method=5)
print(f"  banner.webp 1000x300 {(OUT/'banner.webp').stat().st_size//1024} KB")

print("=== TEKSTUR ===")
# kertas: prosedural, grain sangat halus
W = H = 256
rnd = random.Random(11)
im = Image.new("RGB", (W, H))
px = im.load()
for y in range(H):
    for x in range(W):
        d = math.sin(x / 41.0) * math.cos(y / 47.0) * 1.4 + rnd.uniform(-1.6, 1.6)
        px[x, y] = tuple(max(0, min(255, round(c + d))) for c in PAPER)
im = im.filter(ImageFilter.GaussianBlur(radius=0.3))
im.save(OUT / "tex-paper.webp", "WEBP", quality=90, method=6)
print(f"  tex-paper.webp {W}x{H} mean {ImageStat.Stat(im.convert('L')).mean[0]:.0f}")

# kayu: dari generate, digelapkan supaya teks krem kontras
kayu = Image.open(f("*072229_31503220.png")).convert("RGB").resize((512, 512), Image.LANCZOS)
kayu = ImageEnhance.Brightness(kayu).enhance(0.60)
kayu = ImageEnhance.Color(kayu).enhance(0.84)
kayu.save(OUT / "tex-wood-dark.webp", "WEBP", quality=82, method=5)
kayu2 = ImageEnhance.Brightness(Image.open(f("*072229_31503220.png")).convert("RGB").resize((512, 512), Image.LANCZOS)).enhance(0.82)
kayu2.save(OUT / "tex-wood.webp", "WEBP", quality=82, method=5)
print(f"  tex-wood-dark.webp 512 {ImageStat.Stat(kayu.convert('L')).mean[0]:.0f} lum")

print("=== IKON ===")
m = Image.open(OUT / "mascot.webp").convert("RGB")
s = min(m.size)
m = m.crop(((m.width - s) // 2, (m.height - s) // 2, (m.width + s) // 2, (m.height + s) // 2))
for u in (192, 512):
    m.resize((u, u), Image.LANCZOS).save(OUT / f"icon-{u}.png", optimize=True)
    print(f"  icon-{u}.png")
kayu_ikon = Image.new("RGB", (512, 512), (92, 63, 36))
inner = int(512 * 0.78)
kayu_ikon.paste(m.resize((inner, inner), Image.LANCZOS), ((512 - inner) // 2, (512 - inner) // 2))
kayu_ikon.save(OUT / "icon-maskable-512.png", optimize=True)
print("  icon-maskable-512.png")
