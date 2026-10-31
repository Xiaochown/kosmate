import asyncio
import sys

sys.path.insert(0, "/root/kosmate")


async def main() -> None:
    import edge_tts

    voices = await edge_tts.list_voices()
    id_voices = [v for v in voices if str(v.get("Locale", "")).lower().startswith("id-")]
    print(f"total voice: {len(voices)} | Indonesia: {len(id_voices)}")
    for v in id_voices:
        print(
            f"  {v['ShortName']:28s} gender={v.get('Gender','?'):6s} "
            f"locale={v.get('Locale','?'):8s} {v.get('FriendlyName','')[:60]}"
        )


asyncio.run(main())
