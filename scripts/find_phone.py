"""Cari HP kosmate di LAN: scan port 8022 (sshd) & 8080 (kosmate) cepat."""
import concurrent.futures
import socket

NET = "192.168.1."
PORTS = (8022, 8080)


def cek(ip: str) -> list[str]:
    hits = []
    for p in PORTS:
        s = socket.socket()
        s.settimeout(0.45)
        try:
            s.connect((ip, p))
            hits.append(str(p))
        except Exception:
            pass
        finally:
            s.close()
    return [ip + " -> " + ",".join(hits)] if hits else []


hasil = []
with concurrent.futures.ThreadPoolExecutor(max_workers=128) as ex:
    for r in ex.map(cek, (NET + str(i) for i in range(1, 255))):
        hasil.extend(r)

print("ditemukan:" if hasil else "tidak ada host dengan port itu")
for h in hasil:
    print("  " + h)
