#!/usr/bin/env python3
"""Asset pipeline for cozy indie-game UI — generate once, normalize always.

Solves the three bugs that make a UI look like patchwork:
  1. different aspect ratios per slot      -> center-crop to a fixed ratio
  2. different background tint per image   -> rescale to your panel colour
  3. different brightness per image        -> grade to a target luminance

Plus a procedural paper texture (AI "paper" has blotches that become speckles
at UI scale — do not use it for a background).

Requires: Pillow  (pip install pillow / uv pip install pillow)
Usage:
    python asset_pipeline.py cards  raw/*.png --out web/assets --prefix card
    python asset_pipeline.py hero   raw/mascot.png --out web/assets --name mascot
    python asset_pipeline.py icon   raw/mascot.png --out web/assets
    python asset_pipeline.py paper  --out web/assets
"""
from __future__ import annotations

import argparse
import glob
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat

# slot -> (width, height, object width fraction inside frame)
SLOTS = {
    "card": (640, 400, 0.92),    # 16:10, content cards
    "wide": (1000, 300, 0.96),   # banner / hero strip
    "hero": (520, 520, 0.86),    # mascot, square
}
PANEL = (251, 244, 228)          # must equal your CSS --card
TARGET_LUMA = 163                # 150..180 looks consistent on cream panels


# --------------------------------------------------------------------- utils
def luma(im: Image.Image) -> float:
    g = ImageStat.Stat(im.convert("L")).mean[0]
    return round(g, 1)


def corner_color(im: Image.Image, k: int = 12) -> tuple[int, int, int]:
    w, h = im.size
    boxes = ((0, 0, k, k), (w - k, 0, w, k), (0, h - k, k, h), (w - k, h - k, w, h))
    means = [ImageStat.Stat(im.crop(b)).mean for b in boxes]
    return tuple(round(sum(m[i] for m in means) / 4) for i in range(3))


def match_bg(im: Image.Image, target=PANEL) -> Image.Image:
    """Rescale channels so the image background equals the panel colour."""
    bg = corner_color(im)
    lut = []
    for i in range(3):
        f = target[i] / max(1, bg[i])
        lut += [min(255, round(v * f)) for v in range(256)]
    return im.point(lut)


def grade(im: Image.Image, target: float = TARGET_LUMA, warm: float = 0.08,
          sat: float = 0.92) -> Image.Image:
    """Push mean luminance toward target (gamma), warm blend, mild desaturation."""
    cur = max(1.0, luma(im))
    gamma = math.log(target / 255.0) / math.log(min(0.97, cur / 255.0))
    gamma = max(0.55, min(1.8, gamma))
    lut = [min(255, round(255 * ((v / 255.0) ** gamma))) for v in range(256)]
    im = im.point(lut * 3)
    if warm > 0:
        im = Image.blend(im, Image.new("RGB", im.size, PANEL), warm)
    if sat < 1:
        g = im.convert("L").convert("RGB")
        im = Image.blend(im, g, 1 - sat)
    return im


def crop_ratio(im: Image.Image, w: int, h: int, frac: float) -> Image.Image:
    """Center-crop by a FIXED fraction of the frame (not object bbox).

    bbox cropping makes poses without props look zoomed-in, so character size
    jumps between app states. Fixed fraction keeps scale stable.
    """
    fw, fh = im.width * frac, im.height * frac
    cx, cy = im.width / 2, im.height * 0.45
    box = (round(cx - fw / 2), round(cy - fh / 2), round(cx + fw / 2), round(cy + fh / 2))
    im = im.crop(box)
    target = w / h
    if im.width / im.height > target:
        im = im.resize((round(im.height * target), im.height), Image.LANCZOS)
    else:
        im = im.resize((im.width, round(im.width / target)), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), PANEL)
    canvas.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return canvas


