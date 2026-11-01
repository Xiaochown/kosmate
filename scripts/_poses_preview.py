from pathlib import Path

from PIL import Image

S = Path("/root/kosmate/screens")
files = ["idle-1.png", "idle-listening-1.png", "idle-thinking-1.png", "idle-speaking-1.png"]
ada = [f for f in files if (S / f).exists()]
if not ada:
    raise SystemExit("tidak ada screenshot")

# ambil potongan area maskot saja (tengah atas) biar vision fokus ke pose
crops = []
for f in ada:
    im = Image.open(S / f).convert("RGB")
    w, h = im.size
    crops.append(im.crop((int(w * 0.28), int(h * 0.30), int(w * 0.72), int(h * 0.62))))

cw = max(c.width for c in crops)
ch = max(c.height for c in crops)
out = Image.new("RGB", (cw * len(crops) + 12 * (len(crops) - 1), ch), (243, 233, 213))
x = 0
for c in crops:
    out.paste(c, (x, 0))
    x += cw + 12
out.save("/tmp/poses.png")
print("preview /tmp/poses.png |", ada)
