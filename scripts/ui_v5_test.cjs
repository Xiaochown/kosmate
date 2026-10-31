// Uji pemilih suara: 3 voice Fish + Gadis muncul, ganti voice -> tempo & fallback ikut.
const { JSDOM, VirtualConsole } = require("/tmp/uitest/node_modules/jsdom");
const fs = require("fs");

const WEB = "/root/kosmate/web";
const html = fs.readFileSync(WEB + "/index.html", "utf8");
const js = fs.readFileSync(WEB + "/app.js", "utf8");

const errs = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errs.push(e.message));
const dom = new JSDOM(html, { runScripts: "outside-only", virtualConsole: vc, url: "http://127.0.0.1:8080/" });
const { window } = dom;
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

const OPTIONS = [
  { key: "miyaa", label: "Miyaa — perempuan muda, ceria", engine: "fish", ref: "a", rate: "-20%", ready: true },
  { key: "kdm", label: "Kang Dedi — laki-laki, ceria, ekspresif", engine: "fish", ref: "b", rate: "-15%", ready: true },
  { key: "prabowo", label: "Prabowo — laki-laki, dalam, tegas", engine: "fish", ref: "c", rate: "-20%", ready: true },
  { key: "gadis", label: "Gadis — edge-tts (tanpa Fish)", engine: "edge", ref: "", rate: "-15%", ready: true },
];

const posts = [];
window.fetch = async (url, opts = {}) => {
  const j = (o) => ({ ok: true, status: 200, json: async () => o, text: async () => "{}", blob: async () => ({ size: 20000 }) });
  if (url.endsWith("/api/health"))
    return j({ ok: true, name: "Kai", llm_key: true, fish_key: true, fish_ref: true, tts_strict: true, tts_voice: "x", tts_rate: "-20%", voice: OPTIONS[0], memory: { facts: 2 } });
  if (url.endsWith("/api/greeting")) return j({ text: "" });
  if (url.endsWith("/api/voice")) {
    if ((opts.method || "GET") === "POST") {
      const key = JSON.parse(opts.body).key;
      posts.push(key);
      const act = OPTIONS.find((o) => o.key === key);
      return j({ active: act, options: OPTIONS });
    }
    return j({ active: OPTIONS[0], options: OPTIONS, fish_key: true });
  }
  return j({});
};

window.URL.createObjectURL = () => "blob:x";
window.URL.revokeObjectURL = () => {};
window.Audio = class { play() { setTimeout(() => this.onended && this.onended(), 5); return Promise.resolve(); } pause() {} };
window.webkitSpeechRecognition = class { start() { setTimeout(() => this.onstart && this.onstart(), 1); } stop() { setTimeout(() => this.onend && this.onend(), 1); } abort() {} };
window.speechSynthesis = { getVoices: () => [], speak: () => {}, cancel: () => {} };
window.SpeechSynthesisUtterance = class {};
window.localStorage.clear();
Object.defineProperty(window.navigator, "wakeLock", { value: { request: async () => ({}) }, configurable: true });
Object.defineProperty(window.navigator, "mediaDevices", { value: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) }, configurable: true });

let evalErr = null;
try { window.eval(js); } catch (e) { evalErr = e.message; }

(async () => {
  await wait(400);
  const doc = window.document;
  const S = window.__S;
  const sel = doc.getElementById("setVoice");
  const out = {
    eval_error: evalErr,
    js_errors: errs,
    jumlah_opsi: sel.options.length,
    opsi: Array.from(sel.options).map((o) => o.value),
    terpilih_awal: sel.value,
    note: doc.getElementById("voiceNote").textContent.slice(0, 60),
  };

  // ganti ke Kang Dedi
  sel.value = "kdm";
  sel.dispatchEvent(new window.Event("change"));
  await wait(400);
  out.post_key = posts[0];
  out.tempo_setelah_kdm = S.tempo;             // harus -15%
  out.fallback_setelah_kdm = S.browserFallback; // harus false (fish -> tanpa cadangan)
  out.terpilih_akhir = sel.value;

  // ganti ke Gadis (edge) -> tempo -15%, tetap tanpa fallback? (gadis = edge, fallback boleh)
  sel.value = "gadis";
  sel.dispatchEvent(new window.Event("change"));
  await wait(300);
  out.tempo_setelah_gadis = S.tempo;

  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
})();
