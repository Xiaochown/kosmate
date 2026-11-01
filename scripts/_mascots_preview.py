from pathlib import Path

from PIL import Image

A = Path("/root/kosmate/web/assets")
names = ["mascot", "mascot-listen", "mascot-think", "mascot-speak"]
ims = [Image.open(A / f"{n}.webp").convert("RGB") for n in names]
w = 300
out = Image.new("RGB", (w * len(ims) + 10 * (len(ims) - 1), w), (243, 233, 213))
x = 0
for im in ims:
    out.paste(im.resize((w, w), Image.LANCZOS), (x, 0))
    x += w + 10
out.save("/tmp/mascots.png")
print("urutan:", names)
