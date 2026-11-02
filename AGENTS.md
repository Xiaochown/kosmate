# AGENTS.md — Kosmate / "Kai"

Baca file ini SEBELUM menyentuh apa pun. Ini peta proyek, bukan dokumentasi marketing.
Kalau ada yang tidak cocok antara file ini dan kode, **kode yang benar** — lalu perbaiki file ini.

---

## 1. Apa ini

Asisten suara AI Bahasa Indonesia yang jalan **100% di HP Android** (Termux + Chrome):
ngomong → STT → LLM → TTS, dengan memori personal, pengingat, jurnal, catatan (RAG),
mode fokus, wake word, dan mode nyanyi. Tanpa root, tanpa VPS, biaya ≈ Rp0
(LLM pakai API key user sendiri, TTS pakai Fish Audio `s2.1-pro-free`).

- Versi sekarang: lihat `VERSION` (sekarang `2.5-sing`)
- Tag checkpoint: `v2.1-checkpoint`, `v2.2-checkpoint`, `v2.3-sprintA`, `v2.5-sing`
- Repo: `Xiaochown/kosmate` (publik, MIT, branch `main`)
- Demo statis: `Xiaochown/companion-demo` → https://xiaochown.github.io/companion-demo/

## 2. Arsitektur (peta file)

```
kos/                  backend Starlette (BUKAN FastAPI — lihat §7)
  app.py      (612)   semua route, lifespan, PinGate (PIN + token + rate limit)
  memory.py   (412)   SQLite FTS5: episodes, facts; context_block(), export
  extras.py   (262)   reminders, notes(RAG), journal, usage, announce, parse_kapan()
  llm.py      (189)   client OpenAI-compatible, streaming SSE/NDJSON, fallback model
  tts.py      (145)   Fish + edge, chunking, cache MP3, clean_for_speech()
  voices.py   (127)   11 voice (Fish reference_id + tempo per voice)
  settings.py (131)   setelan runtime data/settings.json (clamp min/max)
  persona.py  (106)   mode teman/tutor/kerja/cerita + tone/humor/nickname
  migrate.py   (95)   migrasi berversi (PRAGMA user_version) + backup otomatis
  scheduler.py (88)   pengingat sisi server → termux-notification
  auth.py      (95)   token per device + rate limit
  sing.py      (210)  mode nyanyi: suku kata → TTS → pitch-shift ffmpeg
  metrics.py   (52)   latency per komponen (llm/tts/stt/sing)
  stt.py / pin.py     STT fallback, halaman PIN

web/                  frontend vanilla (tanpa framework, tanpa build step)
  index.html          struktur + kontrak id/class (JANGAN rename, lihat §5)
  style.css  (860)    tema cozy farm: token, panel, tombol, orb, sheet, kartu
  app.js     (1139)   chat SSE, pipeline TTS prefetch, voice, settings, debug overlay
  extras.js           quick actions, reminder, jurnal, RAG, fokus, nyanyi, briefing
  wake.js             wake word "Hei Kai" (instance SpeechRecognition sendiri)
  i18n.js             kamus ID/EN + ukuran tampilan (zoom)
  sw.js               service worker (HTML/CSS/JS network-first, /api bypass)
  manifest.json       PWA (path RELATIF — wajib, lihat §7)
  demo.js             mock API untuk demo statis
  assets/             maskot 4 pose, banner, 4 kartu + sing, 2 tekstur, ikon

scripts/              55+ script: tes, build aset, deploy, diagnosa
docs/                 TUTORIAL.html, BLUEPRINT.html, POLISH_PROMPT.md
data/                 RUNTIME — jangan di-commit (db, .env, jurnal, backup)
profile/              profil Hermes 'web-builder' + installer
```

## 3. Jalan & tes

