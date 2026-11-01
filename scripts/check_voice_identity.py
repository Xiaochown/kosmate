"""Cek apakah Fish benar-benar memakai reference_id: bandingkan hash audio."""
import asyncio
import hashlib
import sys

sys.path.insert(0, "/root/kosmate")

from kos import tts, voices  # noqa: E402

TEKS = "Ini tes suara yang berbeda ya."
CEK = ["japangirl", "egirl", "beatrix", "airia", "toktok", "venti", "raiden"]


async def ambil(ref: str) -> tuple[int, str]:
    total = 0
    h = hashlib.md5()
    async for chunk in tts._fish(TEKS, speed=1.0, ref=ref):
        total += len(chunk)
        h.update(chunk)
    return total, h.hexdigest()[:12]


async def main():
    print("  tanpa ref (default fish) :", await ambil(""))
    for key in CEK:
        p = voices.PRESETS[key]
        total, hh = await ambil(p["ref"])
        print(f"  {key:10s} ref {p['ref'][:8]}…  {total:>7d} byte  hash {hh}")


asyncio.run(main())
