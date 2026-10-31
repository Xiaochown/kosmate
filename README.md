# KOSMATE — AI teman kos di HP bekas

Poco X3 NFC yang nganggur → asisten suara real-time yang nemenin ngobrol, ngajarin, dan bantuin kerja.
Jalan **100% di HP itu sendiri**: tanpa server sewa, tanpa GPU, tanpa langganan (default pakai model gratis).

```
        ┌────────────────────────── POCO X3 NFC ──────────────────────────┐
        │                                                                  │
  🎙 mic ──► Chromium/FullyKiosk (web UI)                                    │
        │      │  VAD + Web Speech API (STT gratis, streaming, id-ID)     │
        │      ▼                                                           │
        │   Starlette + uvicorn (:8080)                                        │
        │      ├─ /api/chat   → LLM API punya lu (streaming SSE)           │
        │      ├─ /api/tts    → Fish Audio / edge-tts  → 🔊 speaker        │
        │      ├─ /api/stt    → fallback ASR (kalau browser gak support)    │
        │      └─ memori      → SQLite + FTS5 (fakta & obrolan lama)        │
        │                                                                  │
        └──────────────────────────────────────────────────────────────────┘
                          ▲ bisa juga: otak dipindah ke STB/server,
                            HP jadi satelit (mic + speaker + layar)
```

## Yang bikin ini "teman" bukan cuma chatbot

| Lapisan | Isi |
|---|---|
| **Suara** | STT streaming di browser → LLM stream → TTS per kalimat (bukan tunggu 1 paragraf penuh) |
| **Memori** | Tabel fakta bertanggal (`alergi kacang`, `ujian Senin jam 8`) + FTS5 + episode obrolan lama. Di-inject otomatis ke prompt tiap giliran |
| **Kepribadian** | `kos/persona.py` — bahasa Indonesia santai, jawaban 1–3 kalimat karena **diucapkan**, sadar jam (pagi/siang/malam), bisa inisiatif |
| **Mode** | `temen` (nemenin) · `tutor` (jelasin + uji pemahaman) · `kerja` (langkah konkret, deadline) |
| **Proaktif** | Sapaan otomatis sesuai jam + memori, bukan nunggu ditanya |

## Yang dibutuhkan

**Wajib**
- Poco X3 NFC (atau HP Android apa pun, RAM ≥ 3GB) + charger
- Termux (dari F-Droid, **bukan** dari Play Store — versi Play Store sudah usang)
- 1 API key LLM OpenAI-compatible (punya lu sudah cukup: TeamORouter, Ldrcloud, Genspark, dll)
- Speaker: **pakai jack 3.5mm** Poco X3 NFC ke speaker aktif (Simbadda/Edifier ~150–250rb). Jangan Bluetooth — delay 150–300ms bikin percakapan canggung.

**Opsional (naikin kualitas)**
- Fish Audio API key → suara lebih natural + bisa kloning suara sendiri (`FISH_REFERENCE_ID`), model `s2.1-pro-free` masih **$0**
- Root/Magisk + "Battery Charge Limit" → batasi cas 60–80% biar baterai gak kembung walau nyala 24/7
- Fully Kiosk Browser (gratis) → auto-start saat boot, layar selalu nyala, restart otomatis kalau crash
- Mic USB-C clip-on (BOYA ~100rb) kalau mau nangkep suara dari jauh
- STB/server rumah (punya lu sudah ada) → pindah otak ke situ, HP jadi satelit

## Pasang

**Satu baris, selalu versi terbaru:**

```bash
curl -sL https://raw.githubusercontent.com/Xiaochown/kosmate/main/install.sh | bash
```

Itu memasang paket dasar, meng-clone repo ke `~/kosmate` (kalau sudah ada: `git pull`,
dan `data/` + `.env` lama dipertahankan), lalu menjalankan installer interaktif:
benerin pip rusak, pilih venv/uv/sistem, install dependency, **tanya API key sekali
(input tersembunyi)**, validasi key ke `/models`, tes LLM, tes TTS, tulis `.env`,
nyalakan server, lalu set autostart (Termux:Boot) + sshd (port 8022) dengan public key
untuk debugging jarak jauh.

Update berikutnya cukup:

```bash
bash ~/kosmate/update.sh
```

**Alternatif: dari file zip** (kalau tidak mau pakai git)

```bash
unzip -o ~/Download/kosmate.zip -d ~/
bash ~/kosmate/scripts/autoinstall.sh
```

