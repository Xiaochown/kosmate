import asyncio
import sys

sys.path.insert(0, "/root/kosmate")

from kos import sing, tts, voices  # noqa: E402


async def cek():
    print("voice aktif:", voices.active())
    print("ref:", sing._ref())
    for teks in ("ba", "lon", "ku"):
        try:
            n = 0
            async for c in tts._fish(teks, speed=1.0, ref=sing._ref()):
                n += len(c)
            print(f"  {teks!r}: {n} byte")
        except Exception as e:  # noqa: BLE001
            print(f"  {teks!r}: GAGAL {type(e).__name__}: {str(e)[:160]}")


asyncio.run(cek())
