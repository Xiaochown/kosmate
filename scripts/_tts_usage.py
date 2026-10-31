import pathlib

p = pathlib.Path("/root/kosmate/kos/app.py")
t = p.read_text()
if "catat_pakai(tts_chars" not in t:
    t = t.replace(
        "    return StreamingResponse(\n        _tts_guard(tts.synth_stream(text, voice=voice, rate=rate)),",
        "    extras.catat_pakai(tts_chars=len(text), tts_calls=1)\n"
        "    return StreamingResponse(\n        _tts_guard(tts.synth_stream(text, voice=voice, rate=rate)),",
    )
    p.write_text(t)
print("tts usage tercatat:", "catat_pakai(tts_chars" in p.read_text())
