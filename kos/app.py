"""KOSMATE server — Starlette (TANPA pydantic/FastAPI).

Kenapa bukan FastAPI: pydantic v2 butuh `pydantic-core` yang ditulis Rust.
Di Termux + Python 3.14 belum ada wheel-nya, dan rustup gak kenal target
`aarch64-unknown-linux-android` -> instalasi pasti gagal di HP.
Starlette murni Python, semua yang kita butuh (routing, SSE, upload, static)
sudah ada di sana.

Jalankan: python -m uvicorn kos.app:app
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from . import memory, persona, stt, tts, voices
from .config import CFG, ROOT
from .llm import complete, stream_chat

WEB_DIR = ROOT / "web"
FACT_WORDS = ("inget", "ingat", "catat", "note", "jangan lupa", "besok", "deadline")
LAST_TTS_ERROR = ""
LAST_TTS_OK = ""


@asynccontextmanager
async def lifespan(app):
    memory.init()
    print(f"[kosmate] db={CFG.db_path} llm={CFG.llm_model} tts={CFG.tts_provider}")
    yield


# ------------------------------------------------------------------ helpers
def _sse(obj: dict) -> str:
    return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"


async def extract_facts_bg(conversation: str, source_ep: int | None = None) -> None:
    """Ambil fakta baru dari obrolan, simpan ke DB. Jalan di background."""
    try:
        prompt = memory.EXTRACT_PROMPT.replace("{conversation}", conversation[-2500:])
        raw = await complete(
            [{"role": "user", "content": prompt}], temperature=0.0, max_tokens=400
        )
        for f in memory.parse_facts_json(raw):
            memory.add_fact(f["subject"], f["predicate"], f["object"], f["confidence"], source_ep)
    except Exception as e:  # noqa: BLE001
        print("[memory] ekstraksi gagal:", e)


def _history(session: str, limit: int = 8) -> list[dict]:
    out: list[dict] = []
    for ep in memory.recent(limit=limit, session=session):
        role = "assistant" if ep["role"] != "user" else "user"
        out.append({"role": role, "content": ep["text"]})
    return out


# -------------------------------------------------------------------- routes
async def health(request: Request):
    return JSONResponse(
        {
            "ok": True,
            "name": CFG.assistant_name,
            "llm": CFG.llm_model,
            "llm_key": bool(CFG.llm_key),
            "tts_providers": tts._providers(),
            "fish_key": bool(CFG.fish_key),
            "stt": CFG.stt_provider,
            "mode": CFG.persona_mode,
            "tts_last_ok": LAST_TTS_OK,
            "tts_last_error": LAST_TTS_ERROR,
            "tts_voice": CFG.tts_voice,
            "tts_rate": CFG.tts_rate,
            "tts_strict": CFG.tts_strict,
            "voice": voices.active(),
            "fish_ref": bool(CFG.fish_ref),
            "fish_model": CFG.fish_model if CFG.fish_key else "",
            "memory": memory.stats(),
            "time": time.time(),
        }
    )


async def chat(request: Request):
    body = await request.json()
    message = (body.get("message") or "").strip()
    session = body.get("session") or "default"
    if not message:
        raise HTTPException(400, "message kosong")

    ep_id = memory.add_episode("user", message, session)
    mem_block = memory.context_block(message)
    messages = [{"role": "system", "content": persona.build_system(mem_block)}] + _history(session)

    async def gen():
        buf: list[str] = []
        yield _sse({"type": "start"})
        try:
            async for delta in stream_chat(messages):
                buf.append(delta)
                yield _sse({"type": "delta", "text": delta})
        except Exception as e:  # noqa: BLE001
            msg = f"Otak gue lagi gangguan: {e}"
            yield _sse({"type": "error", "text": msg})
            yield _sse({"type": "done", "text": msg, "memory": memory.stats()})
            return
        full = "".join(buf).strip()
        if not full:
            full = "Hmm, gue kosong. Coba ulang pertanyaannya."
            yield _sse({"type": "delta", "text": full})
        memory.add_episode("assistant", full, session)
        yield _sse({"type": "done", "text": full, "memory": memory.stats()})

        conv = f"User: {message}\n{CFG.assistant_name}: {full}"
        should = any(w in message.lower() for w in FACT_WORDS) or memory.stats()["episodes"] % 4 == 0
        if should:
            asyncio.create_task(extract_facts_bg(conv, ep_id))

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def synth(request: Request):
    global LAST_TTS_ERROR, LAST_TTS_OK
    body = await request.json()
    text = (body.get("text") or "").strip()
    voice = (body.get("voice") or "").strip() or None
    rate = (body.get("rate") or "").strip() or None
    if rate and not re.fullmatch(r"[+-]?\d{1,2}%", rate):
        rate = None
    if not text:
        raise HTTPException(400, "text kosong")
    v = voices.active()
    if v.get("engine") == "fish" and not CFG.fish_key:
        raise HTTPException(
            503,
            "FISH_API_KEY belum diisi di .env — voice " + v["key"] + " belum bisa dipakai",
        )
    return StreamingResponse(
        _tts_guard(tts.synth_stream(text, voice=voice, rate=rate)),
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _tts_guard(agen):
    """Catat error TTS terakhir biar kelihatan di /api/health (buat diagnosa)."""
    global LAST_TTS_ERROR, LAST_TTS_OK
    n = 0
    try:
        async for chunk in agen:
            n += len(chunk)
            yield chunk
    except Exception as e:  # noqa: BLE001
        LAST_TTS_ERROR = f"{type(e).__name__}: {e}"[:300]
        print("[tts] gagal:", LAST_TTS_ERROR)
        raise
    else:
        if n:
            LAST_TTS_ERROR = ""
            LAST_TTS_OK = f"{n} byte"
        else:
            LAST_TTS_ERROR = "audio kosong"
            print("[tts] audio kosong")


async def greeting(request: Request):
    """Sapaan proaktif saat app dibuka / setelah lama idle."""
    hint = persona.greeting_hint()
    mem = memory.context_block("")
    sys = persona.build_system(mem)
    try:
        text = await complete(
            [
                {"role": "system", "content": sys},
                {
                    "role": "user",
                    "content": f"[SISTEM] {hint} Maksimal 2 kalimat, langsung bicara, jangan pakai nama sendiri.",
                },
            ],
            temperature=0.85,
            max_tokens=120,
        )
    except Exception as e:  # noqa: BLE001
        text = f"Halo {CFG.user_name}, gue di sini. Ada apa?"
        print("[greeting] gagal:", e)
    from datetime import datetime

    return JSONResponse({"text": text, "part_of_day": persona.part_of_day(datetime.now().hour)})


async def transcribe(request: Request):
    form = await request.form()
    audio = form.get("audio")
    if not isinstance(audio, UploadFile):
        raise HTTPException(400, "file 'audio' gak ada")
    data = await audio.read()
    if len(data) < 800:
        return JSONResponse({"text": ""})
    txt = await stt.transcribe(data, audio.filename or "audio.m4a")
    return JSONResponse({"text": txt})


async def mem_stats(request: Request):
    return JSONResponse(memory.stats())


async def mem_context(request: Request):
    return JSONResponse({"context": memory.context_block(request.query_params.get("q", ""))})


async def mem_facts(request: Request):
    limit = int(request.query_params.get("limit", "200"))
    return JSONResponse({"facts": memory.list_facts(limit=limit)})


async def add_mem_fact(request: Request):
    b = await request.json()
    fid = memory.add_fact(
        b.get("subject", "user"),
        b.get("predicate", ""),
        b.get("object", ""),
        float(b.get("confidence", 0.9)),
    )
    return JSONResponse({"id": fid, "ok": fid is not None})


async def del_mem_fact(request: Request):
    fid = int(request.path_params["fid"])
    return JSONResponse({"ok": memory.delete_fact(fid)})


async def mem_search(request: Request):
    q = request.query_params.get("q", "")
    return JSONResponse({"episodes": memory.search_episodes(q), "facts": memory.search_facts(q)})


async def add_note(request: Request):
    b = await request.json()
    nid = memory.add_note(b.get("text", ""), b.get("kind", "note"), int(b.get("pinned", 0)))
    return JSONResponse({"id": nid})


async def get_notes(request: Request):
    pinned = request.query_params.get("pinned", "0") not in ("0", "", "false")
    return JSONResponse({"notes": memory.list_notes(pinned_only=pinned)})


async def set_mode(request: Request):
    b = await request.json()
    mode = (b.get("mode") or "temen").lower()
    if mode not in ("temen", "tutor", "kerja"):
        raise HTTPException(400, "mode: temen|tutor|kerja")
    CFG.persona_mode = mode
    return JSONResponse({"mode": mode})


async def get_voice(request: Request):
    return JSONResponse(
        {
            "active": voices.active(),
            "options": voices.available(),
            "fish_key": bool(CFG.fish_key),
            "fish_model": CFG.fish_model,
        }
    )


async def set_voice(request: Request):
    body = await request.json()
    key = (body.get("key") or "").strip().lower()
    try:
        v = voices.set_active(key)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    print(f"[voice] aktif: {v['key']} ({v['engine']}) ref={v['ref'] or '-'} rate={v['rate']}")
    return JSONResponse({"active": v, "options": voices.available()})


async def export_memory(request: Request):
    return JSONResponse(memory.export_all())


async def not_found(request: Request, exc):
    return JSONResponse({"error": str(exc.detail), "status": exc.status_code}, status_code=exc.status_code)


routes = [
    Route("/api/health", health),
    Route("/api/chat", chat, methods=["POST"]),
    Route("/api/tts", synth, methods=["POST"]),
    Route("/api/greeting", greeting, methods=["POST"]),
    Route("/api/stt", transcribe, methods=["POST"]),
    Route("/api/mode", set_mode, methods=["POST"]),
    Route("/api/voice", get_voice),
    Route("/api/voice", set_voice, methods=["POST"]),
    Route("/api/export", export_memory),
    Route("/api/memory/stats", mem_stats),
    Route("/api/memory/context", mem_context),
    Route("/api/memory/search", mem_search),
    Route("/api/memory/facts", mem_facts),
    Route("/api/memory/facts", add_mem_fact, methods=["POST"]),
    Route("/api/memory/facts/{fid:int}", del_mem_fact, methods=["DELETE"]),
    Route("/api/memory/notes", get_notes),
    Route("/api/memory/notes", add_note, methods=["POST"]),
    Mount("/", app=StaticFiles(directory=str(WEB_DIR), html=True), name="web"),
]

app = Starlette(routes=routes, lifespan=lifespan, exception_handlers={HTTPException: not_found})
