"""Uji lanjut-otomatis saat jawaban kena batas token (tanpa manggil LLM beneran).

pakai: python scripts/test_continue.py
"""
import json
import sys

sys.path.insert(0, ".")

import kos.app as A  # noqa: E402

calls = {"n": 0}


async def fake_stream(messages, model=None, temperature=0.75, max_tokens=None, info=None):
    calls["n"] += 1
    if calls["n"] <= 2:
        if info is not None:
            info["finish_reason"] = "length"   # seolah-olah kehabisan token
        for w in ("Saudara-saudara sebangsa ", "dan setanah air "):
            yield w
    else:
        if info is not None:
            info["finish_reason"] = "stop"
        yield "kita semua bersatu."


async def _no_bg(*a, **k):
    return None


A.stream_chat = fake_stream
A.extract_facts_bg = _no_bg
A.pin.aktif = lambda: False  # matikan gerbang PIN khusus test ini (data/pin.txt tidak disentuh)

from starlette.testclient import TestClient  # noqa: E402

teks, done = "", {}
with TestClient(A.app) as c:
    with c.stream("POST", "/api/chat", json={"message": "bacain pidato", "session": "uji"}) as r:
        print("status:", r.status_code)
        for line in r.iter_lines():
            if line and not line.startswith("data:"):
                print("raw:", line[:120])
            if not line.startswith("data:"):
                continue
            evt = json.loads(line[5:].strip())
            if evt.get("type") == "delta":
                teks += evt["text"]
            elif evt.get("type") == "done":
                done = evt

print("panggilan LLM :", calls["n"], "(harus 3 = 1 awal + 2 lanjut)")
print("teks akhir    :", repr(teks))
print("truncated     :", done.get("truncated"), "(harus False karena lanjut sampai selesai)")
ok = calls["n"] == 3 and teks.endswith("kita semua bersatu.") and done.get("truncated") is False
print("\nHASIL:", "LOLOS" if ok else "GAGAL")
sys.exit(0 if ok else 1)
