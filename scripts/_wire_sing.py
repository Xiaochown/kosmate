"""Endpoint /api/sing + daftar lagu, lalu tes nyanyi beneran."""
import pathlib

p = pathlib.Path("/root/kosmate/kos/app.py")
s = p.read_text()

if "from . import sing" not in s:
    s = s.replace(
        "from . import auth, extras, memory, metrics, migrate, persona, pin, scheduler, stt, tts, voices",
        "from . import auth, extras, memory, metrics, migrate, persona, pin, scheduler, sing, stt, tts, voices",
    )

if "async def nyanyi_handler" not in s:
    s = s.replace(
        "# ---------------------- metrik & briefing ----------------------",
        '''# ---------------------- mode nyanyi ----------------------
async def daftar_lagu(request: Request):
    return JSONResponse({"items": sing.daftar_lagu()})


async def nyanyi_handler(request: Request):
    b = await request.json()
    lirik = (b.get("lirik") or "").strip()
    lagu = (b.get("lagu") or "pelangi").strip()
    bpm = b.get("bpm")
    nada = None
    if isinstance(b.get("nada"), list):
        try:
            nada = [(int(n[0]), float(n[1])) for n in b["nada"]]
        except Exception:  # noqa: BLE001
            nada = None
    if not lirik:
        raise HTTPException(400, "lirik kosong")
    try:
        with metrics.ukur("sing"):
            audio = await sing.nyanyi(lirik, lagu=lagu, nada_khusus=nada, bpm=bpm)
    except ValueError as e:
        raise HTTPException(400, str(e))
    extras.catat_pakai(tts_chars=len(lirik) * 2, tts_calls=1)
    return Response(audio, media_type="audio/mpeg",
                    headers={"Cache-Control": "no-store"})


# ---------------------- metrik & briefing ----------------------''',
    )
    s = s.replace(
        '    Route("/api/metrics", laporan_metrik),',
        '''    Route("/api/sing", nyanyi_handler, methods=["POST"]),
    Route("/api/sing/songs", daftar_lagu),
    Route("/api/metrics", laporan_metrik),''',
    )

# import Response
if "Response," not in s:
    s = s.replace("from starlette.responses import JSONResponse, StreamingResponse",
                  "from starlette.responses import JSONResponse, Response, StreamingResponse")

p.write_text(s)
import ast
ast.parse(s)
print("endpoint sing:", "nyanyi_handler" in s, "| Response import:", "Response," in s)
