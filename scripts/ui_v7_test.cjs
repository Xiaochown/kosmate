// Uji pemotongan teks TTS: satu blok utuh (bukan per kalimat).
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

const ttsCalls = [];
window.fetch = async (url, opts = {}) => {
  const j = (o) => ({ ok: true, status: 200, json: async () => o, text: async () => "{}", blob: async () => ({ size: 30000 }) });
  if (url.endsWith("/api/tts")) {
    const body = JSON.parse(opts.body || "{}");
    ttsCalls.push(body.text || "");
    return j({});
  }
  if (url.endsWith("/api/health")) return j({ ok: true, name: "Kai", llm_key: true, fish_key: true, tts_voice: "x", tts_rate: "-20%", voice: { key: "miyaa", label: "Miyaa", engine: "fish", rate: "-20%" }, memory: { facts: 0 } });
  if (url.endsWith("/api/greeting")) return j({ text: "" });
  if (url.endsWith("/api/voice")) return j({ active: { key: "miyaa", label: "Miyaa", engine: "fish", rate: "-20%" }, options: [], fish_key: true });
  return j({});
};
window.URL.createObjectURL = () => "blob:x";
window.URL.revokeObjectURL = () => {};
window.Audio = class { play() { setTimeout(() => this.onended && this.onended(), 5); return Promise.resolve(); } pause() {} };
window.webkitSpeechRecognition = class { start() {} stop() {} abort() {} };
window.speechSynthesis = { getVoices: () => [], speak: () => {}, cancel: () => {} };
window.SpeechSynthesisUtterance = class {};
window.localStorage.clear();
Object.defineProperty(window.navigator, "wakeLock", { value: { request: async () => ({}) }, configurable: true });
Object.defineProperty(window.navigator, "mediaDevices", { value: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) }, configurable: true });

let evalErr = null;
try { window.eval(fs.readFileSync(WEB + "/app.js", "utf8")); } catch (e) { evalErr = e.message; }

(async () => {
  await wait(300);
  const S = window.__S;
  const doc = window.document;
  const out = { eval_error: evalErr, js_errors: errs, mode: S.speechChunk };

  // 1) balasan pendek: 3 kalimat, dikirim 5 potong
  const pendek = "Halo Faa. Hari ini gue santai banget. Mau ngobrol apa?";
  for (let i = 0; i < pendek.length; i += 12) window.feedDelta(pendek.slice(i, i + 12));
  out.tts_sebelum_done = ttsCalls.length;                     // harus 0
  const sisa = window.takeChunk(S.replyBuf || "", true).take;  // apa yang dikirim saat done
  out.panjang_sisa = sisa.length;
  out.kalimat_dalam_satu_blok = (sisa.match(/[.!?]/g) || []).length; // harus 3

  // 2) balasan panjang: 1200 karakter -> harus pecah, tapi tidak per kalimat
  ttsCalls.length = 0;
  S.replyBuf = "";
  S.replyText = "";
  const kalimat = "Ini kalimat contoh yang lumayan panjang untuk menguji pemotongan teks pada mode satu blok. ";
  const panjang = kalimat.repeat(12);
  for (let i = 0; i < panjang.length; i += 20) window.feedDelta(panjang.slice(i, i + 20));
  await wait(300);
  const sisaPanjang = window.takeChunk(S.replyBuf || "", true).take;
  if (sisaPanjang.trim().length >= 3) {
    window.enqueueSpeech(sisaPanjang);
    await wait(200);
  }
  out.total_karakter = panjang.length;
  out.tts_potongan = ttsCalls.length;
  out.panjang_tiap_potongan = ttsCalls.map((t) => t.length);
  out.avg_kalimat_per_potongan = ttsCalls.map((t) => (t.match(/[.!?]/g) || []).length);

  // 3) mode per kalimat masih bisa dipilih
  ttsCalls.length = 0;
  S.speechChunk = "sentence";
  S.replyBuf = "";
  window.feedDelta("Satu. Dua. Tiga.");
  await wait(50);
  out.mode_kalimat_potongan = ttsCalls.length; // 2 (kalimat terakhir nunggu flush)

  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
})();
