// Uji UI v0.2: fallback suara browser, auto-listen, panel diagnosa.
// jsdom tidak punya SpeechRecognition/speechSynthesis/Audio asli -> distub.
const { JSDOM, VirtualConsole } = require("/tmp/uitest/node_modules/jsdom");
const fs = require("fs");

const WEB = "/root/kosmate/web";
const html = fs.readFileSync(WEB + "/index.html", "utf8");
const js = fs.readFileSync(WEB + "/app.js", "utf8");

const events = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => events.push({ jsdomError: e.message }));

const dom = new JSDOM(html, { runScripts: "outside-only", virtualConsole: vc, url: "http://127.0.0.1:8080/" });
const { window } = dom;

// ---- stub jaringan ----
window.fetch = async (url) => {
  const j = (o) => ({ ok: true, status: 200, json: async () => o, text: async () => JSON.stringify(o), blob: async () => ({ size: 33000 }) });
  if (url.endsWith("/api/health")) return j({ ok: true, name: "Kai", llm: "x", llm_key: true, tts_providers: ["edge"], memory: { facts: 3 } });
  if (url.endsWith("/api/greeting")) return j({ text: "Hai Faa." });
  if (url.endsWith("/api/tts")) return j({});
  return j({ ok: true });
};

// ---- stub audio ----
let playedBlobs = 0;
window.URL.createObjectURL = () => "blob:x";
window.URL.revokeObjectURL = () => {};
window.Audio = class {
  constructor() { this.src = ""; }
  play() { playedBlobs++; setTimeout(() => this.onended && this.onended(), 5); return Promise.resolve(); }
  pause() {}
};

// ---- stub SpeechRecognition (Chrome Android) ----
let recStarts = 0;
window.webkitSpeechRecognition = class {
  constructor() { this.lang = ""; this.continuous = false; this.interimResults = false; }
  start() { recStarts++; setTimeout(() => this.onstart && this.onstart(), 1); }
  stop() { setTimeout(() => this.onend && this.onend(), 1); }
  abort() { setTimeout(() => this.onend && this.onend(), 1); }
};

// ---- stub speechSynthesis ----
let ssSpeaks = 0;
window.speechSynthesis = {
  getVoices: () => [{ name: "Google Bahasa Indonesia", lang: "id-ID" }],
  speak: (u) => { ssSpeaks++; setTimeout(() => u.onend && u.onend(), 5); },
  cancel: () => {},
};
window.SpeechSynthesisUtterance = class { constructor(t) { this.text = t; } };

window.localStorage.clear();
Object.defineProperty(window.navigator, "wakeLock", { value: { request: async () => ({}) }, configurable: true });
Object.defineProperty(window.navigator, "mediaDevices", { value: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) }, configurable: true });

let evalErr = null;
try { window.eval(js); } catch (e) { evalErr = e.message; }

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  await wait(300);
  const doc = window.document;
  const out = { eval_error: evalErr, js_errors: events.filter((e) => e.jsdomError) };

  // 1. panel diagnosa bisa dibuka & punya isi
  doc.getElementById("diagBtn").click();
  await wait(100);
  out.diag_open = doc.getElementById("diagSheet").classList.contains("open");
  out.diag_rows = doc.querySelectorAll("#diagBox .fact").length;
  out.diag_has_stt_ok = doc.getElementById("diagBox").textContent.includes("ada");

  // 2. tes suara -> harus mainkan audio dari server (fallback browser kalau gagal)
  doc.getElementById("diagTtsTest").click();
  await wait(400);
  out.tts_played_blobs = playedBlobs;

  // 3. auto-listen: toggle harus LANGSUNG mulai mendengar (dulu tidak)
  const before = recStarts;
  doc.getElementById("setAutoListen").click();
  await wait(300);
  out.rec_starts_after_toggle = recStarts - before;

  // 4. heartbeat: pendengar dimatikan paksa -> dalam ~3.5s harus nyala sendiri
  if (typeof window.stopRecognition === "function") window.stopRecognition(true);
  const before2 = recStarts;
  await wait(3800);
  out.rec_starts_heartbeat = recStarts - before2;

  // 5. server TTS gagal -> harus jatuh ke suara bawaan HP (speechSynthesis)
  window.fetch = async (url) => {
    if (url.endsWith("/api/tts")) throw new Error("network down");
    return { ok: true, status: 200, json: async () => ({ ok: true }), text: async () => "{}", blob: async () => ({ size: 10 }) };
  };
  const ssBefore = ssSpeaks;
  if (typeof window.runTtsTest === "function") window.runTtsTest();
  await wait(500);
  out.fallback_browser_spoken = ssSpeaks - ssBefore;

  out.tts_mode_default = doc.getElementById("setTtsMode").value;
  out.footer_version = doc.body.textContent.includes("v0.1") ? "v0.1" : "lain";

  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
})();