```bash
# jalan (di box dev)
bash scripts/serve_local.sh 8080        # atau: bash scripts/restart.sh 8080

# tes cepat (jalankan setelah SETIAP perubahan backend)
python3 scripts/smoke_py.py             # harus "13 lolos, 0 gagal"

# tes UI (jsdom)
node scripts/ui_v9_test.cjs             # 0 js_errors, 5 kartu, 10 field advanced
node scripts/ui_v10_wake_test.cjs       # wake word: toggle, deteksi, persistensi
node scripts/ui_v11_lang_test.cjs       # bahasa ID/EN, zoom, konfirmasi hapus
node scripts/ui_v8_test.cjs             # jeda TTS antar potongan ~0

# tes fitur
python3 scripts/test_sprint_a.py        # pengingat server-side (tunggu ~20 detik)
python3 scripts/test_sprint_a4.py       # token device + rate limit
python3 scripts/test_sing_http.py       # /api/sing → 200 audio/mpeg
python3 scripts/test_extras.py          # reminder/jurnal/catatan/kuota/export

# deploy demo
cp web/{style.css,app.js,extras.js,wake.js,i18n.js,index.html,manifest.json,sw.js} demo/
cp -r web/assets/. demo/assets/
python3 scripts/_fix_demo_index.py && python3 scripts/build_single.py
```

## 4. Status pekerjaan (per `2.5-sing`)

**Sudah selesai & teruji**
- Chat suara penuh: SSE, auto-continue kalau kepotong token, TTS prefetch 2 paralel (jeda ≈1 ms)
- 11 voice Fish (Miyaa default 0.80×), **tanpa fallback** — gagal = 503, bukan ganti timbre
- Wake word "Hei Kai": pause saat mic dipakai, lanjut saat idle, tersimpan di localStorage
- Pengingat **sisi server** (`termux-notification`) + antrean `/api/announce`
- Migrasi DB berversi + backup otomatis `data/backups/` (5 terakhir)
- Token per device (`X-Kos-Token`) + rate limit 240/menit (endpoint berat 30/menit)
- Jurnal harian, catatan RAG (FTS5), mode fokus, kuota, export/import memori
- Briefing pagi (`/api/briefing`), metrik latency (`/api/metrics`)
- Bahasa ID/EN, ukuran tampilan 95–120%, konfirmasi sebelum hapus
- Mode nyanyi: 5 lagu domain publik (`pelangi/twinkle/birthday/amazing/balon`)
- PWA installable (sw.js v3, ikon maskable), tema cozy farm lengkap

**Belum dikerjakan (urut prioritas, jangan lompat)**
1. RAG masih **lexical** (FTS5), belum embedding — lemah untuk sinonim jauh
2. Mode nyanyi: nada cuma dari preset/`nada` manual; belum bisa "nyanyi lagu X" bebas
3. Wake word hanya jalan saat tab Chrome di depan (batas Web Speech API)
4. Undo universal (sekarang cuma konfirmasi)
5. App native Kotlin untuk mic 24 jam (di luar cakupan Termux)

## 5. Kontrak yang TIDAK boleh diubah

Rename id/class = fitur mati diam-diam (tidak ada error, cuma tombolnya berhenti kerja).

```
body[data-state="idle|listening|thinking|speaking"]
#status #live #reply #replyYou #replyText .reply.show
#orb .orb .orb-ring .orb-core .mascot
#voiceChip #voiceNote #setVoice #setTempo
#healthDot #brandSub #memCount
#actBtn #memBtn #diagBtn #gear #actSheet #sheet #diagSheet .sheet.open
#advFields #personaFields #notesList #notesFile #usageBox #btnExport #importFile
#remindTeks #remindList [data-kapan] [data-focus] #focusStop
#journalDay #journalWeek #journalList #setWake #setLang #setZoom #setConfirm
#singLirik #singLagu #singGo #singStop
#closeAct #closeSheet #closeDiag #diagTtsTest #diagMicTest
.row .row-label .switch(.on) .field .fact .chip .btn(.solid) .preset
.cards .card(.wide) .card-media .card-body .group-title
```

Event internal: `document.dispatchEvent(new CustomEvent("kos:state", {detail: st}))`
dipakai `wake.js` untuk pause/resume. Jangan hapus.