**Kalau `curl` / `git` di Termux rusak** (mis. `cannot locate symbol ngtcp2...`,
`pkg` gagal karena dia ngecek mirror pakai curl) — pakai bootstrap lewat python,
tanpa curl dan tanpa git sama sekali:

```bash
apt update && apt full-upgrade -y   # benerin lib yang tidak sinkron (ini yang bikin curl mati)
python -m ensurepip --upgrade       # benerin pip
```

lalu jalankan installer tanpa curl:

```bash
python -c "import urllib.request as u,os;d=u.urlopen(u.Request('https://api.github.com/repos/Xiaochown/kosmate/contents/install.sh',headers={'Accept':'application/vnd.github.raw','User-Agent':'kosmate'}),timeout=60).read();p=os.path.expanduser('~/kos.sh');open(p,'wb').write(d);os.environ['KOSMATE_FORCE_ZIP']='1';os.execvp('bash',['bash',p])"
```

**Jalur manual (kalau mau paham tiap langkah):**

```bash
pkg update -y && pkg install -y python ffmpeg unzip
termux-setup-storage
unzip /sdcard/Download/kosmate/kosmate.zip -d ~/
cd ~/kosmate
bash scripts/install.sh     # benerin pip + dependency

cp .env.example .env
nano .env                   # LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_MODEL_FALLBACK

bash scripts/termux-start.sh   # wake-lock + buka http://127.0.0.1:8080
```

Buka di Chrome HP: `http://127.0.0.1:8080`
Dari HP lain di WiFi yang sama: `http://<ip-hp>:8080` (cek `ifconfig wlan0`)

**Jadikan kiosk:** install Fully Kiosk Browser → Start URL `http://127.0.0.1:8080` → aktifkan *Keep Screen On*, *Launch on Boot*, *Restart on Crash* → matikan battery optimization buat Termux + Fully.

## Struktur

```
kosmate/
├── kos/
│   ├── app.py       # Starlette: /api/chat (SSE), /api/tts, /api/stt, /api/memory/*
│   ├── persona.py   # system prompt, mode, sapaan sadar-jam
│   ├── memory.py    # SQLite + FTS5 + fakta bertanggal + retrieval hybrid
│   ├── llm.py       # client OpenAI-compatible (tahan SSE/NDJSON/wrapper {"data":..})
│   ├── tts.py       # Fish Audio streaming → fallback edge-tts + cache
│   ├── stt.py       # Fish ASR / whisper.cpp (fallback server-side)
│   └── config.py    # baca .env tanpa dependency
├── web/             # UI: orb, mode, sheet memori, antrean TTS
├── scripts/         # install, termux-start, termux-boot, diag, kiosk, smoke test
├── docs/
│   ├── TUTORIAL.html   # ⬅ panduan dari nol, 12 bagian, bisa dicentang
│   └── BLUEPRINT.html  # ringkasan desain & keputusan
└── data/            # kosmate.db + cache audio  (gitignored)
```

**Baru pertama kali? Buka `docs/TUTORIAL.html` di Chrome HP** — langkah demi langkah,
ada contoh output yang benar dan bagian troubleshooting.

## Endpoint

| Method | Path | Fungsi |
|---|---|---|
| POST | `/api/chat` | `{message, session}` → SSE: `start` / `delta` / `done` / `error` |
| POST | `/api/tts` | `{text, voice}` → `audio/mpeg` (streaming, ada cache) |
| POST | `/api/stt` | multipart `audio` → `{text}` |
| POST | `/api/greeting` | sapaan proaktif dari jam + memori |
| POST | `/api/mode` | `{mode: temen\|tutor\|kerja}` |
| GET | `/api/memory/facts` · `/api/memory/search?q=` · `/api/memory/context?q=` |
| DELETE | `/api/memory/facts/{id}` | hapus fakta (dia langsung lupa) |
| GET | `/api/export` | backup seluruh memori (JSON) |

## Budget latency (target biar kerasa "hidup")

| Tahap | Waktu realistis | Cara nurunin |
|---|---|---|
| Deteksi selesai bicara (VAD) | 300–900 ms | `setSilence` di UI, turunin ke 600 ms |
| STT | 200–500 ms | Web Speech API sudah streaming; hindari kirim file utuh |
| LLM token pertama | 300 ms – 2 s | pakai model `flash`/`free`; hindari model reasoning |
| TTS byte pertama | 400 ms – 1,5 s | Fish > edge-tts; cache kalimat pendek |
| **Total** | **~1,5–3,5 s** | target berikutnya: < 1,2 s |

