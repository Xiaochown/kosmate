"""Uji gerbang token + rate limit tanpa perlu tunnel beneran.

Memanggil middleware langsung dengan scope HTTP palsu, mensimulasikan request
dari IP publik.
"""
import asyncio
import sys

sys.path.insert(0, "/root/kosmate")

from kos import auth  # noqa: E402
from kos.app import PinGate  # noqa: E402
from kos.config import CFG  # noqa: E402


async def panggil(client_ip: str, path: str = "/api/journal", headers=None, qs=b""):
    """Kembalikan status code yang dikirim middleware."""
    tercatat = {}

    async def inner(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"lolos"})

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        if msg["type"] == "http.response.start":
            tercatat["status"] = msg["status"]

    gate = PinGate(inner)
    scope = {
        "type": "http",
        "path": path,
        "query_string": qs,
        "client": (client_ip, 12345),
        "headers": [(k.encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    await gate(scope, receive, send)
    return tercatat.get("status")


async def main():
    pin_file = CFG.data_dir / "pin.txt"
    asli = pin_file.read_text().strip() if pin_file.exists() else ""
    pin_file.write_text("999888")           # pastikan gate aktif
    auth.cabut("uji-device")

    print("--- 1. lokal (127.0.0.1) selalu lolos ---")
    print("  status:", await panggil("127.0.0.1"))

    print("\n--- 2. dari IP publik tanpa token/PIN ---")
    print("  status:", await panggil("8.8.8.8"), "(harus 401)")

    print("\n--- 3. dengan token device ---")
    tok = auth.buat("uji-device")
    print("  token dibuat, sidik:", auth.sidik(tok))
    print("  header X-Kos-Token:", await panggil("8.8.8.8", headers={"x-kos-token": tok}), "(harus 200)")
    print("  query ?token=      :", await panggil("8.8.8.8", qs=f"token={tok}".encode()), "(harus 200)")

    print("\n--- 4. token asal-asalan ---")
    print("  status:", await panggil("8.8.8.8", headers={"x-kos-token": "ngawur"}), "(harus 401)")

    print("\n--- 5. cabut token ---")
    auth.cabut("uji-device")
    print("  setelah dicabut:", await panggil("8.8.8.8", headers={"x-kos-token": tok}), "(harus 401)")

    print("\n--- 6. rate limit ---")
    auth._semua.clear()
    hasil = [auth.batasi("9.9.9.9") for _ in range(245)]
    print("  izinkan 240 pertama:", all(hasil[:240]))
    print("  ke-245 diblokir     :", hasil[-1] is False)
    auth._semua.clear()
    berat = [auth.batasi("9.9.9.9", berat=True) for _ in range(32)]
    print("  endpoint berat (tts/chat) batas 30:", all(berat[:30]), berat[-1] is False)

    pin_file.write_text(asli or "999888")
    print("\nsisa token:", auth.daftar())


asyncio.run(main())
