"""Samakan 'mood' semua ilustrasi: luminance disetarakan, warm grade, saturasi turun.

Tujuan: 4 kartu + banner kelihatan satu set (bukan patchwork), tanpa menghapus isi.
"""
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps, ImageStat

SRC = Path("/root/.hermes/cache/images")
OUT = Path("/root/kosmate/web/assets")
KREM = (247, 231, 198)

JOBS = [
    ("mascot.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_062936_9c0892f3.png", 1.0, 520, 178, 0.06),
    ("banner.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_062958_cecbd875.png", 1000 / 280, 1000, 132, 0.05),
    ("story.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_063022_9fde46d0.png", 1.6, 640, 170, 0.10),
    ("focus.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_063050_fbe439f2.png", 1.6, 640, 182, 0.08),
    ("remind.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_063123_0e5c2cad.png", 1.6, 640, 176, 0.08),
    ("journal.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_063145_16558658.png", 1.6, 640, 180, 0.08),
]


def crop(im: Image.Image, rasio: float) -> Image.Image:
    w, h = im.size
    th = round(w / rasio)
    if th <= h:
        top = (h - th) // 2
        return im.crop((0, top, w, top + th))
    tw = round(h * rasio)
    left = (w - tw) // 2
    return im.crop((left, 0, left + tw, h))


def luminance(im: Image.Image) -> float:
    return ImageStat.Stat(im.convert("L")).mean[0]


def grade(im: Image.Image, target_lum: float, warm: float) -> Image.Image:
    # 1) regangkan kontras pelan-pelan
    im = ImageOps.autocontrast(im, cutoff=0.4)
    # 2) gamma supaya luminance mendekati target
    lum = max(1.0, luminance(im))
    gamma = 1.0
    if abs(lum - target_lum) > 6:
        import math

        gamma = math.log(max(0.02, min(0.98, target_lum / 255))) / math.log(max(0.02, min(0.98, lum / 255)))
        gamma = max(0.55, min(1.75, gamma))
    if abs(gamma - 1.0) > 0.02:
        lut = [min(255, round(255 * ((v / 255) ** gamma))) for v in range(256)] * 3
        im = im.point(lut)
        im = Image.merge("RGB", im.split()[:3])
    # 3) warm blend + saturasi turun biar satu keluarga
    im = Image.blend(im, Image.new("RGB", im.size, KREM), warm)
    im = ImageEnhance.Color(im).enhance(0.92)
    return im


for nama, sumber, rasio, lebar, target, warm in JOBS:
    f = SRC / sumber
    im = Image.open(f).convert("RGB")
    sebelum = luminance(im)
    im = crop(im, rasio)
    im = im.resize((lebar, round(lebar / rasio)), Image.LANCZOS)
    im = grade(im, target, warm)
    im.save(OUT / nama, "WEBP", quality=86, method=4)
    print(f"{nama:14s} {im.width}x{im.height}  luminance {sebelum:.0f} -> {luminance(im):.0f} (target {target})  {(OUT / nama).stat().st_size // 1024} KB")

# ikon dari maskot
m = Image.open(OUT / "mascot.webp").convert("RGB")
s = min(m.size)
m = m.crop(((m.width - s) // 2, (m.height - s) // 2, (m.width + s) // 2, (m.height + s) // 2))
for u in (192, 512):
    m.resize((u, u), Image.LANCZOS).save(OUT / f"icon-{u}.png", optimize=True)
kayu = Image.new("RGB", (512, 512), (91, 58, 33))
inner = int(512 * 0.78)
kayu.paste(m.resize((inner, inner), Image.LANCZOS), ((512 - inner) // 2, (512 - inner) // 2))
kayu.save(OUT / "icon-maskable-512.png", optimize=True)
print("ikon diperbarui")
