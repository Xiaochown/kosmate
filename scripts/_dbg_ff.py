import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/root/kosmate")

from kos import sing  # noqa: E402

env = sing._env_ffmpeg()
print("LD_LIBRARY_PATH:", env.get("LD_LIBRARY_PATH", "(kosong)"))

# 1) cek ffmpeg dasar
r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, env=env)
print("ffmpeg -version:", r.returncode, (r.stdout or r.stderr).splitlines()[:1])

# 2) cek tanpa env khusus
r2 = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
print("tanpa env     :", r2.returncode, (r2.stderr or "").splitlines()[:1])

# 3) coba geser nada pakai file uji
uji = Path("/tmp/uji.mp3")
data = Path("/tmp/nyanyi.mp3")
if uji.exists():
    keluar = Path("/tmp/uji.wav")
    ok = sing._geser_nada(uji, keluar, 2.0, 0.6)
    print("geser nada:", ok, keluar.exists() and keluar.stat().st_size)
    if not ok:
        r3 = subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(uji), "-af", "asetrate=44100*1.1", str(keluar)],
            capture_output=True, text=True, env=env,
        )
        print("stderr ffmpeg:", (r3.stderr or "")[:300])
else:
    print("file uji tidak ada")
