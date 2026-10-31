import pathlib

p = pathlib.Path("/root/kosmate/kos/tts.py")
t = p.read_text()
t = t.replace("from . import voices", "from . import settings, voices")
t = t.replace("    timeout = httpx.Timeout(60.0, connect=15.0, read=60.0)",
              "    timeout = httpx.Timeout(60.0, connect=15.0, read=float(settings.get(\"tts_timeout\")))")
t = t.replace("    return t[:4000]", "    return t[: int(settings.get(\"tts_max_chars\"))]")
p.write_text(t)
print("tts:", 'settings.get("tts_timeout")' in t, "| cap:", "tts_max_chars" in t)

a = pathlib.Path("/root/kosmate/kos/app.py")
s = a.read_text()
s = s.replace("from . import memory, persona, pin, stt, tts, voices",
              "from . import memory, persona, pin, stt, tts, voices\nfrom . import settings as setelan")
s = s.replace("def _history(session: str, limit: int = 8) -> list[dict]:",
              "def _history(session: str, limit: int | None = None) -> list[dict]:")
s = s.replace("    mem_block = memory.context_block(message)",
              "    mem_block = memory.context_block(message, max_chars=setelan.get(\"memory_chars\"))")
s = s.replace("+ _history(session)", "+ _history(session, int(setelan.get(\"history_messages\")))")
a.write_text(s)
print("app setelan refs:", s.count("setelan.get"))
print("history limit:", "int(setelan.get(\"history_messages\"))" in s)
