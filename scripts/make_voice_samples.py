import asyncio
import sys
from pathlib import Path

import edge_tts

OUT = Path("/root/kosmate/data/samples")
OUT.mkdir(parents=True, exist_ok=True)

TEKS = (
    "Halo Faa, gue Kai. Hari ini gimana? Kalau capek, "
    "kita santai dulu aja. Gue temenin sampai lu siap lagi."
)

VARIAN = [
    ("1_normal", "+0%", "+0Hz"),
    ("2_pelan", "-12%", "-2Hz"),
    ("3_pelan_halus", "-20%", "-4Hz"),
]


async def main() -> None:
    for name, rate, pitch in VARIAN:
        comm = edge_tts.Communicate(TEKS, "id-ID-GadisNeural", rate=rate, pitch=pitch)
        buf = bytearray()
        async for ch in comm.stream():
            if ch.get("type") == "audio" and ch.get("data"):
                buf.extend(ch["data"])
        p = OUT / f"gadis_{name}.mp3"
        p.write_bytes(bytes(buf))
        print(f"{p.name:24s} rate={rate:6s} pitch={pitch:5s} {len(buf)} byte")


asyncio.run(main())
