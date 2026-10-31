// Uji v0.4 "anti potong": mic harus nunggu SEMUA kalimat selesai + jeda,
// lalu teks yang mirip suara sendiri harus diabaikan.
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

window.fetch = async (url) => {
  const j = (o) => ({ ok: true, status: 200, json: async () => o, text: async () => "{}", blob: async () => ({ size: 30000 }) });
  if (url.endsWith("/api/health")) return j({ ok: true, name: "Kai", llm_key: true, fish_key: true, fish_ref: true, tts_strict: true, tts_voice: "x", tts_rate: "-15%", memory: { facts: 1 } });
  if (url.endsWith("/api/greeting")) return j({ text: "" });
  return j({});
};

window.URL.createObjectURL = () => "blob:x";
window.URL.revokeObjectURL = () => {};
let plays = 0;
window.Audio = class {
  constructor() { this.src = ""; }
  play() { plays++; setTimeout(() => this.onended && this.onended(), 120); return Promise.resolve(); }
  pause() {}
};

let recStarts = 0, recAborts = 0;
window.webkitSpeechRecognition = class {
  start() { recStarts++; setTimeout(() => this.onstart && this.onstart(), 1); }
  stop() { setTimeout(() => this.onend && this.onend(), 1); }
  abort() { recAborts++; setTimeout(() => this.onend && this.onend(), 1); }
};
window.speechSynthesis = { getVoices: () => [], speak: () => {}, cancel: () => {} };
window.SpeechSynthesisUtterance = class {};
window.localStorage.clear();
Object.defineProperty(window.navigator, "wakeLock", { value: { request: async () => ({}) }, configurable: true });
Object.defineProperty(window.navigator, "mediaDevices", { value: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) }, configurable: true });

let evalErr = null;
try { window.eval(js); } catch (e) { evalErr = e.message; }

(async () => {
  await wait(250);
  const S = window.__S;
  const out = { eval_error: evalErr, js_errors: errs };

  S.autoListen = true;
  S.cooldownMs = 700;
  S.replyText = "Halo Faa, apa kabar? Hari ini gue siap bantu lu. Mau mulai dari mana?";

  const recBefore = recStarts;
  // tiga kalimat diucapkan berurutan (seperti jawaban 3 kalimat)
  window.enqueueSpeech("Halo Faa, apa kabar?");
  window.enqueueSpeech("Hari ini gue siap bantu lu.");
  window.enqueueSpeech("Mau mulai dari mana?");
  await wait(200);
  out.plays = plays;
  out.mic_hidup_saat_ngomong = recStarts - recBefore; // harus 0

  // tunggu semua kalimat + jeda 700ms
  await wait(1400);
  out.mic_hidup_setelah_selesai = recStarts - recBefore; // harus 1

  // tes deteksi gema: teks mirip yang baru diucapkan harus dianggap gema
  out.echo_1 = window.looksLikeEcho("halo faa apa kabar");
  out.echo_2 = window.looksLikeEcho("gue mau nanya soal tugas basis data");
  S.lastSpoken = "Halo Faa, apa kabar? Hari ini gue siap bantu lu.";
  out.echo_3 = window.looksLikeEcho("hari ini gue siap bantu lu");

  // tombol orb saat ngomong -> potong semua
  plays = 0;
  window.enqueueSpeech("Kalimat satu.");
  window.enqueueSpeech("Kalimat dua.");
  await wait(30);
  window.document.getElementById("orb").click();
  await wait(400);
  out.plays_setelah_dipotong = plays; // harus tidak nambah lagi

  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
})();
