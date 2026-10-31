"""Render layout pakai WeasyPrint lalu ukur posisi/ukuran elemen penting.

Bukan screenshot visual, tapi geometri nyata: bisa mendeteksi gambar kepotong,
elemen meluber, banner kelewat tinggi, dsb.
"""
import sys

from weasyprint import HTML

W, H = 390, 844  # ukuran HP (Poco X3 / iQOO ~ 393x851)

html = open("/root/kosmate/web/index.html").read().replace(
    "</head>", '<style>@page { size: 390px 844px; margin: 0 }</style></head>'
)
doc = HTML(string=html, base_url="/root/kosmate/web/").render()
page = doc.pages[0]
root = page._page_box


def walk(box, out):
    el = getattr(box, "element_tag", None)
    cls = ""
    try:
        cls = box.element.get("class", "") if box.element is not None else ""
    except Exception:
        cls = ""
    if el:
        out.append((el, cls, box.position_x, box.position_y, box.width, box.height))
    for child in getattr(box, "children", []) or []:
        walk(child, out)


boxes = []
walk(root, boxes)

print(f"halaman: {page.width:.0f} x {page.height:.0f} pt  (target {W}x{H} px)\n")

targets = {
    "topbar": "header",
    "banner": "pembungkus banner",
    "mode-row": "baris mode",
    "stage": "panggung",
    "orb": "maskot/orb",
    "composer": "kolom kirim",
}
for key, label in targets.items():
    hit = [b for b in boxes if key in b[1]]
    if not hit:
        print(f"  {label:18s} TIDAK KETEMU")
        continue
    el, cls, x, y, w, h = hit[0]
    print(f"  {label:18s} {w:6.1f} x {h:6.1f} pt   di ({x:6.1f}, {y:6.1f})")

print("\n  gambar (img) yang ter-render:")
for el, cls, x, y, w, h in boxes:
    if el == "img":
        rasio = (w / h) if h else 0
        print(f"    {cls or '(tanpa class)':12s} {w:6.1f} x {h:6.1f} pt  rasio {rasio:.2f}")

print("\n  cek luber (elemen lebih lebar dari halaman):")
luber = [b for b in boxes if b[4] > page.width + 1]
print(f"    {len(luber)} elemen meluber")
for b in luber[:5]:
    print(f"    - {b[0]}.{b[1][:24]:24s} lebar {b[4]:.1f} pt")

print("\n  cek tinggi total konten:", f"{max(b[3] + b[5] for b in boxes):.0f} pt")
