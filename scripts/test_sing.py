"""Tes mode nyanyi: pemenggalan suku kata + sintesis audio nyata."""
import asyncio
import sys

sys.path.insert(0, "/root/kosmate")

from kos import sing  # noqa: E402

print("--- 1. pemenggalan suku kata ---")
for kata in ("pelangi", "balonku", "alangkah", "indahmu", "kupu", "senja", "rumah"):
    print(f"  {kata:10s} -> {sing.pecah_suku(kata)}")

print("\n--- 2. lirik -> suku ---")
lirik = "pelangi pelangi alangkah indahmu"
suku = sing.lirik_ke_suku(lirik)
print("  lirik:", lirik)
print("  suku :", [s for s, _ in suku])
print("  jumlah:", len(suku))

print("\n--- 3. sintesis nyata (4 suku kata, lagu balon) ---")
teks = "balonku ada"
try:
    audio = asyncio.run(sing.nyanyi(teks, lagu="balon"))
    print(f"  hasil: {len(audio)} byte ({len(audio)//1024} KB)")
    open("/tmp/nyanyi.ogg", "wb").write(b"")  # placeholder
    open("/tmp/nyanyi.mp3", "wb").write(audio)
    print("  disimpan: /tmp/nyanyi.mp3")
    print("  durasi perkiraan:", round(len(audio) * 8 / 128000, 1), "detik")
except Exception as e:  # noqa: BLE001
    print("  GAGAL:", type(e).__name__, str(e)[:200])

print("\n--- 4. lagu tersedia ---")
for l in sing.daftar_lagu():
    print(f"  {l['kunci']:10s} {l['judul']:38s} bpm {l['bpm']} · {l['not']} not")