## 6. Aturan kerja (kenapa begini, bukan lain)

- **Vanilla HTML/CSS/JS.** Tanpa framework, tanpa build step, tanpa dependency baru.
  Alasan: target HP kentang + install di Termux. Kalau butuh library, tanya dulu.
- **Starlette, BUKAN FastAPI.** `pydantic-core` butuh Rust; rustup tidak punya target
  `aarch64-unknown-linux-android` → instalasi pasti gagal di HP.
- **Satu blok TTS + prefetch paralel.** Jangan pecah per kalimat (intonasi jadi kereset).
- **Mic gating ketat.** Mic mati selama speaking/antrean; ketuk orb = potong.
- **Setiap klaim harus ada angka.** "Sudah diperbaiki" tanpa output tes = belum selesai.
- **Commit per satuan kerja** + tag checkpoint sebelum perubahan besar. Push ke `main`.
  Jangan push `demo/` ke repo utama (di-gitignore); demo punya repo sendiri.

## 7. Jebakan yang sudah memakan waktu (baca sebelum debug)

| Gejala | Sebab nyata |
|---|---|
| `pkg install` menggantung lama / install lambat | `pkg update` + `ffmpeg` 50 MB. Pakai `KOSMATE_SKIP_PKG=1`; ffmpeg cuma perlu untuk nyanyi |
| `curl: cannot locate symbol ngtcp2_...` | curl Termux rusak. **Semua** health-check pakai `python3 scripts/_health.py` (urllib) |
| Gambar UI "patchwork", latar beda-beda | Aset digenerate terpisah: beda rasio + beda tint. Jalankan `scripts/build_assets.py` (crop → samakan latar → grade) |
| Karakter terlihat beda ukuran antar pose | Crop pakai bbox objek. Harus crop **fraksi tetap** (86–97% frame) |
| Server jalan tapi `?v=` masih desain lama | Service worker cache-first. Sekarang network-first + bump `CACHE` di `sw.js` |
| "This app cannot be installed" | Path manifest absolut di GH Pages subpath. Harus `./` dan `assets/...` |
| Suara bisu setelah reload | Autoplay diblok. `unlockAudio()` di gesture pertama |
| `chromium`/Playwright hang (`EXIT=124`) | Chromium tidak bisa render di proot (network service mati). Pakai jsdom + overlay `?debug=1` |
| ffmpeg `libblas.so.3` / `invalid ELF header` | Env lib salah. `sing.py` sudah auto-probe; jangan hardcode `LD_LIBRARY_PATH` |
| Perintah panjang ditempel di Termux kepotong | Bikin script pendek di repo (`fix.sh`, `go.sh`), chat cukup satu baris pemanggil |
| `data/pin.txt` pernah ter-commit | Sekarang di-gitignore. Kalau bocor, ganti PIN |

## 8. Rahasia & data

- `.env` (LLM base/key/model, `FISH_API_KEY`, Telegram) — **tidak pernah** di-commit
- `data/` = runtime: `kosmate.db`, `settings.json`, `voice.json`, `journal/`, `backups/`, `pin.txt`
- Jangan pernah mencetak isi `.env` ke chat/log. Jangan commit `data/`.
- Update kode di HP: user menjalankan `bash go.sh` (ZIP dari GitHub, `data/` & `.env` dipertahankan).

## 9. Cara lanjut kerja

1. `git pull` lalu baca §4 — pilih item prioritas teratas.
2. Baca file yang akan diubah (§2), jangan menebak.
3. Ubah → jalankan tes di §3 → baru commit.
4. Kalau menyentuh UI: jalankan `ui_v9` + `ui_v10` + `ui_v11`, dan pastikan tidak ada id di §5 yang hilang.
5. Kalau menyentuh aset: `python3 scripts/build_assets.py` lalu cek luminance 150–180.
6. Update bagian §4 di file ini kalau status berubah. File ini harus selalu jujur.
