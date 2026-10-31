import pathlib
import re

p = pathlib.Path("/root/kosmate/web/app.js")
t = p.read_text()

# UI chrome -> English (teks yang diucapkan tetap Bahasa Indonesia)
MAP = {
    # status state
    '"santai… ketuk orb buat ngobrol"': '"Tap to talk"',
    'idle: "santai… ketuk orb buat ngobrol",': 'idle: "Tap to talk",',
    'listening: "gue dengerin…",': 'listening: "Listening…",',
    'thinking: "mikir sebentar…",': 'thinking: "Thinking…",',
    'speaking: "lagi ngomong…",': 'speaking: "Speaking…",',
    # reply label
    '"lu: " + S.youSaid': '"You: " + S.youSaid',
    # mic / stt errors
    'setStatus("browser ini gak dukung STT — buka di Chrome (bukan Fully Kiosk)")':
        'setStatus("This browser has no speech recognition — open in Chrome")',
    '"izin mic ditolak. Buka <strong>chrome://settings</strong> → Site settings → Microphone"':
        '"Microphone blocked. Open <strong>chrome://settings</strong> → Site settings → Microphone"',
    '"mic dipakai app lain"': '"Microphone is used by another app"',
    '"koneksi STT putus — coba lagi"': '"Speech service unreachable — retrying"',
    # statuses
    '"ketuk orb buat mulai ngobrol"': '"Tap to talk"',
    '"isi API key dulu di file .env"': '"Add your API key in .env first"',
    '"dipotong. ketuk lagi kalau mau ngomong"': '"Stopped. Tap again to talk"',
    '"suara gak keluar — buka ⚙ → Diagnostik"': '"No audio — check Settings → Diagnostics"',
    # voice picker
    '"Fish Audio siap. Pilih salah satu — kalau Fish gagal, Kosmate <b>diam</b>, tidak ganti suara lain."':
        '"Fish Audio ready. Pick one — if it fails, it stays <b>silent</b> instead of switching voice."',
    '"FISH_API_KEY belum diisi di .env — voice Fish belum bisa dipakai. Isi dulu, lalu muat ulang halaman."':
        '"FISH_API_KEY is missing in .env — Fish voices are unavailable. Add it, then reload."',
    '"suara: <strong>" + j.active.label + "</strong> · " + j.active.rate':
        '"Voice: <strong>" + j.active.label + "</strong> · " + j.active.rate',
    '"gagal ganti suara: " + e.message': '"Could not change voice: " + e.message',
    # misc statuses
    '"jeda dengerin: <strong>" + n + " ms</strong> (" + (n / 1000).toFixed(1) + " detik)"':
        '"Silence wait: <strong>" + n + " ms</strong> (" + (n / 1000).toFixed(1) + "s)"',
    '"mode <strong>" + b.dataset.mode + "</strong> aktif"': '"Mode: <strong>" + b.dataset.mode + "</strong>"',
    'setStatus("jawaban kena batas token — naikin <code>LLM_MAX_TOKENS</code> di .env")':
        'setStatus("Reply hit the token limit — raise <code>LLM_MAX_TOKENS</code> in .env")',
    # diag rows
    '["Suara dipakai",': '["Voice",',
    '["Cadangan suara HP", S.browserFallback ? "aktif (bisa ganti timbre kalau server gagal)" : "mati (suara tetap satu)", true]':
        '["Device fallback", S.browserFallback ? "on (timbre may change if the server fails)" : "off (single voice)", true]',
    '["STT (Web Speech)", hasSR ? "ada" : "TIDAK ADA → pakai Chrome, bukan Fully Kiosk", hasSR]':
        '["Speech recognition", hasSR ? "available" : "MISSING — use Chrome, not a WebView", hasSR]',
    '["TTS server", S.diag.tts || "belum dites",': '["TTS server", S.diag.tts || "not tested",',
    '"ada · " + nVoices + " suara" + (idVoice ? " · " + idVoice.name : " · (voice id-ID gak ketemu)") : "TIDAK ADA"':
        '"available · " + nVoices + " voices" + (idVoice ? " · " + idVoice.name : " · (no Indonesian voice)") : "MISSING"',
    '["Bicara otomatis", S.speakReply ? "aktif" : "nonaktif", S.speakReply]':
        '["Speak replies", S.speakReply ? "on" : "off", S.speakReply]',
    '["Dengerin otomatis", S.autoListen ? "aktif" : "nonaktif", S.autoListen]':
        '["Auto listen", S.autoListen ? "on" : "off", S.autoListen]',
    '["Log terakhir STT", S.diag.stt || "-",': '["Last speech log", S.diag.stt || "-",',
    '["Mic (tes manual)", S.diag.mic || "belum dites", S.diag.mic === "akses OK"]':
        '["Mic test", S.diag.mic || "not tested", S.diag.mic === "akses OK"]',
    '"modul" ': '"module" ',
    '"akses OK"': '"access OK"',
    '"akses ditolak: "': '"access denied: "',
    '"branch" ': '"branch" ',
    'memStats.textContent = facts.length + " fakta"': 'memStats.textContent = facts.length + " facts"',
    'memCount").textContent = h.memory.facts + " fakta"': 'memCount").textContent = h.memory.facts + " facts"',
    'memCount").textContent = evt.memory.facts + " fakta"': 'memCount").textContent = evt.memory.facts + " facts"',
    'setStatus("gagal muat daftar suara: "': 'setStatus("Could not load voices: "',
    'diag("tts", "gagal muat daftar suara: "': 'diag("tts", "voice list failed: "',
}

hits = 0
for a, b in MAP.items():
    if a in t:
        t = t.replace(a, b)
        hits += 1
    else:
        print("LEWAT (tidak ketemu):", a[:70])
p.write_text(t)
print(f"\n{hits}/{len(MAP)} string diterjemahkan")
sisa = re.findall(r'"[^"\n]*(?:dengerin|ngomong|ketuk|dipotong|belum dites)[^"\n]*"', t)
print("sisa string ID:", sisa[:6])
