# PROMPT — Ratakan & perbagus desain "Kai" (tema Stardew Valley)

Copy seluruh isi di bawah ini ke model AI berikutnya (yang punya vision + bisa generate gambar).

---

## PERAN & TUJUAN

Kamu engineer + desainer UI. Tugasmu **meratakan dan memperbagus** tampilan aplikasi web
"Kai" (asisten suara Bahasa Indonesia) supaya konsisten, rapi, dan terasa seperti **game
indie cozy bergaya Stardew Valley** — bukan template SaaS.

Kamu PUNYA vision: wajib buka halamannya, screenshoot, kritik sendiri, perbaiki, lalu
screenshot lagi sampai rapi. Jangan menebak.

Yang dinilai berhasil:
1. Semua kartu/gambar punya ukuran & tone yang sama (tidak patchwork).
2. Tidak ada elemen mepet, kepotong, atau meluber, di lebar 360 / 390 / 414 px.
3. Terasa "game": kayu, krem, amber, tebal, chunky, hangat — bukan minimalis Linear.
4. Semua fungsi tetap jalan (chat, voice picker, settings, quick actions, reminders,
   journal, notes/RAG, focus timer, wake word, PWA).

## LOKASI KERJA

- Repo utama (aplikasi + backend): `Xiaochown/kosmate`, folder lokal `/root/kosmate`
  - `web/` → frontend statis (index.html, style.css, app.js, extras.js, sw.js, manifest.json, assets/)
  - `kos/` → backend Starlette (jangan diubah kecuali perlu)
  - `scripts/` → tooling (build & tes)
- Repo demo (dipakai user buat lihat tampilan): `Xiaochown/companion-demo`, folder lokal
  `/root/kosmate/demo` (hasil salinan `web/` + `demo.js` yang memalsukan API)
- Live demo: https://xiaochown.github.io/companion-demo/
- Halaman bisa dibuka lokal: server jalan di `http://127.0.0.1:8080` (kalau perlu:
  `bash scripts/restart.sh 8080`)

## BATASAN KERAS (jangan dilanggar)

- **Tanpa framework, tanpa build step, tanpa dependency baru.** HTML + CSS + JS vanilla.
- **Jangan rename/ hapus id atau class yang dipakai JS.** Kontrak yang dipakai `app.js`/`extras.js`:
  - `body[data-state="idle|listening|thinking|speaking"]` untuk state orb
  - `#status`, `#live`, `#reply`, `#replyYou`, `#replyText`, `.reply.show`
  - `#orb`, `.orb`, `.orb-ring`, `.orb-core`, `.mascot`
  - `#voiceChip` (chip suara di beranda), `#voiceNote`, `#setVoice`, `#setTempo`
  - `#healthDot`, `#brandSub`, `#memCount`
  - `#actBtn`, `#memBtn`, `#diagBtn`, `#gear`, `#actSheet`, `#sheet`, `#diagSheet`, `.sheet.open`
  - `#advFields`, `#personaFields` (diisi JS dari `/api/settings` — jangan hardcode)
  - `#notesList`, `#notesFile`, `#usageBox`, `#btnExport`, `#importFile`
  - `#remindTeks`, `#remindList`, `[data-kapan]`, `[data-focus]`, `#focusStop`
  - `#journalDay`, `#journalWeek`, `#journalList`, `#setWake`
  - `#cardStory`, `#closeAct`, `#closeSheet`, `#closeDiag`, `#diagTtsTest`, `#diagMicTest`
  - class yang dipakai gaya/JS: `.row`, `.row-label`, `.switch(.on)`, `.field`, `.fact`,
    `.chip`, `.btn(.solid)`, `.preset`, `.cards`, `.card(.wide)`, `.card-media`, `.card-body`
- **Aksesibilitas:** target tap ≥ 44px, teks ≥ 12px (isi ≥ 15px), kontras AA,
  `:focus-visible` jelas, tidak pakai emoji di tombol.
- **Offline-friendly:** jangan tambah CDN wajib. Font Google boleh, tapi harus ada fallback.
- **Mobile-first**, satu kolom, tidak ada scroll horizontal.
- Jangan pakai gradient pelangi/glassmorphism/shadow blur besar. Gaya: hard shadow + border tebal.

## PALET & TIPOGRAFI SAAT INI (boleh dirapikan, jangan diganti jauh)

