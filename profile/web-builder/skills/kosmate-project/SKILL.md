---
name: kosmate-project
description: Resume Kosmate/Kai voice-assistant project work.
---

# Kosmate / "Kai" — project resume skill

Pakai skill ini setiap kali user menyebut: **Kosmate, Kai, asisten suara, voice companion,
mode nyanyi, wake word, atau proyek Termux + Chrome**.

## Langkah pertama (wajib, jangan dilewat)

1. Cari foldernya: `~/kosmate` (Termux/Linux), `$HOME/kosmate`, atau `C:\Users\<user>\kosmate`.
2. **Baca `AGENTS.md` di root repo itu** — di situ ada peta file, status pekerjaan,
   kontrak id/class yang tidak boleh diubah, perintah tes, dan 11 jebakan yang sudah
   memakan waktu. Jangan menebak arsitektur sebelum membacanya.
3. `git pull` dulu, dan cek `cat VERSION` + `git log --oneline | head -3`.
4. Jalankan `python3 scripts/smoke_py.py` — kalau bukan "13 lolos", server/kode belum sehat,
   perbaiki itu dulu sebelum menambah fitur.

## Kalau foldernya belum ada di device ini

```bash
cd ~ && python -c "import urllib.request as u;open('jp.sh','wb').write(u.urlopen('https://raw.githubusercontent.com/Xiaochown/kosmate/main/profile/join-project.sh').read())" && bash jp.sh
```

Script itu: unduh repo (git atau ZIP), bikin venv + dependency, pasang skill desain,
lalu mencetak langkah berikutnya.

## Batasan produk (jangan dilanggar tanpa bertanya)

- Jalan di HP Android via Termux + Chrome. Tanpa root, tanpa VPS, tanpa Docker.
- Backend **Starlette** (bukan FastAPI: pydantic-core butuh Rust yang tidak ada untuk Android).
- Frontend **vanilla** HTML/CSS/JS, tanpa framework/build step.
- TTS Fish Audio; **tanpa fallback** — kalau voice gagal, balas 503 jangan ganti timbre.
- Data user (`data/`, `.env`) tidak pernah di-commit dan tidak boleh dicetak ke chat.
- Desain: tema cozy indie-game (lihat skill `cozy-indie-game-ui`).

## Cara kerja yang diharapkan user

- Bahasa Indonesia santai, ringkas, langsung eksekusi kalau user bilang "gas".
- **Satu perintah** untuk user — jangan menyuruhnya menyalin path atau mengunduh manual.
- Setiap klaim disertai angka hasil tes; kalau belum dites, bilang belum.
- Commit per satuan kerja + tag checkpoint sebelum perubahan besar; push ke `main`.
