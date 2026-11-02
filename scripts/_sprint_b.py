"""Tambah grup 'Tampilan & Bahasa' + konfirmasi hapus."""
import pathlib
import re

# --- HTML: grup baru sebelum Personality ---
h = pathlib.Path("/root/kosmate/web/index.html")
s = h.read_text()
if 'id="setLang"' not in s:
    grup = '''      <section class="group">
        <h3 class="group-title">Tampilan &amp; Bahasa</h3>
        <div class="field">
          <label for="setLang">Bahasa</label>
          <select id="setLang">
            <option value="id">Indonesia (mudah)</option>
            <option value="en">English</option>
          </select>
          <p class="tiny">Bahasa Indonesia menyembunyikan istilah teknis.</p>
        </div>
        <div class="field">
          <label for="setZoom">Ukuran tampilan</label>
          <select id="setZoom">
            <option value="0.95">Kecil · 95%</option>
            <option value="1">Sedang · 100%</option>
            <option value="1.1">Besar · 110%</option>
            <option value="1.2">Sangat besar · 120%</option>
          </select>
        </div>
        <div class="row">
          <span class="row-label">Tanya dulu sebelum hapus<small>biar gak kepencet dan data hilang</small></span>
          <button class="switch on" id="setConfirm" type="button"><span class="dot ok"></span>on</button>
        </div>
      </section>

'''
    s = s.replace('      <section class="group">\n        <h3 class="group-title">Personality</h3>',
                  grup + '      <section class="group">\n        <h3 class="group-title">Personality</h3>')
    # script i18n
    if "i18n.js" not in s:
        s = s.replace('<script src="wake.js?v=2"></script>',
                      '<script src="wake.js?v=2"></script>\n  <script src="i18n.js?v=2"></script>')
    h.write_text(s)

# --- extras.js: binding + konfirmasi hapus ---
e = pathlib.Path("/root/kosmate/web/extras.js")
t = e.read_text()

if 'on("setLang"' not in t:
    t = t.replace(
        '  // wake word (logikanya di wake.js)',
        '''  // bahasa, ukuran tampilan, konfirmasi hapus
  const selLang = $x("setLang");
  if (selLang) {
    selLang.value = (EX.lang && EX.lang()) || "id";
    selLang.onchange = () => EX.setLang(selLang.value);
  }
  const selZoom = $x("setZoom");
  if (selZoom) {
    selZoom.value = String((EX.zoom && EX.zoom()) || 1);
    selZoom.onchange = () => EX.setZoom(selZoom.value);
  }
  const btnConf = $x("setConfirm");
  if (btnConf) {
    let on = localStorage.getItem("kosmate.confirm") !== "0";
    const lukis = () => {
      btnConf.classList.toggle("on", on);
      btnConf.innerHTML = '<span class="dot' + (on ? " ok" : "") + '"></span>' + (on ? "on" : "off");
    };
    lukis();
    btnConf.onclick = () => {
      on = !on;
      localStorage.setItem("kosmate.confirm", on ? "1" : "0");
      lukis();
    };
  }

  // wake word (logikanya di wake.js)''',
    )

# fungsi konfirmasi global
if "function bolehHapus" not in t:
    t = t.replace(
        "function esc(s) {",
        '''/* dipakai semua tombol hapus: Bu Sari takut salah pencet */
function bolehHapus(apa) {
  if (localStorage.getItem("kosmate.confirm") === "0") return true;
  return confirm("Hapus " + apa + "? Ini tidak bisa dibatalkan.");
}

function esc(s) {''',
    )
e.write_text(t)

print("setLang di html:", "setLang" in s)
print("i18n.js disisipkan:", "i18n.js" in s)
print("bolehHapus:", "function bolehHapus" in t)
