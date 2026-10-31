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

from . import memory, persona, pin, stt, tts, voices
from . import settings as setelan
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


def _history(session: str, limit: int | None = None) -> list[dict]:
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


AKHIR_SAH = set('.!?…"\'”’)]}')


def _kepotong(t: str) -> bool:
    """True kalau teks berhenti tanpa tanda akhir kalimat (indikasi stream dipotong)."""
    t = (t or "").rstrip()
    if len(t) < 40:
        return False
    return t[-1] not in AKHIR_SAH


def _dedupe(prev: str, new: str) -> str:
    """Buang tumpang-tindih di awal lanjutan biar gak ada kata dobel."""
    tail = prev[-60:]
    for n in range(min(len(tail), len(new)), 3, -1):
        if tail.endswith(new[:n]):
            return new[n:]
    return new


async def chat(request: Request):
    body = await request.json()
    message = (body.get("message") or "").strip()
    session = body.get("session") or "default"
    if not message:
        raise HTTPException(400, "message kosong")

    ep_id = memory.add_episode("user", message, session)
    mem_block = memory.context_block(message, max_chars=setelan.get("memory_chars"))
    messages = [{"role": "system", "content": persona.build_system(mem_block)}] + _history(session, int(setelan.get("history_messages")))

    async def gen():
        buf: list[str] = []
        info: dict = {}
        yield _sse({"type": "start"})
        try:
            async for delta in stream_chat(messages, info=info):
                buf.append(delta)
                yield _sse({"type": "delta", "text": delta})
            # target panjang untuk mode cerita (pengantar tidur)
            target = int(setelan.get("story_words")) if CFG.persona_mode == "cerita" else 0
            batas_lanjut = max(CFG.llm_continue_max, 8) if target else CFG.llm_continue_max
            lanjut = 0
            while lanjut < batas_lanjut and (
                info.get("finish_reason") == "length"
                or _kepotong("".join(buf))
                or (target and len("".join(buf).split()) < target)
            ):
                lanjut += 1
                print(f"[chat] lanjut #{lanjut}: finish={info.get('finish_reason')} kata={len(''.join(buf).split())} target={target}")
                sisa = max(0, target - len("".join(buf).split())) if target else 0
                arahan = (
                    f"Lanjutkan cerita tepat dari kalimat terakhir. Jangan ulangi, jangan beri pembuka. "
                    f"Tulis minimal {sisa} kata lagi dengan suasana tenang, lalu tutup cerita dengan penutup yang menenangkan."
                    if sisa > 100 else
                    "Lanjutkan tepat dari kata terakhir. Jangan ulangi kalimat sebelumnya, jangan beri pembuka baru."
                )
                cont = messages + [
                    {"role": "assistant", "content": "".join(buf)},
                    {"role": "user", "content": arahan},
                ]
                info.clear()
                pertama = True
                async for delta in stream_chat(cont, info=info):
                    if pertama:
                        pertama = False
                        delta = _dedupe("".join(buf), delta)
                        if not delta:
                            continue
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
        yield _sse({
            "type": "done",
            "text": full,
            "memory": memory.stats(),
            "truncated": info.get("finish_reason") == "length",
        })

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


MODE_FILE = CFG.data_dir / "mode.txt"
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
        MODE_FILE.write_text(mode + "\n", encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
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


async def get_settings(request: Request):
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
    Route("/api/settings", get_settings),
    Route("/api/settings", post_settings, methods=["POST"]),
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

CFG.persona_mode = _baca_mode()

app = Starlette(routes=routes, lifespan=lifespan, exception_handlers={HTTPException: not_found})


class PinGate:
    """Gerbang PIN untuk akses lewat tunnel publik.

    - lokal (127.0.0.1) selalu lolos, biar tetap gampang dipakai di HP sendiri
    - kalau data/pin.txt belum ada, gerbang mati total
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not pin.aktif():
            return await self.inner(scope, receive, send)

        client = (scope.get("client") or ("", 0))[0]
        if client in ("127.0.0.1", "::1", "localhost"):
            return await self.inner(scope, receive, send)

        from urllib.parse import parse_qs

        qs = parse_qs(scope.get("query_string", b"").decode("latin-1"))
        tebakan = (qs.get("pin") or [None])[0]
        cookie = dict(scope.get("headers") or []).get(b"cookie", b"").decode("latin-1")
        punya_cookie = ("kosmate_pin=" + pin.pin()) in cookie

        if pin.cocok(tebakan):
            if tebakan:
                await send({
                    "type": "http.response.start",
                    "status": 303,
                    "headers": [
                        (b"location", b"/"),
                        (b"set-cookie", f"kosmate_pin={pin.pin()}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000".encode()),
                    ],
                })
                await send({"type": "http.response.body", "body": b""})
                return
            return await self.inner(scope, receive, send)

        if punya_cookie:
            return await self.inner(scope, receive, send)

        body = pin.form("PIN salah, coba lagi" if tebakan else "").encode()
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"text/html; charset=utf-8"),
                (b"content-length", str(len(body)).encode()),
                (b"cache-control", b"no-store"),
            ],
        })
        await send({"type": "http.response.body", "body": body})


app = PinGate(app)
