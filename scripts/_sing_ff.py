"""Ganti semua pemanggilan subprocess ffmpeg di sing.py pakai _ff (env LD_LIBRARY_PATH)."""
import pathlib

p = pathlib.Path("/root/kosmate/kos/sing.py")
s = p.read_text()

# _geser_nada
s = s.replace(
    '''    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(sumber), "-af", fil,
           "-ar", "44100", "-ac", "1", str(keluar)]
    try:
        subprocess.run(cmd, timeout=30, check=True)
        return keluar.exists() and keluar.stat().st_size > 200
    except Exception:  # noqa: BLE001
        return False''',
    '''    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(sumber), "-af", fil,
           "-ar", "44100", "-ac", "1", str(keluar)]
    ok = _ff(cmd, timeout=30)
    return ok and keluar.exists() and keluar.stat().st_size > 200''',
)

# jeda
s = s.replace(
    '''                subprocess.run(
                    ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                     f"anullsrc=r=44100:cl=mono", "-t", f"{jeda:.3f}", str(diam)],
                    timeout=15, check=False,
                )''',
    '''                _ff(
                    ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                     "anullsrc=r=44100:cl=mono", "-t", f"{jeda:.3f}", str(diam)],
                    timeout=15,
                )''',
)

# concat
s = s.replace(
    '''        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", str(daftar), "-ar", "44100", "-b:a", "128k", str(hasil)],
            timeout=120, check=True,
        )
        return hasil.read_bytes()''',
    '''        if not _ff(
            ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", str(daftar), "-ar", "44100", "-b:a", "128k", str(hasil)],
            timeout=120,
        ):
            raise ValueError("gagal menggabungkan audio (ffmpeg)")
        return hasil.read_bytes()''',
)

p.write_text(s)
import ast
ast.parse(s)
print("pakai _ff:", s.count("_ff(") >= 3, "| subprocess.run sisa:", s.count("subprocess.run"))
