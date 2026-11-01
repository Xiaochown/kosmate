from PIL import Image, ImageEnhance

im = Image.open("/root/kosmate/web/assets/tex-wood.webp").convert("RGB")
gelap = ImageEnhance.Brightness(im).enhance(0.62)
gelap = ImageEnhance.Color(gelap).enhance(0.85)
gelap.save("/root/kosmate/web/assets/tex-wood-dark.webp", "WEBP", quality=82, method=5)

prev = Image.new("RGB", (im.width * 2 + 24, im.height), (247, 231, 198))
prev.paste(im, (0, 0))
prev.paste(gelap, (im.width + 24, 0))
prev.save("/tmp/tex-preview.png")
print("tex-wood-dark.webp", gelap.size, "| preview /tmp/tex-preview.png")
