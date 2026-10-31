import pathlib

# .env.example: variabel baru
p = pathlib.Path("/root/kosmate/.env.example")
t = p.read_text()
if "TELEGRAM_BOT_TOKEN" not in t:
    t = t.rstrip() + """

# --- watchdog (opsional) ---
# bikin bot lewat @BotFather, chat id dari @userinfobot
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
"""
    p.write_text(t)
    print(".env.example: telegram ditambahkan")

# README: bagian fitur baru
r = pathlib.Path("/root/kosmate/README.md")
t = r.read_text()
if "## Fitur harian" not in t:
    t = t.replace("## UI (v0.9)", """## Fitur harian (v1.1)

Semua diakses dari tombol **Actions** di header; kartunya pakai ilustrasi asli
(`web/assets/*.webp`).

- **Bedtime story** — set preset story + mode pencerita; target kata bisa diatur,
  cerita dilanjutkan otomatis sampai target lalu ditutup dengan kalimat menenangkan
- **Focus** — timer 15/25/45 menit; Kai mengumumkan setengah jalan & akhir
- **Reminder** — "5 menit / 15 menit / 1 jam / jam 9"; diucapkan saat jatuh tempo
  (`parse_kapan` juga paham "dalam 2 jam", "besok jam 9")
- **Journal** — ringkasan hari ini / minggu ini, ditulis orang pertama, disimpan
  ke `data/journal/YYYY-MM-DD.md`
- **Notes (RAG)** — unggah catatan kuliah (.txt/.md/.html); dipecah ~900 char,
  diindeks FTS5, dan 3 potongan relevan disisipkan ke prompt saat menjawab
- **Personality** — tone (santai/lembut/tegas), humor 0–2, nickname
- **Data & usage** — ekspor/impor memori JSON + hitungan token & karakter TTS hari ini
- **Wake word "Hei Kai"** — toggle di Settings → Listening (butuh Chrome di depan)
- **Watchdog** — `bash scripts/watchdog.sh --loop`: cek tiap 5 menit, restart kalau mati,
  lapor Telegram (`TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` di .env)
- **PWA** — `manifest.json` + ikon, bisa "Add to Home screen"

API baru: `/api/reminders`, `/api/reminders/due`, `/api/usage`, `/api/journal`,
`/api/notes`, `/api/import`, `/api/settings`.

## UI (v0.9)""")
    r.write_text(t)
    print("README: fitur harian ditambahkan")
