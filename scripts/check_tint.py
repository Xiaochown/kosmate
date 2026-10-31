from pathlib import Path

from PIL import Image, ImageStat

OUT = Path("/root/kosmate/web/assets")
for n in ("story", "focus", "remind", "journal", "banner", "mascot"):
    im = Image.open(OUT / f"{n}.webp").convert("RGB")
    w, h = im.size
    mean = [round(v) for v in ImageStat.Stat(im).mean]
    # warna sudut (indikator latar)
    k = 12
    pts = [im.getpixel((2, 2)), im.getpixel((w - 3, 2)), im.getpixel((2, h - 3)), im.getpixel((w - 3, h - 3))]
    sudut = [round(sum(p[i] for p in pts) / 4) for i in range(3)]
    print(f"{n:8s} {w}x{h}  rata-rata {tuple(mean)}  sudut {tuple(sudut)}")
