// Uji wake word "Hei Kai": toggle, deteksi, jeda saat mic dipakai, simpan setting.
const { JSDOM, VirtualConsole } = require("/tmp/uitest/node_modules/jsdom");
const fs = require("fs");
const WEB = "/root/kosmate/web";

const vc = new VirtualConsole();
const errs = [];
vc.on("jsdomError", (e) => errs.push(String(e.message).slice(0, 160)));

const html = fs.readFileSync(WEB + "/index.html", "utf8")
  .replace(/<script src="[^"]*"><\/script>/g, "")
  .replace('<link rel="manifest" href="manifest.json">', "");

const dom = new JSDOM(html, { runScripts: "dangerously", url: "http://127.0.0.1:8080/", virtualConsole: vc });
const { window } = dom;
const doc = window.document;

const store = {};
Object.defineProperty(window, "localStorage", {
  value: {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); },
    removeItem: (k) => { delete store[k]; },
  },
  configurable: true,
});

// --- SpeechRecognition palsu: bisa dikendalikan test ---
const instances = [];
class FakeSR {
  constructor() {
    this.started = 0; this.aborted = 0; this.lang = ""; this.continuous = false;
    this.onresult = null; this.onerror = null; this.onend = null; this.running = false;
    instances.push(this);
  }
  start() { this.started++; this.running = true; }
  abort() { this.aborted++; this.running = false; if (this.onend) this.onend({ error: "aborted" }); }
  stop() { this.running = false; }
  kirim(teks) { if (this.onresult) this.onresult({ resultIndex: 0, results: [[{ transcript: teks }]] }); }
}
window.SpeechRecognition = FakeSR;
window.webkitSpeechRecognition = FakeSR;

// --- fetch palsu ---
window.fetch = async (url, opts = {}) => {
  const j = (o) => ({ ok: true, status: 200, json: async () => o, text: async () => "{}", blob: async () => ({ size: 30000 }) });
  if (url.includes("/api/health")) return j({ llm: "x", llm_key: true, fish_key: true, voice: { label: "Miyaa" }, memory: { facts: 1, episodes: 1, notes: 0 }, tts_strict: true });
  if (url.includes("/api/voice")) return j({ active: { key: "miyaa", label: "Miyaa — perempuan", rate: "-20%" }, options: [{ key: "miyaa", label: "Miyaa — perempuan", rate: "-20%", ready: true }], fish_key: true });
  if (url.includes("/api/settings")) return j({ values: { max_tokens: 8000 }, skema: { fields: {}, teks: {} } });
  if (url.includes("/api/usage")) return j({ llm_tokens: 0, tts_chars: 0, tts_calls: 0 });
  if (url.includes("/api/reminders")) return j({ items: [] });
  if (url.includes("/api/journal")) return j({ items: [] });
  if (url.includes("/api/notes")) return j({ items: [] });
  if (url.includes("/api/memory")) return j({ facts: [] });
  if (url.includes("/api/greeting")) return j({ text: "" });
  if (url.includes("/api/tts")) return j({});
  return j({});
};
window.Audio = class {
  constructor() { this.duration = 1; }
  play() { setTimeout(() => this.onended && this.onended(), 5); return Promise.resolve(); }
  pause() {}
};

async function main() {
  const out = {};
  // digabung dalam satu eval supaya binding const (EX, S) terlihat antar file
  // (di browser asli, <script> terpisah berbagi global lexical scope)
  const semua = ["app.js", "extras.js", "wake.js"]
    .map((f) => fs.readFileSync(`${WEB}/${f}`, "utf8"))
    .join("\n;\n");
  window.eval(semua);
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  await wait(1600);

  out.js_errors = errs;

  // 1) toggle wake word on
  const btn = doc.getElementById("setWake");
  btn.click();
  await wait(300);
  out.toggle_on = btn.classList.contains("on");
  out.status_on = doc.getElementById("status").textContent.slice(0, 40);
  out.instances = instances.length;
  const wakeRec = instances[instances.length - 1];
  out.wake_started = wakeRec && wakeRec.started > 0;
  out.lang = wakeRec && wakeRec.lang;
  out.continuous = wakeRec && wakeRec.continuous;
  out.tersimpan = store["kosmate.wake"];

  // 2) ucapkan "hei kai" -> harus mulai listening
  wakeRec.kirim(" hei kai ");
  await wait(700);
  out.deteksi_memicu = doc.getElementById("status").textContent !== out.status_on;
  out.wake_aborted = wakeRec.aborted > 0;
  out.listening = doc.body.dataset.state === "listening";

  // 3) balik idle -> wake nyala lagi
  doc.dispatchEvent(new window.CustomEvent("kos:state", { detail: "idle" }));
  await wait(1200);
  const baru = instances.filter((i) => i.started > 0).length;
  out.wake_restart_setelah_idle = baru >= 2;

  // 4) matikan
  btn.click();
  await wait(200);
  out.toggle_off = !btn.classList.contains("on");
  out.tersimpan_off = store["kosmate.wake"];

  out.js_errors_akhir = errs;
  console.log(JSON.stringify(out, null, 2));
  try { window.close(); } catch (e) {}
  process.exit(0);
}

main().catch((e) => {
  console.log("GAGAL:", e.message); console.log(e.stack ? e.stack.split("\n").slice(0,6).join("\n") : "");
  process.exit(1);
});
