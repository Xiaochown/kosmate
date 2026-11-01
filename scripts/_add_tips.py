"""Isi kartu petunjuk beranda: berguna (bukan hiasan) dan berganti-ganti."""
import pathlib

a = pathlib.Path("/root/kosmate/web/app.js")
s = a.read_text()

if "function pasangTip" not in s:
    blok = '''
/* ---------------- tip di beranda ---------------- */
const TIPS = [
  "Ketik atau ketuk maskot buat ngobrol. Kalau lagi males ngomong, tinggal tulis aja.",
  "Mau cerita pengantar tidur? Buka <b>Actions</b> → Bedtime story, Kai bakal cerita sampai kamu tidur.",
  "Bilang \\"ingetin gue 15 menit lagi\\" — Kai bakal nyebut langsung di waktunya.",
  "Klik <b>Memory</b> buat lihat apa aja yang Kai inget. Hapus satu, dia langsung lupa.",
  "Upload catatan kuliah di <b>Settings → Notes</b>, terus minta \\"kuis gue soal ini\\".",
  "Mode <b>Tutor</b> bikin jawaban lebih jelas dan sabar. Mode <b>Work</b> lebih ringkas.",
  "Kalau suara kedengeran aneh, buka <b>Diagnostics</b> → Test voice.",
];
function pasangTip() {
  const el = $("tip");
  if (!el) return;
  const i = Math.floor(Math.random() * TIPS.length);
  el.innerHTML = "<b>Tip</b> · " + TIPS[i];
  el.style.display = "";
}
function sembunyiTip() {
  const el = $("tip");
  if (el) el.style.display = "none";
}
'''
    s = s.replace("function setStatus(html) {", blok + "\nfunction setStatus(html) {")

# panggil saat boot selesai
if "pasangTip();" not in s:
    s = s.replace("    updateVoiceChip();\n", "    updateVoiceChip();\n    pasangTip();\n", 1)

# sembunyikan tip saat sudah ada balasan
if "sembunyiTip()" not in s.split("function sembunyiTip")[0]:
    s = s.replace('  $("reply").classList.add("show");', '  $("reply").classList.add("show");\n  sembunyiTip();')

a.write_text(s)
print("pasangTip:", "function pasangTip" in s, "| dipanggil:", s.count("pasangTip();") )
