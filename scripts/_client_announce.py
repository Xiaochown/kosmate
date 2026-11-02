"""Klien: polling 20s diganti antrean ucapan server + jeda ngomong lebih sabar."""
import pathlib

e = pathlib.Path("/root/kosmate/web/extras.js")
s = e.read_text()

# 1) fungsi cekAnnounce (menggantikan cekPengingat untuk detak rutin)
if "function cekAnnounce" not in s:
    s = s.replace(
        "function cekPengingat() {",
        '''/* Server sudah mengirim notifikasi Android sendiri; klien cuma mengambil
   kalimat yang tertinggal untuk diucapkan. Tidak ada polling berat. */
function cekAnnounce() {
  if (document.visibilityState !== "visible") return;  // hemat baterai
  api("/api/announce")
    .then((j) => {
      const items = j.items || [];
      if (!items.length) return;
      items.forEach((a, i) => {
        const kalimat = (a.kind === "reminder" ? "Pengingat: " : "") + a.teks;
        setTimeout(() => enqueueSpeech(kalimat), i * 400);
      });
      setStatus("Pengingat: " + esc(items[items.length - 1].teks));
      muatPengingat();
    })
    .catch(() => {});
}

function cekPengingat() {''',
    )

# 2) ganti interval polling reminders -> announce
s = s.replace("setInterval(cekPengingat, 20000);",
              'setInterval(cekAnnounce, 15000);\n  setTimeout(cekAnnounce, 2500);')
e.write_text(s)

# 3) jeda ngomong lebih sabar (masalah "keburu nyimpulin")
a = pathlib.Path("/root/kosmate/web/app.js")
t = a.read_text()
t = t.replace("silenceMs: 900,", "silenceMs: 2200,")
t = t.replace("cooldownMs: 900,", "cooldownMs: 1200,")
t = t.replace("Number(s.silenceMs || 900)", "Number(s.silenceMs || 2200)")
t = t.replace("Number(s.cooldownMs || 900)", "Number(s.cooldownMs || 1200)")
a.write_text(t)

print("cekAnnounce:", "function cekAnnounce" in s)
print("interval announce:", "setInterval(cekAnnounce, 15000)" in s)
print("silence 2200:", "silenceMs: 2200" in t)
