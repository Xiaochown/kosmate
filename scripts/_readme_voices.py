import pathlib

p = pathlib.Path("/root/kosmate/README.md")
t = p.read_text()

blok = """
## Suara (Fish Audio)

| kunci | nama | tempo |
|---|---|---|
| `miyaa` | Miyaa — perempuan muda, ceria (default) | 0.80x |
| `beatrix` | Beatrix — perempuan, tenang | 0.82x |
| `airia` | Airia — perempuan, lembut | 0.82x |
| `toktok` | Live Toktok — perempuan, ceria | 0.82x |
| `japangirl` | Japan girl — perempuan, imut | 0.82x |
| `egirl` | E-Girl — perempuan, playful | 0.82x |
| `venti` | Venti — perempuan, ringan | 0.82x |
| `raiden` | Raiden Shogun — perempuan, dalam | 0.80x |
| `kdm` | Kang Dedi — laki-laki, ekspresif | 0.85x |
| `prabowo` | Prabowo — laki-laki, dalam | 0.80x |
| `gadis` | Gadis — edge-tts (tanpa Fish) | 0.85x |

Ganti dari UI: **Settings -> Voice**. Semua suara Fish butuh `FISH_API_KEY`.

## Wake word "Hei Kai"

**Settings -> Listening -> Wake word**. Bilang "Hei Kai" / "Hai Kai" / "Kai" untuk
mulai bicara tanpa menyentuh HP. Syarat: Chrome, tab di depan, mic diizinkan.
Setting tersimpan, jadi setelah reload otomatis nyala lagi. Otomatis berhenti saat
mic sedang dipakai dan nyala lagi setelah jawaban selesai.
"""

if "## Suara (Fish Audio)" not in t:
    if "## Memori" in t:
        t = t.replace("## Memori", blok + "\n## Memori", 1)
    else:
        t = t + "\n" + blok
    p.write_text(t)

print("README diperbarui:", "## Suara (Fish Audio)" in p.read_text())
