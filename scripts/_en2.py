import pathlib

p = pathlib.Path("/root/kosmate/web/app.js")
t = p.read_text()

MAP = [
    ('"izin mic ditolak. Chrome → Site settings → Microphone → izinkan 127.0.0.1"',
     '"Microphone blocked. Chrome → Site settings → Microphone → allow 127.0.0.1"'),
    ('"mic dipakai app lain? tutup app yang pakai mic"',
     '"Microphone busy? Close the app using it"'),
    ('"gak kedengeran, coba lagi"', '"Didn\'t catch that, try again"'),
    ('"gagal transkripsi: "', '"Transcription failed: "'),
    ('"ngerekam… ketuk mic lagi buat kirim"', '"Recording… tap mic again to send"'),
    ('"mic gak bisa diakses: "', '"Mic unavailable: "'),
    ('"auto-dengerin butuh Chrome (browser ini gak punya STT)"',
     '"Auto listen needs Chrome (no speech recognition here)"'),
    ('"belum tahu"', '"unknown"'),
    ('" · tempo "', '" · speed "'),
    ('"Fakta yang Kosmate ingat tentang kamu. Hapus yang salah — dia langsung lupa."',
     '"Facts remembered about you. Delete a wrong one and it forgets immediately."'),
    ('facts.length + " fakta"', 'facts.length + " facts"'),
    ("'<div class=\"tiny\">gagal memuat memori</div>'",
     "'<div class=\"tiny\">Could not load memory</div>'"),
    ('"rekam lalu kirim (STT server)"', '"record and send (server STT)"'),
    ('(h.memory ? h.memory.facts : 0) + " fakta"', '(h.memory ? h.memory.facts : 0) + " facts"'),
    ('"auto-dengerin dinyalakan"', '"auto listen enabled"'),
    ('"dipotong. ketuk lagi kalau mau ngomong"', '"Stopped. Tap again to talk"'),
    ('"suara gak keluar — buka ⚙ → Diagnostik"', '"No audio — open Settings → Diagnostics"'),
    ('"Ketuk orb buat ngobrol"', '"Tap to talk"'),
]

n = 0
for a, b in MAP:
    if a in t:
        t = t.replace(a, b)
        n += 1
    else:
        print("lewat:", a[:64])
p.write_text(t)
print(f"{n}/{len(MAP)} diganti")
