"""Normalisasi ilustrasi: rasio disamakan, ukuran disamakan, tint krem diseragamkan.

Kenapa: tiap gambar digenerate terpisah -> rasio & warna latar beda tipis,
jadi di grid kelihatan patchwork / "tidak fit".
"""
from pathlib import Path

from PIL import Image, ImageEnhance

SRC = Path("/root/.hermes/cache/images")
OUT = Path("/root/kosmate/web/assets")
TARGET_KREM = (247, 238, 216)  # krem acuan UI (--paper terang)

# nama -> (file sumber, rasio target, lebar output)
JOBS = [
    ("mascot.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_062936_9c0892f3.png", 1.0, 520),
    ("banner.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_062958_cecbd875.png", 1000 / 300, 1000),
    ("story.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_063022_9fde46d0.png", 1.6, 640),
    ("focus.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_063050_fbe439f2.png", 1.6, 640),
    ("remind.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_063123_0e5c2cad.png", 1.6, 640),
    ("journal.webp", "teamorouter_gpt-img-2.5-sunburst_20261101_063145_16558658.png", 1.6, 640),
]


def crop_rasio(im: Image.Image, rasio: float) -> Image.Image:
    w, h = im.size
    target_h = round(w / rasio)
    if target_h <= h:  # buang atas-bawah
        top = (h - target_h) // 2
        return im.crop((0, top, w, top + target_h))
    target_w = round(h * rasio)  # buang kiri-kanan
    left = (w - target_w) // 2
    return im.crop((left, 0, left + target_w, h))


def krem_rapikan(im: Image.Image) -> Image.Image:
    """Geser white-balance supaya warna latar (sudut gambar) mendekati krem acuan."""
    w, h = im.size
    n = 14
    patches = [
        im.crop((0, 0, n, n)), im.crop((w - n, 0, w, n)),
        im.crop((0, h - n, n, h)), im.crop((w - n, h - n, w, h)),
    ]
    total = [0, 0, 0]
    for p in patches:
        for px in p.convert("RGB").getdata():
            for i in range(3):
                total[i] += px[i]
    count = n * n * 4
    mean = [t / count for t in total]

    faktor = []
    for i in range(3):
        f = TARGET_KREM[i] / max(1.0, mean[i])
        faktor.append(max(0.86, min(1.20, f)))  # jangan ekstrem

    lut = []
    for i in range(3):
        lut += [min(255, round(v * faktor[i])) for v in range(256)]
    out = im.point(lut)
    return ImageEnhance.Color(out).enhance(0.97)  # sedikit turunkan saturasi biar nyatu


for nama, sumber, rasio, lebar in JOBS:
    f = SRC / sumber
    if not f.exists():
        print("HILANG:", sumber)
        continue
    im = Image.open(f).convert("RGB")
    im = crop_rasio(im, rasio)
    tinggi = round(lebar / rasio)
    im = im.resize((lebar, tinggi), Image.LANCZOS)
    im = krem_rapikan(im)
    im.save(OUT / nama, "WEBP", quality=85, method=4)
    print(f"{nama:14s} {lebar}x{tinggi}  {(OUT / nama).stat().st_size // 1024} KB")

# ikon dari maskot yang sudah dirapikan (persegi, crop tengah)
m = Image.open(OUT / "mascot.webp").convert("RGB")
s = min(m.size)
m = m.crop(((m.width - s) // 2, (m.height - s) // 2, (m.width + s) // 2, (m.height + s) // 2))
for ukuran in (192, 512):
    m.resize((ukuran, ukuran), Image.LANCZOS).save(OUT / f"icon-{ukuran}.png", optimize=True)

kayu = Image.new("RGB", (512, 512), (74, 44, 23))
inner = int(512 * 0.78)
kayu.paste(m.resize((inner, inner), Image.LANCZOS), ((512 - inner) // 2, (512 - inner) // 2))
kayu.save(OUT / "icon-maskable-512.png", optimize=True)
print("ikon 192/512/maskable dibuat dari maskot yang sudah dirapikan")