```
--paper: #f7e7c6   (latar krem perkamen)
--paper-2: #efd9b0 (panel turun)
--paper-3: #e3c999 (footer composer)
--cream: #fffaf0   (kartu/panel terang)
--ink: #3d2a17      --ink-soft: #6b4c2c
--wood: #8a5a33     --wood-dark: #5b3a21   --wood-light: #b98b4f
--amber: #e8a33d    --leaf: #7aa53f        --leaf-dark: #4f7a2a
--night: #2b3a52    --danger: #c05a3a
font display: 'Pixelify Sans'  |  font body: 'Nunito'
```

Ciri gaya yang harus dipertahankan: border 3px cokelat tua, radius 10–14px, hard shadow
`0 4px 0 var(--wood-light)`, tombol "ambles" saat ditekan (translateY 2px + shadow hilang),
chip seperti tab inventory, balon jawaban dengan ekor.

## ASET GAMBAR (yang ada sekarang)

`web/assets/` (dipakai juga di `demo/assets/`):

| file | ukuran | dipakai di |
|---|---|---|
| `mascot.webp` | 520×520 | orb utama (maskot moon-spirit: topi jerami, syal hijau, lentera) |
| `banner.webp` | 1000×280 | strip di bawah header (farm saat senja) |
| `story.webp` | 640×400 | kartu Bedtime story |
| `focus.webp` | 640×400 | kartu Focus |
| `remind.webp` | 640×400 | kartu Reminder |
| `journal.webp` | 640×400 | kartu Journal |
| `icon-192/512.png`, `icon-maskable-512.png` | persegi | PWA / ikon install |

**Aturan aset:** semua kartu WAJIB 16:10 (640×400) dan `object-fit: cover` lewat
`.card-media`. Banner 1000×280. Maskot persegi. Setelah generate gambar baru, WAJIB
normalisasi pakai `python3 scripts/_grade_assets.py` (itu melakukan crop rasio + gamma
supaya luminance 150–180 + warm blend + saturasi 0.92). Kalau luminance antar gambar
selisih > 25, ulangi grade — itu penyebab tampilan "patchwork".

### Prompt generate gambar (pakai ini kalau perlu aset baru / ganti aset jelek)

