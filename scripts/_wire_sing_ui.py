"""Kartu 'Nyanyi' di Menu Cepat + logika pemutaran."""
import pathlib
import re

h = pathlib.Path("/root/kosmate/web/index.html")
s = h.read_text()

if 'id="singGo"' not in s:
    kartu = '''        <article class="card wide">
          <figure class="card-media"><img src="assets/sing.webp" alt=""></figure>
          <div class="card-body">
            <h3>Nyanyi</h3>
            <p>Tulis lirik, pilih lagu. Kai nyanyi ngikutin nada lagunya.</p>
            <input id="singLirik" type="text" placeholder="pelangi pelangi alangkah indahmu">
            <div class="chips">
              <select id="singLagu" class="chip" style="height:auto;padding:4px 8px"></select>
            </div>
            <div class="chips">
              <button class="chip" id="singGo" type="button">Nyanyi</button>
              <button class="chip" id="singStop" type="button" hidden>Stop</button>
            </div>
          </div>
        </article>

'''
    s = s.replace('        <article class="card">\n          <figure class="card-media"><img src="assets/remind.webp" alt=""></figure>',
                  kartu + '        <article class="card">\n          <figure class="card-media"><img src="assets/remind.webp" alt=""></figure>')
    h.write_text(s)

e = pathlib.Path("/root/kosmate/web/extras.js")
t = e.read_text()

if "function nyanyiSekarang" not in t:
    blok = '''
/* ---------------------- mode nyanyi ---------------------- */
let singAudio = null;

function muatLagu() {
  const sel = $x("singLagu");
  if (!sel) return;
  api("/api/sing/songs")
    .then((j) => {
      sel.innerHTML = (j.items || [])
        .map((l) => '<option value="' + l.kunci + '">' + esc(l.judul) + "</option>")
        .join("");
    })
    .catch(() => {});
}

async function nyanyiSekarang() {
  const lirik = ($x("singLirik").value || "").trim();
  const lagu = ($x("singLagu") && $x("singLagu").value) || "pelangi";
  if (!lirik) {
    setStatus("Tulis liriknya dulu");
    return;
  }
  setStatus("Nyanyi… (" + lirik.split(/\\s+/).length + " kata)");
  try {
    const res = await fetch("/api/sing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lirik, lagu }),
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      throw new Error(e.detail || e.error || ("HTTP " + res.status));
    }
    const blob = await res.blob();
    if (!blob || blob.size < 2000) throw new Error("audio kosong");
    hentikanNyanyi();
    singAudio = new Audio(URL.createObjectURL(blob));
    singAudio.onended = () => setStatus("Selesai nyanyi");
    $x("singStop").hidden = false;
    await singAudio.play();
    setStatus("Nyanyi…");
  } catch (e) {
    setStatus("Gagal nyanyi: " + e.message);
  }
}

function hentikanNyanyi() {
  if (singAudio) {
    try { singAudio.pause(); } catch (e) {}
    singAudio = null;
  }
  const b = $x("singStop");
  if (b) b.hidden = true;
}

'''
    t = t.replace("/* ---------------------- briefing pagi ---------------------- */",
                  blok + "/* ---------------------- briefing pagi ---------------------- */")
    t = t.replace('  on("diagBtn"',
                  '  on("singGo", nyanyiSekarang);\n  on("singStop", hentikanNyanyi);\n  muatLagu();\n  on("diagBtn"', 1)
    e.write_text(t)

print("kartu sing:", "singGo" in s)
print("logika sing:", "function nyanyiSekarang" in t)
