"""Finalisasi: guard ffmpeg, sw.js aset baru, build_single i18n, demo stub."""
import pathlib
import re

# 1) sing.py: cek ffmpeg ada
p = pathlib.Path("/root/kosmate/kos/sing.py")
s = p.read_text()
if "def ada_ffmpeg" not in s:
    s = s.replace(
        "_ENV_FF: dict | None = None",
        '''def ada_ffmpeg() -> bool:
    import shutil

    return bool(shutil.which("ffmpeg"))


_ENV_FF: dict | None = None''',
    )
    s = s.replace(
        '''    suku = lirik_ke_suku(lirik)''',
        '''    if not ada_ffmpeg():
        raise ValueError("mode nyanyi butuh ffmpeg. Di Termux: pkg install ffmpeg")
    suku = lirik_ke_suku(lirik)''',
    )
    p.write_text(s)

# 2) sw.js: aset baru
w = pathlib.Path("/root/kosmate/web/sw.js")
t = w.read_text()
if "./assets/sing.webp" not in t:
    t = t.replace('  "./assets/story.webp",', '  "./assets/story.webp",\n  "./assets/sing.webp",') if '"./assets/story.webp"' in t else t
    if "./assets/sing.webp" not in t:
        t = t.replace('  "./assets/tex-wood-dark.webp",',
                      '  "./assets/tex-wood-dark.webp",\n  "./assets/sing.webp",')
    if "./i18n.js" not in t:
        t = t.replace('  "./wake.js",', '  "./wake.js",\n  "./i18n.js",')
    t = t.replace('const CACHE = "kai-shell-v2"', 'const CACHE = "kai-shell-v3"')
    w.write_text(t)

# 3) build_single: i18n + sing
b = pathlib.Path("/root/kosmate/scripts/build_single.py")
u = b.read_text()
if "i18n.js" not in u:
    u = u.replace('wake = (ROOT / "wake.js").read_text()',
                  'wake = (ROOT / "wake.js").read_text()\ni18n = (ROOT / "i18n.js").read_text()')
    u = u.replace('("wake.js", wake)):', '("wake.js", wake), ("i18n.js", i18n)):')
    u = u.replace('("mascot.webp", "image/webp"),', '("mascot.webp", "image/webp"), ("sing.webp", "image/webp"),')
    b.write_text(u)

# 4) demo.js: stub /api/sing + briefing + metrics
d = pathlib.Path("/root/kosmate/web/demo.js")
v = d.read_text()
if "/api/sing" not in v:
    v = v.replace(
        '    "/api/voice":',
        '''    "/api/sing/songs": { items: [
      { kunci: "pelangi", judul: "Pelangi (nada Twinkle Twinkle)", bpm: 100, not: 14 },
      { kunci: "balon", judul: "Balonku (lagu anak)", bpm: 112, not: 12 },
    ] },
    "/api/announce": { items: [] },
    "/api/tokens": { items: [] },
    "/api/metrics": {
      llm_first_token: { n: 12, rata: 640.2, p95: 910.0, akhir: 702.1 },
      llm_total: { n: 12, rata: 3200.5, p95: 4100.0, akhir: 3010.0 },
      tts_first_byte: { n: 20, rata: 780.4, p95: 1200.0, akhir: 690.0 },
      tts_total: { n: 20, rata: 2100.0, p95: 2900.0, akhir: 1980.0 },
      stt: { n: 8, rata: 900.0, p95: 1400.0, akhir: 880.0 },
      sing: { n: 0, rata: null, p95: null, akhir: null },
    },
    "/api/briefing": { ada: true, teks: "Selamat pagi. Jurnal terakhir: semalam gue belajar resolusi. Pengingat hari ini: 09:00 kelas SBD." },
    "/api/voice":''',
    )
    v = v.replace(
        '    if (p === "/api/tts")',
        '''    if (p === "/api/sing") return { ok: true, status: 200, json: async () => ({}), text: async () => "",
      blob: async () => new Blob([new Uint8Array(4096)], { type: "audio/mpeg" }) };
    if (p === "/api/tts")''',
    )
    d.write_text(v)

print("guard ffmpeg:", "def ada_ffmpeg" in s)
print("sw v3 + sing.webp:", "kai-shell-v3" in t and "./assets/sing.webp" in t)
print("build_single i18n:", "i18n.js" in u)
print("demo stub:", "/api/sing" in v)
