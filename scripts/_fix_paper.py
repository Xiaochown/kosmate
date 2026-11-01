"""Perbaiki tekstur kertas: noda gelap dihilangkan, sisa grain halus saja.

Masalah sebelumnya: brightening menaikkan noda jadi bintik kontras -> tampak
seperti plester rusak. Solusi: blur kuat (hilangkan bintik), lalu tambah noise
halus sendiri, lalu turunkan kontras.
"""
import random
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps, ImageStat

OUT = Path("/root/kosmate/web/assets")
SRC = Path("/root/.hermes/cache/images")
import glob

jam = sorted(glob.glob(str(SRC / "*072245_028495ed.png")))[-1]

base = Image.open(jam).convert("L")
# 1) buang bintik: blur besar lalu perkecil -> cuma tersisa variasi sangat lembut
base = base.filter(ImageFilter.GaussianBlur(radius=9)).resize((256, 256), Image.LANCZOS)
# 2) ratakan ke arah terang: kontras ditekan keras
base = ImageOps.autocontrast(base, cutoff=2)
mean = ImageStat.Stat(base).mean[0]
# tarik semua nilai ke 244..250 (hampir putih, sisakan 6 level saja)
piksel = [min(252, max(238, 244 + int((v - mean) * 0.10))) for v in base.getdata()] if False else None
data = list(base.getdata())
data = [min(252, max(238, round(244 + (v - mean) * 0.12))) for v in data]
base.putdata(data)

# 3) tambah grain halus sendiri (deterministik biar hasil stabil)
rnd = random.Random(7)
noise = Image.new("L", base.size)
noise.putdata([rnd.randint(240, 250) for _ in range(base.width * base.height)])
halus = Image.blend(base, noise, 0.55).filter(ImageFilter.GaussianBlur(radius=0.6))

# 4) warnai jadi krem
krem = (247, 231, 198)
warna = Image.new("RGB", halus.size)
warna.putdata([(int(krem[0] * v / 255), int(krem[1] * v / 255), int(krem[2] * v / 255)) for v in halus.getdata()])
warna = warna.resize((512, 512), Image.LANCZOS)
warna.save(OUT / "tex-paper.webp", "WEBP", quality=88, method=5)

st = ImageStat.Stat(warna.convert("L"))
print(f"tex-paper.webp 512x512  mean {st.mean[0]:.1f}  min/max {st.extrema[0]}  {(OUT/'tex-paper.webp').stat().st_size//1024} KB")