def trim_to_content(im: Image.Image, pad: float = 0.08) -> Image.Image:
    """Crop away empty margin around the object (use BEFORE crop_ratio for cards)."""
    bg = Image.new("RGB", im.size, corner_color(im))
    diff = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 14 else 0)
    box = diff.getbbox()
    if not box:
        return im
    x0, y0, x1, y1 = box
    px, py = round((x1 - x0) * pad), round((y1 - y0) * pad)
    return im.crop((max(0, x0 - px), max(0, y0 - py),
                    min(im.width, x1 + px), min(im.height, y1 + py)))


def save_webp(im: Image.Image, path: Path, q: int = 87) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "WEBP", quality=q, method=5)
    print(f"{path.name:28s} {im.size[0]}x{im.size[1]} {path.stat().st_size // 1024} KB  luma {luma(im)}")


# ------------------------------------------------------------------ textures
def paper_texture(out: Path, size: int = 256, base=(243, 233, 213), spread: int = 3) -> None:
    """Procedural grain: <=5 luminance levels. AI textures have blotches."""
    random.seed(7)
    im = Image.new("RGB", (size, size), base)
    px = im.load()
    for y in range(size):
        for x in range(size):
            d = random.randint(-spread, spread)
            px[x, y] = tuple(max(0, min(255, c + d)) for c in base)
    im = im.filter(ImageFilter.GaussianBlur(0.4))
    hairline = [base[0] - 1, base[1] - 1, base[2] - 1]
    for _ in range(size // 8):                       # faint fibres
        x = random.randrange(size)
        px[x, random.randrange(size)] = tuple(hairline)
    save_webp(im, out / "tex-paper.webp", q=80)


def wood_texture(src: Path, out: Path, darken: float = 0.62) -> None:
    im = Image.open(src).convert("RGB")
    im = im.resize((512, 512), Image.LANCZOS)
    im = im.point([min(255, round(v * darken)) for v in range(256)] * 3)
    save_webp(im, out / "tex-wood-dark.webp", q=82)


# --------------------------------------------------------------------- icons
def icons(src: Image.Image, out: Path) -> None:
    base = trim_to_content(src, 0.04).convert("RGB")
    for side in (192, 512):
        sq = Image.new("RGB", (max(base.size),) * 2, PANEL)
        sq.paste(base, ((sq.width - base.width) // 2, (sq.height - base.height) // 2))
        sq.resize((side, side), Image.LANCZOS).save(out / f"icon-{side}.png")
        print(f"icon-{side}.png")
    # maskable: solid pad to 78% safe zone
    mask = Image.new("RGB", (512, 512), (29, 36, 51))
    inner = base.resize((round(512 * 0.78),) * 2, Image.LANCZOS)
    mask.paste(inner, ((512 - inner.width) // 2, (512 - inner.height) // 2))
    mask.save(out / "icon-maskable-512.png")
    print("icon-maskable-512.png")


# ---------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["cards", "hero", "icon", "paper", "wood"])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--out", default="web/assets")
    ap.add_argument("--name", default="")
    ap.add_argument("--prefix", default="card")
    ap.add_argument("--slot", default="card", choices=list(SLOTS))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    if a.mode == "paper":
        paper_texture(out)
        return
    if a.mode == "wood":
        wood_texture(Path(a.files[0]), out)
        return

    paths: list[Path] = []
    for f in a.files:
        paths += [Path(p) for p in glob.glob(f)]
    if not paths:
        raise SystemExit("tidak ada file masukan")

    w, h, frac = SLOTS[a.slot]
    for i, p in enumerate(sorted(paths)):
        im = Image.open(p).convert("RGB")
        im = match_bg(im)
        im = grade(im)
        if a.mode == "icon":
            icons(im, out)
        else:
            im = trim_to_content(im) if a.mode == "cards" else im
            im = crop_ratio(im, w, h, frac)
            name = a.name or f"{a.prefix}-{i+1}"
            save_webp(im, out / f"{name}.webp")


if __name__ == "__main__":
    main()
