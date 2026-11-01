"""Proses semua aset baru: crop rasio, samakan tone, tekstur, ikon.

Sumber: gambar hasil generate di /root/.hermes/cache/images/
Target akhir di /root/kosmate/web/assets/
"""
import glob
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps, ImageStat

CACHE = Path("/root/.hermes/cache/images")
OUT = Path("/root/kosmate/web/assets")
OUT.mkdir(parents=True, exist_ok=True)


def find(pattern: str) -> Path:
    hits = sorted(glob.glob(str(CACHE / pattern)))
    if not hits:
        raise SystemExit("tidak ketemu: " + pattern)
    return Path(hits[-1])


# nama file hasil -> (pola sumber, rasio, lebar, target luminance, warm blend)
JOBS = [
    ("mascot.webp", find("*062936_9c*o") if False else find("*062936_9c0892f3.png"), 1.0, 480, 200, 0.03),
    ("mascot-listen.webp", find("*071705_03d34b6a.png"), 1.0, 480, 200, 0.03),
    ("mascot-think.webp", find("*072112_413b80b6.png"), 1.0, 480, 200, 0.03),
    ("mascot-speak.webp", find("*072019_88d298f1.png"), 1.0, 480, 200, 0.03),
    ("banner.webp", find("*072130_3d886038.png"), 1000 / 300, 1000, 150, 0.04),
    ("story.webp", find("*071619_0d168ed6.png"), 1.6, 640, 226, 0.02),
    ("focus.webp", find("*071854_1240a585.png"), 1.6, 640, 226, 0.02),
    ("remind.webp", find("*071910_19af0342.png"), 1.6, 640, 226, 0.02),
    ("journal.webp", find("*071959_1fd52630.png"), 1.6, 640, 226, 0.02),
]
KREM = (247, 231, 198)


def crop(im, rasio):
    w, h = im.size
    th = round(w / rasio)
    if th <= h:
        top = (h - th) // 2
        return im.crop((0, top, w, top + th))
    tw = round(h * rasio)
    left = (w - tw) // 2
    return im.crop((left, 0, left + tw, h))


def lum(im):
    return ImageStat.Stat(im.convert("L")).mean[0]


def grade(im, target, warm, sat=0.98):
    im = ImageOps.autocontrast(im, cutoff=0.3)
    now = max(1.0, lum(im))
    if abs(now - target) > 3:
        import math
        g = math.log(target / 255) / math.log(now / 255)
        g = max(0.6, min(1.7, g))
        lut = [min(255, round(255 * ((v / 255) ** g))) for v in range(256)] * 3
        im = im.point(lut)
    if warm:
        im = Image.blend(im, Image.new("RGB", im.size, KREM), warm)
    return ImageEnhance.Color(im).enhance(sat)


print("--- ilustrasi ---")
for nama, src, rasio, lebar, target, warm in JOBS:
    im = Image.open(src).convert("RGB")
    awal = lum(im)
    im = crop(im, rasio).resize((lebar, round(lebar / rasio)), Image.LANCZOS)
    im = grade(im, target, warm)
    im.save(OUT / nama, "WEBP", quality=87, method=5)
    print(f"{nama:20s} {im.width}x{im.height}  lum {awal:.0f} -> {lum(im):.0f}  {(OUT / nama).stat().st_size//1024} KB")

# ---------------- tekstur ----------------
print("--- tekstur ---")
kayu_src = Image.open(find("*072229_31503220.png")).convert("RGB")
kayu = kayu_src.resize((512, 512), Image.LANCZOS)
kayu = grade(kayu, 118, 0.10, 0.88)  # agak gelap & kalem biar teks putih kebaca
kayu.save(OUT / "tex-wood.webp", "WEBP", quality=82, method=5)
print(f"tex-wood.webp      512x512  lum {lum(kayu):.0f}  {(OUT/'tex-wood.webp').stat().st_size//1024} KB")

kertas_src = Image.open(find("*072245_028495ed.png")).convert("RGB")
kertas = kertas_src.resize((512, 512), Image.LANCZOS)
kertas = grade(kertas, 250, 0.0, 0.30)  # hampir rata, cuma grain
# tarik ke terang: tekstur harus jadi latar, bukan noda
kertas = ImageEnhance.Brightness(kertas).enhance(1.0 + max(0.0, (244 - lum(kertas)) / 255))
kertas.save(OUT / "tex-paper.webp", "WEBP", quality=80, method=5)
print(f"tex-paper.webp     512x512  lum {lum(kertas):.0f}  {(OUT/'tex-paper.webp').stat().st_size//1024} KB")

# ---------------- ikon ----------------
print("--- ikon ---")
m = Image.open(OUT / "mascot.webp").convert("RGB")
s = min(m.size)
m = m.crop(((m.width - s) // 2, (m.height - s) // 2, (m.width + s) // 2, (m.height + s) // 2))
for u in (192, 512):
    m.resize((u, u), Image.LANCZOS).save(OUT / f"icon-{u}.png", optimize=True)
    print(f"icon-{u}.png")
kayu_ikon = Image.new("RGB", (512, 512), (91, 58, 33))
inner = int(512 * 0.76)
kayu_ikon.paste(m.resize((inner, inner), Image.LANCZOS), ((512 - inner) // 2, (512 - inner) // 2))
kayu_ikon.save(OUT / "icon-maskable-512.png", optimize=True)
print("icon-maskable-512.png")
