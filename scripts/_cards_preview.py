from pathlib import Path

from PIL import Image

A = Path("/root/kosmate/web/assets")
prev = Image.new("RGB", (640 * 2 + 30, 400 * 2 + 30), (246, 230, 196))
for i, n in enumerate(("story", "focus", "remind", "journal")):
    im = Image.open(A / f"{n}.webp").convert("RGB")
    prev.paste(im, ((i % 2) * (640 + 30), (i // 2) * (400 + 30)))
prev.save("/tmp/cards-preview.png")
print("preview /tmp/cards-preview.png (2x2 grid)")
