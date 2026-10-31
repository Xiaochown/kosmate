import asyncio
import sys

sys.path.insert(0, "/root/kosmate")
from kos import memory  # noqa: E402
from kos.llm import complete  # noqa: E402

CONV = """User: inget ya, gue alergi kacang, tiap Senin jam 8 pagi ada ujian logika informatika di gedung C, dan gue lagi belajar jaringan pakai packet tracer
Kai: Iya, gue inget."""


async def main() -> None:
    memory.init()
    prompt = memory.EXTRACT_PROMPT.replace("{conversation}", CONV)
    raw = await complete([{"role": "user", "content": prompt}], temperature=0.0, max_tokens=500)
    print("RAW:", raw[:600])
    facts = memory.parse_facts_json(raw)
    print("PARSED:", facts)
    for f in facts:
        fid = memory.add_fact(f["subject"], f["predicate"], f["object"], f["confidence"])
        print("  insert id:", fid)
    print("STATS:", memory.stats())


asyncio.run(main())
