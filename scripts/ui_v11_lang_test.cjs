// Uji Sprint B: bahasa ID/EN, ukuran tampilan, konfirmasi hapus
const { JSDOM, VirtualConsole } = require("/tmp/uitest/node_modules/jsdom");
const fs = require("fs");
const WEB = "/root/kosmate/web";

const errs = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errs.push(String(e.message).slice(0, 140)));

const html = fs.readFileSync(WEB + "/index.html", "utf8").replace(/<script src="[^"]*"><\/script>/g, "");
const dom = new JSDOM(html, { runScripts: "dangerously", url: "http://127.0.0.1:8080/", virtualConsole: vc });
const { window } = dom;
const doc = window.document;
const store = {};
Object.defineProperty(window, "localStorage", {
  value: { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: (k) => { delete store[k]; } },
  configurable: true,
});
window.fetch = async () => ({ ok: true, status: 200, json: async () => ({ values: {}, skema: { fields: {}, teks: {} }, items: [], options: [], active: {} }), text: async () => "{}", blob: async () => ({ size: 30000 }) });
window.Audio = class { play() { setTimeout(() => this.onended && this.onended(), 5); return Promise.resolve(); } pause() {} };
window.confirm = () => true;

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const semua = ["app.js", "extras.js", "wake.js", "i18n.js"].map((f) => fs.readFileSync(`${WEB}/${f}`, "utf8")).join("\n;\n")
    + "\n;window.EX = EX; window.bolehHapus = bolehHapus;";  // jsdom: eval terpisah tidak lihat const
  window.eval(semua);
  await wait(1500);

  const out = { js_errors: errs };
  const judul = () => [...doc.querySelectorAll(".group-title")].map((e) => e.textContent.trim());

  out.sebelum = judul().slice(0, 4);
  window.EX.setLang("id");
  await wait(200);
  out.sesudah_id = judul().slice(0, 4);
  out.nav_id = doc.querySelector("#actBtn .lbl").textContent;
  out.chip_id = doc.querySelector('.mode-chip[data-mode="teman"], .mode-chip[data-mode="temen"]').textContent;
  out.status_id = doc.getElementById("status").textContent;
  out.tersimpan_lang = store["kosmate.lang"];

  window.EX.setLang("en");
  await wait(200);
  out.sesudah_en = judul().slice(0, 4);
  out.nav_en = doc.querySelector("#actBtn .lbl").textContent;

  // zoom
  window.EX.setZoom(1.2);
  await wait(150);
  out.zoom_app = doc.querySelector(".app").style.zoom;
  out.zoom_tersimpan = store["kosmate.zoom"];

  // konfirmasi hapus tersedia global
  out.bolehHapus_ada = typeof window.bolehHapus === "function";
  out.confirm_default_on = store["kosmate.confirm"] !== "0";

  console.log(JSON.stringify(out, null, 2));
  try { window.close(); } catch (e) {}
  process.exit(0);
})().catch((e) => { console.log("GAGAL:", e.message); process.exit(1); });
