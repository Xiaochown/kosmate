import pathlib

a = pathlib.Path("/root/kosmate/kos/app.py")
s = a.read_text()

# mode "cerita" + persist ke data/mode.txt
if "cerita" not in s:
    s = s.replace(
        '''async def set_mode(request: Request):
    b = await request.json()
    mode = (b.get("mode") or "temen").lower()
    if mode not in ("temen", "tutor", "kerja"):
        raise HTTPException(400, "mode: temen|tutor|kerja")
    CFG.persona_mode = mode
    return JSONResponse({"mode": mode})''',
        '''MODE_FILE = CFG.data_dir / "mode.txt"
MODE_SAH = ("temen", "tutor", "kerja", "cerita")


def _baca_mode() -> str:
    try:
        m = MODE_FILE.read_text(encoding="utf-8").strip()
        return m if m in MODE_SAH else "temen"
    except Exception:  # noqa: BLE001
        return "temen"


async def set_mode(request: Request):
    b = await request.json()
    mode = (b.get("mode") or "temen").lower()
    if mode not in MODE_SAH:
        raise HTTPException(400, "mode: " + "|".join(MODE_SAH))
    CFG.persona_mode = mode
    try:
        MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
        MODE_FILE.write_text(mode + "\\n", encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    return JSONResponse({"mode": mode})''')

# baca mode tersimpan saat startup
s = s.replace(
    "app = Starlette(routes=routes, lifespan=lifespan, exception_handlers={HTTPException: not_found})",
    'CFG.persona_mode = _baca_mode()\n\napp = Starlette(routes=routes, lifespan=lifespan, exception_handlers={HTTPException: not_found})',
)
a.write_text(s)
print("mode cerita:", "MODE_SAH" in s, "| persist:", "_baca_mode()" in s)
