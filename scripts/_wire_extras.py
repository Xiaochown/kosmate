import pathlib

a = pathlib.Path("/root/kosmate/kos/app.py")
s = a.read_text()

BLOK = '''
# ---------------------- pengingat, jurnal, kuota, catatan ----------------------
async def reminders_list(request: Request):
    return JSONResponse({"items": extras.daftar_reminder()})


async def reminders_add(request: Request):
    b = await request.json()
    teks = (b.get("teks") or "").strip()
    if not teks:
        raise HTTPException(400, "teks kosong")
    due = b.get("due_ts")
    if not due:
        due = extras.parse_kapan(b.get("kapan") or "")
    if not due:
        raise HTTPException(400, "waktu tidak kebaca — pakai '10 menit', 'jam 5', 'besok jam 9', atau due_ts")
    return JSONResponse(extras.tambah_reminder(teks, int(due)))


async def reminders_del(request: Request):
    extras.hapus_reminder(int(request.path_params["rid"]))
    return JSONResponse({"ok": True})


async def reminders_due(request: Request):
    return JSONResponse({"items": extras.ambil_jatuh_tempo()})


async def usage_today(request: Request):
    pakai = extras.pakai_hari_ini()
    pakai["limits"] = {"max_tokens": setelan.get("max_tokens"), "tts_max_chars": setelan.get("tts_max_chars")}
    return JSONResponse(pakai)


async def journal_generate(request: Request):
    b = await request.json()
    pilih = (b.get("period") or "day").lower()
    eps = extras.episode_terakhir(120 if pilih == "week" else 60)
    if not eps:
        raise HTTPException(400, "belum ada obrolan buat diringkas")
    convo = "\\n".join(
        f"{'User' if e.get('role') == 'user' else CFG.assistant_name}: {str(e.get('text'))[:400]}" for e in eps
    )
    prompt = (
        "Ringkas obrolan berikut jadi jurnal pribadi 3-5 kalimat, sudut pandang orang pertama (gue), "
        "bahasa Indonesia santai, tanpa bullet, tanpa markdown. Sorot: apa yang dikerjakan, perasaan, "
        "dan satu hal buat besok.\\n\\n" + convo[-6000:]
    )
    teks = (await complete([{"role": "user", "content": prompt}], max_tokens=400, temperature=0.6) or "").strip()
    if not teks:
        raise HTTPException(502, "model tidak membalas")
    simpan = extras.simpan_jurnal(teks, pilih)
    try:
        folder = CFG.data_dir / "journal"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{simpan['hari']}.md").write_text(f"# Jurnal {simpan['hari']}\\n\\n{teks}\\n", encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    extras.catat_pakai(llm_tokens=700)
    return JSONResponse(simpan)


async def journal_list(request: Request):
    return JSONResponse({"items": extras.daftar_jurnal()})


async def notes_add(request: Request):
    ct = (request.headers.get("content-type") or "").lower()
    judul, teks = "catatan", ""
    if "multipart" in ct:
        form = await request.form()
        up = form.get("file")
        judul = (form.get("judul") or "").strip()
        if up is not None and hasattr(up, "read"):
            teks = (await up.read()).decode("utf-8", "ignore")
            judul = judul or getattr(up, "filename", "catatan")
    else:
        b = await request.json()
        judul = (b.get("judul") or "catatan").strip()
        teks = b.get("teks") or ""
    if len(teks.strip()) < 20:
        raise HTTPException(400, "teks terlalu pendek")
    return JSONResponse(extras.tambah_catatan(judul, teks))


async def notes_list(request: Request):
    return JSONResponse({"items": extras.daftar_catatan()})


async def notes_del(request: Request):
    extras.hapus_catatan(int(request.path_params["did"]))
    return JSONResponse({"ok": True})


async def import_memory(request: Request):
    b = await request.json()
    eps = b.get("episodes") or []
    fakta = b.get("facts") or []
    for e in eps:
        memory.add_episode(e.get("role", "user"), str(e.get("text", ""))[:2000], e.get("session", "impor"))
    for f in fakta:
        try:
            memory.add_fact(f.get("subject", "user"), f.get("predicate", ""), f.get("object", ""))
        except Exception:  # noqa: BLE001
            pass
    return JSONResponse({"ok": True, "episodes": len(eps), "facts": len(fakta)})


async def export_memory(request: Request):'''

s = s.replace("async def export_memory(request: Request):", BLOK.strip() + "\n", 1)

ROUTES = '''    Route("/api/reminders", reminders_list),
    Route("/api/reminders", reminders_add, methods=["POST"]),
    Route("/api/reminders/due", reminders_due),
    Route("/api/reminders/{rid:int}", reminders_del, methods=["DELETE"]),
    Route("/api/usage", usage_today),
    Route("/api/journal", journal_generate, methods=["POST"]),
    Route("/api/journal", journal_list),
    Route("/api/notes", notes_add, methods=["POST"]),
    Route("/api/notes", notes_list),
    Route("/api/notes/{did:int}", notes_del, methods=["DELETE"]),
    Route("/api/import", import_memory, methods=["POST"]),
'''
s = s.replace('    Route("/api/settings", get_settings),', ROUTES + '    Route("/api/settings", get_settings),')

# import extras + init di lifespan
s = s.replace("from . import memory, persona, pin, stt, tts, voices",
              "from . import extras, memory, persona, pin, stt, tts, voices")
s = s.replace("    memory.init()", "    memory.init()\n    extras.init()", 1)
if "extras.init()" not in s:
    # fallback: sisipkan setelah baris pertama di dalam lifespan
    s = s.replace("async def _lifespan", "async def _lifespan")

# RAG + kuota di chat
s = s.replace('    mem_block = memory.context_block(message, max_chars=setelan.get("memory_chars"))',
              '    mem_block = memory.context_block(message, max_chars=setelan.get("memory_chars"))\n'
              '    mem_block += extras.blok_catatan(message)')
s = s.replace('        memory.add_episode("assistant", full, session)',
              '        memory.add_episode("assistant", full, session)\n'
              '        extras.catat_pakai(llm_tokens=max(1, len(full) // 4))')

a.write_text(s)
print("extras.init:", "extras.init()" in s, "| routes:", s.count('Route("/api/reminders'), "| rag:", "blok_catatan" in s)
