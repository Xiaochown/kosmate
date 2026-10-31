"""Client LLM OpenAI-compatible — streaming, provider-agnostic.

Tahan banting terhadap provider murahan/aneh:
- SSE (text/event-stream) dan NDJSON
- provider yang balas JSON penuh walau diminta stream
- provider yang bungkus payload jadi {"data": {...}}
- content berupa string ATAU list of parts
- fallback otomatis ke model kedua kalau model pertama 4xx/5xx
"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx

from .config import CFG

_HEADERS = lambda: {
    "Authorization": f"Bearer {CFG.llm_key}",
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
}


def _unwrap(obj: Any) -> Any:
    """Provider seperti ldrcloud membungkus respons: {"data": {...}}."""
    if isinstance(obj, dict) and "choices" not in obj and isinstance(obj.get("data"), dict):
        return obj["data"]
    return obj


def _content_of(node: dict) -> str:
    c = node.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        out = []
        for part in c:
            if isinstance(part, dict):
                out.append(part.get("text") or part.get("content") or "")
            elif isinstance(part, str):
                out.append(part)
        return "".join(out)
    if isinstance(node.get("text"), str):
        return node["text"]
    return ""


def _delta(obj: Any) -> str:
    obj = _unwrap(obj)
    if not isinstance(obj, dict):
        return ""
    for ch in obj.get("choices") or []:
        if not isinstance(ch, dict):
            continue
        for key in ("delta", "message"):
            node = ch.get(key)
            if isinstance(node, dict):
                txt = _content_of(node)
                if txt:
                    return txt
        txt = _content_of(ch)
        if txt:
            return txt
    # beberapa provider taruh teks di root
    return _content_of(obj) if "choices" not in obj else ""


async def _request(messages: list[dict], model: str, temperature: float,
                   max_tokens: int, stream: bool, info: dict | None = None) -> AsyncIterator[str]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    url = f"{CFG.llm_base}/chat/completions"
    timeout = httpx.Timeout(60.0, connect=15.0, read=90.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        if not stream:
            r = await client.post(url, json=payload, headers=_HEADERS())
            r.raise_for_status()
            txt = _delta(r.json())
            if txt:
                yield txt
            return
        async with client.stream("POST", url, json=payload, headers=_HEADERS()) as r:
            if r.status_code >= 400:
                body = (await r.aread()).decode("utf-8", "ignore")[:400]
                raise RuntimeError(f"{r.status_code} {body}")
            ctype = (r.headers.get("content-type") or "").lower()
            textual = "event-stream" in ctype or "ndjson" in ctype or "text/plain" in ctype
            if not textual:
                raw = await r.aread()
                try:
                    yield _delta(json.loads(raw))
                except json.JSONDecodeError:
                    yield raw.decode("utf-8", "ignore")
                return
            async for line in r.aiter_lines():
                line = line.strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line in ("[DONE]", "DONE"):
                    return
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                txt = _delta(obj)
                if info is not None:
                    try:
                        fr = (obj.get("choices") or [{}])[0].get("finish_reason")
                        if fr:
                            info["finish_reason"] = fr
                    except Exception:  # noqa: BLE001
                        pass
                if txt:
                    yield txt


async def stream_chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.75,
    max_tokens: int | None = None,
    info: dict | None = None,
) -> AsyncIterator[str]:
    """Stream teks; fallback model kedua; fallback ke non-stream kalau perlu.

    `info` (opsional) diisi finish_reason supaya pemanggil tahu kalau jawaban
    kepotong gara-gara batas token, bukan karena modelnya berhenti.
    """
    mt = max_tokens or CFG.llm_max_tokens
    models = [model or CFG.llm_model]
    if CFG.llm_fallback and CFG.llm_fallback not in models:
        models.append(CFG.llm_fallback)

    last_err: Exception | None = None
    for m in models:
        got = False
        try:
            async for chunk in _request(messages, m, temperature, mt, True, info):
                got = True
                yield chunk
            if got:
                return
        except Exception as e:  # noqa: BLE001
            last_err = e
        if not got:
            try:
                async for chunk in _request(messages, m, temperature, mt, False, info):
                    yield chunk
                return
            except Exception as e:  # noqa: BLE001
                last_err = e
    raise RuntimeError(f"semua model gagal: {last_err}")


async def complete(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 500,
) -> str:
    buf: list[str] = []
    async for chunk in stream_chat(messages, model=model, temperature=temperature, max_tokens=max_tokens):
        buf.append(chunk)
    return "".join(buf).strip()


async def main_test() -> None:
    msgs = [
        {"role": "system", "content": "Jawab satu kalimat pendek, bahasa Indonesia santai."},
        {"role": "user", "content": "tes koneksi, bilang 'nyambung' kalau lu denger gue"},
    ]
    print(await complete(msgs))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main_test())
