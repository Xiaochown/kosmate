"""Tes 7 suara perempuan baru: sintesis nyata lewat _fish, laporkan byte."""
import asyncio
import sys

sys.path.insert(0, "/root/kosmate")

from kos import tts, voices  # noqa: E402

BARU = ["beatrix", "airia", "toktok", "japangirl", "egirl", "venti", "raiden"]
TEKS = "Halo, aku Kai. Malam ini aku temenin kamu ya."


async def main():
    for key in BARU:
        p = voices.PRESETS[key]
        speed = tts._rate_to_speed(p["rate"])
        total = 0
        try:
            async for chunk in tts._fish(TEKS, speed=speed, ref=p["ref"]):
                total += len(chunk)
            if total > 2000:
                print(f"  {key:10s} {p['label'][:26]:28s} {total:>7d} byte  OK")
            else:
                print(f"  {key:10s} {p['label'][:26]:28s} {total:>7d} byte  KECIL/ANEh")
        except Exception as e:  # noqa: BLE001
            print(f"  {key:10s} GAGAL: {type(e).__name__}: {str(e)[:110]}")


asyncio.run(main())
