import pathlib

# 1) persona: mode "cerita" (bedtime story)
p = pathlib.Path("/root/kosmate/kos/persona.py")
t = p.read_text()
if '"cerita"' not in t:
    t = t.replace(
        '    "kerja": "MODE AKTIF: ASISTEN KERJA. Prioritas langkah konkret dan deadline.",',
        '    "kerja": "MODE AKTIF: ASISTEN KERJA. Prioritas langkah konkret dan deadline.",\n'
        '    "cerita": (\n'
        '        "MODE AKTIF: PENCERITA (pengantar tidur). Tugasmu membacakan cerita panjang yang menenangkan.\\n"\n'
        '        "- Tulis cerita utuh dan panjang (minimal 1500 kata), mengalir, tanpa bertanya balik.\\n"\n'
        '        "- Kalimat pendek-pendek, tempo tenang, deskripsi lembut, hindari konflik menegangkan atau cliffhanger.\\n"\n'
        '        "- Tanpa judul berformat markdown, tanpa bullet, tanpa emoji, tanpa tanda kurung.\\n"\n'
        '        "- Akhiri dengan kalimat yang menenangkan dan mengajak tidur."\n'
        '    ),'
    )
    # tambahkan ke daftar peran
    t = t.replace("3. ASISTEN KERJA",
                  "3. ASISTEN KERJA")
    p.write_text(t)
    print("persona: mode cerita ditambahkan")
else:
    print("persona: mode cerita sudah ada")

# 2) app.py: endpoint /api/settings + route
a = pathlib.Path("/root/kosmate/kos/app.py")
s = a.read_text()
if "/api/settings" not in s:
    s = s.replace(
        "async def export_memory(request: Request):",
        '''async def get_settings(request: Request):
    return JSONResponse(setelan.skema())


async def post_settings(request: Request):
    body = await request.json()
    if body.get("preset"):
        try:
            val = setelan.preset(str(body["preset"]))
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
    else:
        val = setelan.save(body.get("values") or body)
    print("[settings]", {k: val[k] for k in ("max_tokens", "temperature", "chunk_chars", "tts_parallel")})
    return JSONResponse({"values": val, "spec": setelan.SPEK})


async def export_memory(request: Request):'''
    )
    s = s.replace('    Route("/api/voice", get_voice),',
                  '    Route("/api/settings", get_settings),\n    Route("/api/settings", post_settings, methods=["POST"]),\n    Route("/api/voice", get_voice),')
    a.write_text(s)
    print("app: endpoint /api/settings ditambahkan")
else:
    print("app: /api/settings sudah ada")
