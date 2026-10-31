from PIL import Image

src = Image.open("/root/kosmate/web/assets/icon-512.png").convert("RGBA")
canvas = Image.new("RGBA", (512, 512), (29, 36, 51, 255))  # navy, sama dengan latar ikon
inner = int(512 * 0.78)  # safe zone maskable ~80%
ic = src.resize((inner, inner), Image.LANCZOS)
off = (512 - inner) // 2
canvas.paste(ic, (off, off), ic)
out = "/root/kosmate/web/assets/icon-maskable-512.png"
canvas.convert("RGB").save(out, optimize=True)
print("maskable:", Image.open(out).size)
