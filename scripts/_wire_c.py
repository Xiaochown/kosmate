"""Sambungkan metrik + briefing pagi ke app.py."""
import pathlib

p = pathlib.Path("/root/kosmate/kos/app.py")
s = p.read_text()

# import
if "from . import metrics" not in s:
    s = s.replace(
        "from . import auth, extras, memory, migrate, persona, pin, scheduler, stt, tts, voices",
        "from . import auth, extras, memory, metrics, migrate, persona, pin, scheduler, stt, tts, voices",
    )

# endpoint: metrik + briefing
if "async def laporan_metrik" not in s:
    s = s.replace(
        "# ---------------------- token device ----------------------",
        '''# ---------------------- metrik & briefing ----------------------
async def laporan_metrik(request: Request):
    """Angka nyata per komponen: dari sini ketahuan 'suara kepotong' itu salah siapa."""
    return JSONResponse(metrics.laporan())


async def briefing_pagi(request: Request):
    """Ringkasan singkat: jurnal terakhir + pengingat hari ini.

    Sengaja TIDAK mengarang jadwal kuliah — app tidak punya data kalender.
    """
    jurnal = extras.daftar_jurnal()[:1]
    hari_ini = time.strftime("%Y-%m-%d")
    pengingat = [
        r for r in extras.daftar_reminder()
        if not r.get("done") and time.strftime("%Y-%m-%d", time.localtime(r.get("due_ts", 0))) == hari_ini
    ]
    bagian = []
    if jurnal:
        bagian.append("Jurnal terakhir: " + jurnal[0].get("teks", "")[:400])
    if pengingat:
        jam = [time.strftime("%H:%M", time.localtime(r["due_ts"])) + " " + r["teks"] for r in pengingat[:5]]
        bagian.append("Pengingat hari ini: " + "; ".join(jam))
    if not bagian:
        return JSONResponse({"ada": False, "teks": ""})
    return JSONResponse({"ada": True, "teks": "Selamat pagi. " + " ".join(bagian)})


# ---------------------- token device ----------------------''',
    )
    s = s.replace(
        '    Route("/api/tokens", tokens_list),',
        '''    Route("/api/metrics", laporan_metrik),
    Route("/api/briefing", briefing_pagi),
    Route("/api/tokens", tokens_list),''',
    )

# metrik di jalur chat: bungkus waktu total & first token
if "metrics.ukur(" not in s:
    s = s.replace(
        "    async def _gen():\n        nonlocal last_text",
        "    async def _gen():\n        nonlocal last_text\n        _t0 = time.perf_counter()\n        _first = [True]",
    )

p.write_text(s)
import ast
ast.parse(s)
print("metrics endpoint:", "laporan_metrik" in s, "| briefing:", "briefing_pagi" in s)
