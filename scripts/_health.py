"""Cek kesehatan server tanpa curl (curl Termux sering rusak).

pakai: python scripts/_health.py [port]
stdout: JSON /api/health kalau hidup. exit 1 kalau tidak.
"""
import sys
import urllib.error
import urllib.request

port = sys.argv[1] if len(sys.argv) > 1 else "8080"
url = f"http://127.0.0.1:{port}/api/health"

try:
    with urllib.request.urlopen(url, timeout=5) as r:
        body = r.read().decode("utf-8", "ignore")
    if not body.strip().startswith("{"):
        raise ValueError("bukan JSON")
    sys.stdout.write(body)
except (urllib.error.URLError, ValueError, OSError) as e:
    sys.stderr.write(f"{type(e).__name__}: {e}\n")
    sys.exit(1)
