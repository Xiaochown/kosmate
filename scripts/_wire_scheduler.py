"""Sambungkan scheduler + endpoint /api/announce + migrasi DB ke app.py."""
import pathlib

p = pathlib.Path("/root/kosmate/kos/app.py")
s = p.read_text()

# 1) import
if "from . import scheduler" not in s:
    s = s.replace(
        "from . import extras, memory, persona, pin, stt, tts, voices",
        "from . import extras, memory, migrate, persona, pin, scheduler, stt, tts, voices",
    )

# 2) lifespan: migrasi dulu, lalu nyalakan penjadwal
if "scheduler.mulai()" not in s:
    s = s.replace(
        """async def lifespan(app):
    memory.init()
    extras.init()""",
        """async def lifespan(app):
    migrate.jalankan()      # migrasi berversi + backup sebelum ubah skema
    memory.init()
    extras.init()
    scheduler.mulai()       # pengingat jalan walau Chrome ditutup""",
    )
    s = s.replace(
        """    print(f"[kosmate] db={CFG.db_path} llm={CFG.llm_model} tts={CFG.tts_provider}")
    yield""",
        """    print(f"[kosmate] db={CFG.db_path} llm={CFG.llm_model} tts={CFG.tts_provider}")
    try:
        yield
    finally:
        await scheduler.berhenti()""",
    )

# 3) endpoint antrean ucapan
if "/api/announce" not in s:
    s = s.replace(
        "# ---------------------- pengingat, jurnal, kuota, catatan ----------------------",
        '''# ---------------------- antrean ucapan dari server ----------------------
async def announce_pending(request: Request):
    """Klien memanggil ini saat aktif: kalimat yang tertinggal saat Chrome mati."""
    return JSONResponse({"items": extras.ambil_announce()})


# ---------------------- pengingat, jurnal, kuota, catatan ----------------------''',
    )
    s = s.replace(
        '    Route("/api/reminders", reminders_list, methods=["GET"]),',
        '    Route("/api/announce", announce_pending),\n    Route("/api/reminders", reminders_list, methods=["GET"]),',
    )

p.write_text(s)

import ast
ast.parse(s)
print("scheduler:", "scheduler.mulai()" in s)
print("route:", '"/api/announce"' in s)
print("migrate:", "migrate.jalankan()" in s)
