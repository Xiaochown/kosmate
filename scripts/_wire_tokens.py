"""Endpoint token device + rate limit test."""
import pathlib

p = pathlib.Path("/root/kosmate/kos/app.py")
s = p.read_text()

if "async def tokens_list" not in s:
    s = s.replace(
        "# ---------------------- antrean ucapan dari server ----------------------",
        '''# ---------------------- token device ----------------------
async def tokens_list(request: Request):
    return JSONResponse({"items": auth.daftar()})


async def tokens_add(request: Request):
    b = await request.json()
    nama = (b.get("nama") or "device").strip()
    token = auth.buat(nama)
    return JSONResponse({"nama": nama, "token": token, "sidik": auth.sidik(token)})


async def tokens_del(request: Request):
    nama = request.path_params["nama"]
    return JSONResponse({"ok": auth.cabut(nama)})


# ---------------------- antrean ucapan dari server ----------------------''',
    )
    s = s.replace(
        '    Route("/api/announce", announce_pending),',
        '''    Route("/api/tokens", tokens_list),
    Route("/api/tokens", tokens_add, methods=["POST"]),
    Route("/api/tokens/{nama}", tokens_del, methods=["DELETE"]),
    Route("/api/announce", announce_pending),''',
    )

p.write_text(s)
import ast
ast.parse(s)
print("endpoint token:", "tokens_add" in s, "| route:", '"/api/tokens"' in s)
