"""Smoke test Kosmate tanpa curl (urllib)."""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8080"


def req(method: str, path: str, body=None, raw: bool = False):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={"content-type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(r, timeout=90) as resp:
            payload = resp.read()
            return resp.status, (payload if raw else payload.decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:160]
    except Exception as e:  # noqa: BLE001
        return 0, f"{type(e).__name__}: {e}"


CEK = [
    ("GET", "/", None, "html"),
    ("GET", "/api/health", None, "json"),
    ("GET", "/api/voice", None, "json"),
    ("POST", "/api/voice", {"key": "miyaa"}, "json"),
    ("GET", "/api/memory/stats", None, "json"),
    ("GET", "/api/memory/context", None, "json"),
    ("GET", "/api/memory/facts?limit=5", None, "json"),
    ("GET", "/api/export", None, "json"),
    ("POST", "/api/mode", {"mode": "temen"}, "json"),
    ("POST", "/api/greeting", None, "json"),
    ("POST", "/api/tts", {"text": "tes suara"}, "audio"),
]

lolos = gagal = 0
for method, path, body, kind in CEK:
    st, out = req(method, path, body, raw=(kind == "audio"))
    ok = 200 <= st < 300
    if ok and kind == "json":
        try:
            json.loads(out)
        except Exception:
            ok = False
    if ok and kind == "audio":
        ok = len(out) > 2000
    print(("  [ok]  " if ok else "  [!!]  ") + f"{method:5s} {path:34s} {st} {len(out) if out else 0}b")
    lolos, gagal = (lolos + 1, gagal) if ok else (lolos, gagal + 1)

print(f"\nhasil: {lolos} lolos, {gagal} gagal")
