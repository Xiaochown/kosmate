import asyncio
import sys
import time

sys.path.insert(0, "/root/kosmate")
from kos import tts  # noqa: E402


async def one(i: int) -> None:
    t0 = time.time()
    total = 0
    try:
        async for chunk in tts.synth_stream(f"Tes suara nomor {i}. Ini kalimat uji coba."):
            total += len(chunk)
        dt = time.time() - t0
        print(f"  #{i}: OK   {total:6d} byte  {dt:.2f}s")
    except Exception as e:  # noqa: BLE001
        dt = time.time() - t0
        print(f"  #{i}: GAGAL {dt:.2f}s -> {type(e).__name__}: {str(e)[:180]}")


async def main() -> None:
    print("provider:", tts._providers())
    for i in range(1, 7):
        await one(i)


asyncio.run(main())