Biar gak nunggu: balasan dipecah per kalimat dan tiap kalimat langsung disintesis selagi LLM masih nulis sisa jawabannya.

## Roadmap

**P0 — sudah jalan (repo ini)**
voice loop, memori fakta, 3 mode, sapaan proaktif, UI kiosk.

**P1 — bikin betah (1–2 minggu)**
- [ ] wake word ("Kai") → `openWakeWord` atau Porcupine, supaya gak perlu ketuk
- [ ] barge-in: potong TTS begitu user mulai ngomong (butuh echo cancellation)
- [ ] flashcard SRS buat mata kuliah (Logika, Basis Data) — dia yang nanyain, lu jawab pakai suara
- [ ] jurnal harian + ringkasan "hari ini lo gimana" tiap jam 22
- [ ] pengingat deadline + daftar tugas sederhana

**P2 — bikin tahan lama (2–4 minggu)**
- [ ] pindah otak ke STB Armbian (24/7, HP cuma satelit lewat browser)
- [ ] whisper.cpp lokal (`small` q5) → STT gratis, offline, privasi penuh
- [ ] kloning suara sendiri via Fish Audio (rekam 1 menit)
- [ ] satelit kedua: HP/tablet lain di kamar mandi/dapur

**P3 — bikin nyambung ke hidup**
- [ ] Google Calendar & tugas kampus, Obsidian/Notion, Home Assistant (lampu/AC)
- [ ] kontrol via Telegram kalau lagi di luar
- [ ] "sleep mode": suara pelan, cerita pendek, auto-off

**P4 — versi serius**
Native Android (Kotlin) + foreground service + wake word + AEC → baru bisa benar-benar always-on tanpa Chrome.

## Biaya

| Komponen | Biaya |
|---|---|
| LLM (model free TeamORouter) | Rp0 |
| TTS Fish `s2.1-pro-free` | Rp0 |
| TTS edge-tts | Rp0 |
| ASR Fish `transcribe-1-pro` (kalau dipakai) | $0.36/jam audio ≈ Rp5.800/jam |
| Listrik HP nyala 24/7 (~5 W) | ± Rp10–15 rb/bulan |
| **Total** | **≈ Rp15 rb/bulan** |

## Privasi

- Semua memori ada di `data/kosmate.db` di HP. Backup: `GET /api/export`.
- Yang keluar dari HP: teks percakapan → provider LLM; teks balasan → provider TTS.
- **Kalau pakai Web Speech API, audio suara lu diproses Google.** Mau privasi penuh: P2 pakai whisper.cpp lokal, dan `TTS_PROVIDER=fish`/lokal.
- Stream suara gak pernah direkam ke disk.

## Jebakan yang sudah ketemu

1. **Termux dari Play Store** ≠ Termux F-Droid → banyak paket gagal build.
2. `UV_LINK_MODE=copy` wajib; hardlink gagal di Android.
3. `edge-tts` butuh kompilasi `aiohttp`. Kalau gagal → `TTS_PROVIDER=fish`.
4. Chrome Android **memblokir audio autoplay**: sapaan pertama bunyi setelah user menyentuh layar sekali (sudah di-handle: `unlockAudio`).
5. Port <1024 gak bisa dipakai tanpa root → pakai 8080.
6. Half-duplex: mic dimatikan selama TTS bunyi (biar gak denger suaranya sendiri). Barge-in butuh AEC → P1.
7. Dicas 24/7 bikin baterai panas → batasi 60–80% atau pakai smart plug timer.
8. Provider aneh (mis. bungkus respons jadi `{"data":{...}}` walau non-stream) sudah ditangani di `kos/llm.py`.
9. **Termux + Python 3.14**: `pip` lama bisa rusak (`bad interpreter: python3.13`) setelah `pkg upgrade`. Pakai `python -m pip`, bukan `pip`. `install.sh` sudah otomatis benerin lewat `ensurepip`.
10. **Jangan pakai FastAPI di sini.** pydantic-core ditulis Rust, tanpa wheel untuk `aarch64-linux-android` + Python 3.14 → `maturin`/`metadata-generation-failed`. Server pakai **Starlette** (murni Python). Ini juga alasan `requirements.txt` gak nyebut fastapi sama sekali.
11. FTS5 dibuat **standalone**, bukan `content='facts'` — versi external-content bikin `DELETE` gagal dengan `no such column: T.obj`. DB lama otomatis di-rebuild saat start (`fts_version` di tabel `meta`).
