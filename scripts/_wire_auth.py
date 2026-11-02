"""Sambungkan token per-device + rate limit ke PinGate."""
import pathlib
import re

p = pathlib.Path("/root/kosmate/kos/app.py")
s = p.read_text()

if "from . import auth" not in s and "import auth" not in s:
    s = s.replace(
        "from . import extras, memory, migrate, persona, pin, scheduler, stt, tts, voices",
        "from . import auth, extras, memory, migrate, persona, pin, scheduler, stt, tts, voices",
    )

baru = '''class PinGate:
    """Gerbang akses untuk request dari luar (tunnel).

    Urutan izin:
      1. lokal (127.0.0.1 / ::1) selalu lolos
      2. token device (header X-Kos-Token atau ?token=) -> dicatat "terakhir dipakai"
      3. cookie PIN (cara lama, tetap didukung)
    Plus rate limit per IP supaya satu device nakal tidak menghabiskan kuota.
    """

    BERAT = ("/api/tts", "/api/chat", "/api/stt", "/api/sing")

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.inner(scope, receive, send)

        client = (scope.get("client") or ("", 0))[0]
        lokal = client in ("127.0.0.1", "::1", "localhost")
        path = scope.get("path", "")

        # --- rate limit (berlaku juga untuk lokal, murah) ---
        berat = any(path.startswith(b) for b in self.BERAT)
        if not auth.batasi(client or "?", berat=berat):
            body = b'{"error":"rate limit","detail":"terlalu banyak permintaan, tunggu sebentar"}'
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": [(b"content-type", b"application/json"),
                            (b"retry-after", b"30"),
                            (b"content-length", str(len(body)).encode())],
            })
            await send({"type": "http.response.body", "body": body})
            return

        if lokal or not pin.aktif():
            return await self.inner(scope, receive, send)

        from urllib.parse import parse_qs

        headers = dict(scope.get("headers") or [])
        qs = parse_qs(scope.get("query_string", b"").decode("latin-1"))
        token = (headers.get(b"x-kos-token", b"").decode("latin-1")
                 or (qs.get("token") or [None])[0])
        if auth.cocok(token):
            return await self.inner(scope, receive, send)

        tebakan = (qs.get("pin") or [None])[0]
        cookie = headers.get(b"cookie", b"").decode("latin-1")
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
'''

awal = s.find("class PinGate:")
akhir = s.find("app = PinGate(app)")
if awal != -1 and akhir != -1:
    s = s[:awal] + baru + "\n\n" + s[akhir:]
    p.write_text(s)
    print("PinGate diganti:", "X-Kos-Token" in s)
else:
    print("PERINGATAN: blok PinGate tidak ketemu", awal, akhir)

import ast
ast.parse(s)
print("sintaks OK")
