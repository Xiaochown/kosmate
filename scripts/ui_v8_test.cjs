// Uji pipeline prefetch: jeda antar potongan harus ~0 (tidak menunggu generate).
const { JSDOM, VirtualConsole } = require("/tmp/uitest/node_modules/jsdom");
const fs = require("fs");
const WEB = "/root/kosmate/web";
const errs = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errs.push(e.message));
const dom = new JSDOM(fs.readFileSync(WEB + "/index.html", "utf8"), {
  runScripts: "outside-only", virtualConsole: vc, url: "http://127.0.0.1:8080/",
});
const { window } = dom;
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

const TTS_DELAY = 400;   // server butuh 0.4s generate
const PLAY_MS = 800;     // tiap potongan diputar 0.8s

let inFlight = 0, maxInFlight = 0;
const events = [];       // {type:'start'|'end', t}
window.fetch = async (url) => {
  const j = (o) => ({ ok: true, status: 200, json: async () => o, text: async () => "{}", blob: async () => ({ size: 30000 }) });
  if (url.endsWith("/api/tts")) {
    inFlight++;
    maxInFlight = Math.max(maxInFlight, inFlight);
    await wait(TTS_DELAY);
    inFlight--;
    return j({});
  }
  if (url.endsWith("/api/health")) return j({ ok: true, name: "K", llm_key: true, fish_key: true, tts_voice: "x", tts_rate: "-20%", voice: { key: "miyaa", label: "Miyaa", engine: "fish", rate: "-20%" }, memory: { facts: 0 } });
  if (url.endsWith("/api/greeting")) return j({ text: "" });
  if (url.endsWith("/api/voice")) return j({ active: { key: "miyaa", label: "Miyaa", engine: "fish", rate: "-20%" }, options: [], fish_key: true });
  return j({});
};
window.URL.createObjectURL = () => "blob:x";
window.URL.revokeObjectURL = () => {};
window.Audio = class {
  constructor() { this.src = ""; }
  play() {
    events.push({ type: "start", t: Date.now() });
    setTimeout(() => { events.push({ type: "end", t: Date.now() }); this.onended && this.onended(); }, PLAY_MS);
    return Promise.resolve();
  }
  pause() {}
};
window.webkitSpeechRecognition = class { start() {} stop() {} abort() {} };
window.speechSynthesis = { getVoices: () => [], speak: () => {}, cancel: () => {} };
window.SpeechSynthesisUtterance = class {};
window.localStorage.clear();
Object.defineProperty(window.navigator, "wakeLock", { value: { request: async () => ({}) }, configurable: true });
Object.defineProperty(window.navigator, "mediaDevices", { value: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) }, configurable: true });

let evalErr = null;
try { window.eval(fs.readFileSync(WEB + "/app.js", "utf8")); } catch (e) { evalErr = e.message; }

(async () => {
  await wait(250);
  window.enqueueSpeech("Potongan satu.");
  window.enqueueSpeech("Potongan dua.");
  window.enqueueSpeech("Potongan tiga.");
  await wait(3600);

  const gaps = [];
  for (let i = 1; i < events.length; i++) {
    if (events[i].type === "start" && events[i - 1].type === "end") {
      gaps.push(events[i].t - events[i - 1].t);
    }
  }
  const out = {
    eval_error: evalErr,
    js_errors: errs,
    potongan_diputar: events.filter((e) => e.type === "start").length,
    request_paralel_maks: maxInFlight,
    jeda_antar_potongan_ms: gaps,
    jeda_terbesar_ms: gaps.length ? Math.max(...gaps) : null,
    tanpa_jeda: gaps.length ? Math.max(...gaps) < 120 : false,
  };
  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
})();
