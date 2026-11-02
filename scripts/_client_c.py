import pathlib
import re

e = pathlib.Path("/root/kosmate/web/extras.js")
t = e.read_text()

blok = '''
/* ---------------------- briefing pagi ---------------------- */
function briefingPagi() {
  const hari = new Date().toISOString().slice(0, 10);
  let terakhir = "";
  try { terakhir = localStorage.getItem("kosmate.brief") || ""; } catch (e) {}
  if (terakhir === hari) return;
  if (new Date().getHours() < 5) return;
  api("/api/briefing")
    .then((j) => {
      if (!j.ada || !j.teks) return;
      S.replyText = j.teks;
      S.youSaid = "";
      showReply();
      enqueueSpeech(j.teks);
      try { localStorage.setItem("kosmate.brief", hari); } catch (e) {}
      setStatus("Ringkasan pagi");
    })
    .catch(() => {});
}

/* ---------------------- metrik latency ---------------------- */
function tampilkanMetrik() {
  const box = $x("diagBox");
  if (!box) return;
  api("/api/metrics")
    .then((m) => {
      const urut = [
        ["llm_first_token", "LLM · token pertama"],
        ["llm_total", "LLM · total"],
        ["tts_first_byte", "Suara · potongan pertama"],
        ["tts_total", "Suara · total"],
        ["stt", "Dengar (STT)"],
      ];
      const baris = urut
        .filter(([k]) => m[k] && m[k].n)
        .map(([k, label]) => {
          const d = m[k];
          return '<div class="fact"><div><b>' + label + "</b><br><span style='color:#6b5136'>rata " +
            d.rata + " ms · p95 " + d.p95 + " ms · " + d.n + " sampel</span></div></div>";
        });
      if (!baris.length) {
        box.insertAdjacentHTML("beforeend",
          '<div class="fact"><div><b>Metrik</b><br><span style="color:#8c7351">belum ada sampel — coba ngobrol sekali</span></div></div>');
        return;
      }
      box.insertAdjacentHTML("beforeend",
        '<div class="fact"><div><b>Metrik latency</b><br><span style="color:#8c7351">makin kecil makin enak</span></div></div>' + baris.join(""));
    })
    .catch(() => {});
}

'''

if "function briefingPagi" not in t:
    m = re.search(r"/\* -+ JURNAL -+ \*/", t)
    if m:
        t = t[:m.start()] + blok + t[m.start():]
    else:
        t = t.replace("/* ------------------------------- util", blok + "/* ------------------------------- util")

if "setTimeout(briefingPagi" not in t:
    t = t.replace("  setInterval(cekAnnounce, 15000);",
                  "  setTimeout(briefingPagi, 3500);\n  setInterval(cekAnnounce, 15000);")

if 'on("diagBtn"' not in t:
    t = t.replace('  on("setWake"', '  on("diagBtn", () => setTimeout(tampilkanMetrik, 400));\n  on("setWake"', 1)

e.write_text(t)
print("briefing:", "function briefingPagi" in t)
print("metrik:", "function tampilkanMetrik" in t)
print("dipanggil:", "setTimeout(briefingPagi" in t, 'on("diagBtn"' in t)
