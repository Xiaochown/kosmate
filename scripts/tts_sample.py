import asyncio
import sys

sys.path.insert(0, "/root/kosmate")
from kos import memory, tts  # noqa: E402

memory.init()
print("ctx 'suka kopi':", repr(memory.context_block("suka kopi")))
print("ctx 'kapan ujian':", repr(memory.context_block("kapan ujian logika")))


async def main() -> None:
    chunks = []
    async for c in tts.synth_stream(
        "Halo Faa, gue Kai. Udah makan belum? Kalau belum, gih makan dulu sebelum ngoding."
    ):
        chunks.append(c)
    data = b"".join(chunks)
    with open("/root/kosmate/data/sample_voice.mp3", "wb") as fh:
        fh.write(data)
    print("bytes:", len(data), "head:", data[:4])


asyncio.run(main())