Gaya acuan (tempel di setiap prompt, bahasa Inggris):
> "Cozy pixel-art-inspired painted illustration, Stardew-Valley-like farm game aesthetic,
> no text, no letters, no UI. Warm palette: cream parchment (#f7e7c6), wood brown
> (#5b3a21), amber lantern light (#e8a33d), sage green (#7aa53f), deep blue night
> (#2b3a52). Thick soft outlines, chunky simple shapes, gentle painterly shading,
> centered composition, generous padding."

1. **maskot (square)** — "A small round moon-spirit mascot: creamy white round body, tiny
   straw hat, little green scarf, big friendly dark eyes, soft blush, holding a tiny
   glowing lantern, sitting on a wooden stump. Plain flat cream background, sticker-like."
2. **banner (landscape, akan di-crop 1000×280)** — "A small farm cottage at dusk seen from
   the yard: wooden fence, glowing paper lanterns, pumpkin patch, pine trees, wooden well,
   warm windows, starry sky with big soft moon. Wide panoramic."
3. **story** — "Cozy bedroom corner at night: wooden bed with patchwork quilt, glowing
   lantern, open storybook with soft light, small window with moonlight, sleeping cat."
4. **focus** — "Wooden work desk: hourglass with golden sand, stack of books, steaming cup
   of tea, small potted sprout, lit candle."
5. **remind** — "Wooden signpost at a farm gate with a small brass bell and two paper notes,
   winding path, lanterns, tall grass."
6. **journal** — "Open leather journal with cream pages on a wooden table, quill in ink pot,
   steaming teacup, folded map, tiny crescent moon charm."

**Jangan** minta teks di dalam gambar (selalu "no text") — huruf hasil generate pasti rusak.

## YANG HARUS DIPERBAIKI (checklist kerja)

Ukur dulu, jangan asal ubah. Kalau kamu punya browser/vision, screenshot di 360, 390, 414 px.

1. **Header** harus 1 baris, tinggi ≤ 56px. Nav 4 tombol: di < 440px tampil ikon saja
   (label `.lbl` disembunyikan), ≥ 440px ikon + label. Status kiri pakai ellipsis.
2. **Banner** ≤ 120px tinggi, `object-position` biar bagian penting (pondok + lentera) kelihatan.
   Kalau kepotong aneh di 360px, turunkan aspek jadi 1000/240.
3. **Orb/maskot**: 120–140px, lingkaran penuh, wajah maskot TIDAK kepotong
   (`object-position: 50% 38%`). Cek 4 state: idle, listening (ring hijau), thinking
   (ring amber putus-putus), speaking (naik-turun halus).
4. **Baris mode chip** (Companion/Tutor/Work/Story): 1 baris, `nowrap`, tidak pecah.
5. **Kartu quick action**: gambar semua sama tinggi; kartu lebar (Bedtime story) gambar
   16:7 di atas, teks di bawah — jangan ada gambar yang melar mengikuti tinggi teks.
   Di 360px grid jadi 1 kolom.
6. **Sheet (Quick actions / Settings / Diagnostics)**: header sticky, grup berupa kartu
   krem dengan border kayu, jarak antar grup 12px, isi tidak mepet tepi (padding 12–14px),
   footer sticky dengan tombol Done.
7. **Form**: input/select tinggi 38–44px, label uppercase kecil, hint 11.5px; semua
   kontrol punya state focus/hover/active/disabled yang jelas.
8. **Balon jawaban**: max-height 42dvh + scroll sendiri, ekor menempel ke arah orb,
   jangan menutupi composer.
9. **Composer**: input + 2 tombol bulat, aman dari keyboard HP (`env(safe-area-inset-bottom)`).
10. **Konsistensi**: satu skala spacing (4/8/12/16/24), satu radius set (8/10/14/999),
    satu set shadow, tidak ada nilai acak.
11. **Motion**: transisi 0.15–0.24s, hormati `prefers-reduced-motion`.
12. **Kosong/edge case**: daftar reminder/jurnal/catatan kosong harus punya empty state
    bergambar/teks ramah, bukan ruang kosong.

## CARA VERIFIKASI (wajib, jangan skip)

```bash
# 1. ukur geometri (tanpa browser): header, banner, orb, composer, elemen luber
python3 scripts/layout_check.py

# 2. tes UI di jsdom (kontrak JS tetap utuh)
node scripts/ui_v9_test.cjs      # quick actions, settings, persona, notes, usage
node scripts/ui_v8_test.cjs      # jeda antar potongan TTS ~0
node scripts/demo_test.cjs       # versi demo (mock API) tanpa error

# 3. smoke backend (jangan sampai rusak gara-gara HTML/CSS)
python3 scripts/smoke_py.py      # harus 13 lolos, 0 gagal
```

Target angka: `header ≤ 56`, `banner ≤ 120`, `orb 120–140`, `luber: tidak ada`,
`scrollWidth == viewport`, `js_errors: []`.

Kalau kamu punya akses browser: screenshot 390×844 untuk keadaan idle, listening,
dan sheet Quick actions terbuka — lampirkan di laporan.

## CARA DEPLOY (setelah desain beres)

```bash
cd /root/kosmate
# 1) sinkron ke demo + bangun single.html (semua inline: css/js/gambar base64)
cp web/style.css web/app.js web/extras.js web/index.html web/manifest.json web/sw.js demo/
cp -r web/assets/. demo/assets/
python3 scripts/_fix_demo_index.py     # menambahkan <script src="demo.js"> + judul demo
python3 scripts/build_single.py        # hasil: demo/single.html (nol request eksternal)

# 2) commit + push repo utama
git add -A && git -c user.name="ZieeRoute" -c user.email="zieeroute@users.noreply.github.com" \
  commit -m "design: <ringkasan>" && git push origin main

# 3) commit + push demo (GitHub Pages auto-build)
cd demo && git add -A && git -c user.name="ZieeRoute" -c user.email="zieeroute@users.noreply.github.com" \
  commit -m "sync demo" && git push origin main

# 4) verifikasi live (tunggu ±45 detik build Pages)
python3 - <<'PY'
import urllib.request
b="https://xiaochown.github.io/companion-demo"
for f in ("/", "/style.css", "/app.js", "/single.html", "/assets/mascot.webp", "/assets/banner.webp"):
    r=urllib.request.urlopen(b+f,timeout=25); print(f, r.status, len(r.read()))
PY
```

PENTING: `demo/index.html` HARUS punya `<script src="demo.js"></script>` sebelum
`app.js`. Kalau tidak, demo akan memanggil API asli dan tampil kosong.

## FORMAT LAPORAN (akhir tugas)

1. Apa yang diubah (poin, bukan cerita).
2. Angka sebelum → sesudah: tinggi header, tinggi banner, ukuran orb, jumlah elemen luber.
3. Hasil `layout_check.py`, `ui_v9_test.cjs`, `smoke_py.py`.
4. URL demo + `single.html` yang sudah diverifikasi 200.
5. Kalau ada yang belum beres / gak bisa diverifikasi, tulis jujur + alasannya.
