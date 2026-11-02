import pathlib

p = pathlib.Path("/root/kosmate/README.md")
t = p.read_text()

blok = """
## Mode nyanyi

Menu Cepat -> **Nyanyi**. Tulis lirik, pilih lagu, Kai nyanyi mengikuti nada lagu.

Cara kerjanya: lirik dipecah per suku kata (aturan V-K-V bahasa Indonesia),
tiap suku kata disintesis pendek lewat TTS, lalu **digeser nadanya** ke nada lagu
pakai ffmpeg (`asetrate` + `atempo`), dipotong sesuai panjang not, lalu digabung.

Lagu bawaan (domain publik / lagu anak): `pelangi`, `twinkle`, `birthday`,
`amazing`, `balon`. Bisa juga kirim nada sendiri lewat field `nada`
(daftar `[midi, ketukan]`).

Syarat: **ffmpeg** terpasang (`pkg install ffmpeg`). Endpoint:
`POST /api/sing {lirik, lagu}` -> `audio/mpeg`, daftar lagu: `GET /api/sing/songs`.

Batas: maksimal 64 suku kata, ~1 detik per suku kata (satu permintaan TTS per suku).
Suara tetap suara Kai yang sedang aktif — bukan penyanyi studio.

## Pengingat yang tetap bunyi

Pengingat sekarang dicek **di server** (bukan dari halaman), lalu dikirim sebagai
notifikasi Android lewat `termux-notification`. Jadi tetap bunyi walau Chrome ditutup.
Kalimat yang tertinggal diucapkan Kai saat halaman dibuka lagi (`/api/announce`).
Matikan salah satu: hapus paket termux-api, atau biarkan — Kai tetap mengucapkannya.

## Keamanan akses tunnel

- PIN tetap ada (`data/pin.txt`), tapi sekarang ada **token per device**:
  `GET /api/tokens`, `POST /api/tokens {nama}`, `DELETE /api/tokens/{nama}`
  Kirim lewat header `X-Kos-Token: <token>` atau `?token=`.
- **Rate limit**: 240 permintaan/menit per IP, endpoint berat (chat/tts/stt/sing) 30/menit.

## Database

Skema punya versi (`PRAGMA user_version`). Sebelum migrasi apa pun, file DB
dicopy ke `data/backups/kosmate-YYYYmmdd-HHMMSS.db` (5 terakhir disimpan).
Jadi update lewat `go.sh` tidak akan menghapus jurnal/ingatan.

## Diagnostik

`Settings -> Diagnostics` sekarang menampilkan **metrik latency**: LLM token pertama,
total LLM, potongan suara pertama, total suara, dan STT — rata-rata, p95, jumlah sampel.

## Bahasa & ukuran tampilan

`Settings -> Display & language`: pilih **Indonesia (mudah)** untuk menyembunyikan
istilah teknis, dan atur ukuran tampilan 95% / 100% / 110% / 120%.
Tombol hapus juga menanyakan konfirmasi lebih dulu (bisa dimatikan).
"""

if "## Mode nyanyi" not in t:
    t = t.rstrip() + "\n" + blok
    p.write_text(t)

print("README:", "## Mode nyanyi" in p.read_text())
