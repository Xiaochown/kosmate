// Uji UI baru: sheet Actions, kartu, personality, notes, usage, reminder, fokus.
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

const TTS = [];
const CALLS = [];
window.fetch = async (url, opts = {}) => {
  CALLS.push((opts.method || "GET") + " " + url.replace("http://127.0.0.1:8080", ""));
  const j = (o) => ({ ok: true, status: 200, json: async () => o, text: async () => "{}", blob: async () => ({ size: 30000 }) });
  if (url.endsWith("/api/tts")) { TTS.push((JSON.parse(opts.body || "{}").text) || ""); return j({}); }
  if (url.endsWith("/api/health"))
    return j({ ok: true, llm_key: true, fish_key: true, tts_voice: "x", tts_rate: "-20%", voice: { key: "miyaa", label: "Miyaa", engine: "fish", rate: "-20%" }, memory: { facts: 3 } });
  if (url.endsWith("/api/voice")) return j({ active: { key: "miyaa", label: "Miyaa", engine: "fish", rate: "-20%" }, options: [], fish_key: true });
  if (url.endsWith("/api/settings") && (opts.method || "GET") === "GET")
    return j({
      spec: { max_tokens: { label: "Max output tokens", min: 200, max: 32000, step: 100, hint: "h" } },
      teks: { tone: { label: "Tone", pilihan: ["santai", "lembut", "tegas"], hint: "h" }, nickname: { label: "Nickname", pilihan: [], hint: "h" } },
      presets: ["story"], values: { max_tokens: 8000, tone: "santai", nickname: "" },
    });
  if (url.endsWith("/api/settings")) return j({ values: { max_tokens: 8000, chunk_chars: 400, tts_parallel: 2, tone: "santai", nickname: "" }, spec: {}, teks: {} });
  if (url.endsWith("/api/usage")) return j({ hari: "2026-11-01", llm_tokens: 1234, tts_chars: 5600, tts_calls: 12 });
  if (url.includes("/api/reminders/due")) return j({ items: [] });
  if (url.endsWith("/api/reminders") && (opts.method || "GET") === "GET") return j({ items: [{ id: 1, teks: "minum air", due_ts: 1793488229 }] });
  if (url.endsWith("/api/reminders")) return j({ id: 2, teks: "x", due_ts: 1793488229 });
  if (url.endsWith("/api/journal") && (opts.method || "GET") === "POST") return j({ id: 1, hari: "2026-11-01", teks: "Hari ini gue belajar basis data." });
  if (url.endsWith("/api/journal")) return j({ items: [{ hari: "2026-11-01", teks: "Belajar SBD" }] });
  if (url.endsWith("/api/notes") && (opts.method || "GET") === "GET") return j({ items: [{ id: 1, judul: "SBD", potongan: 4 }] });
  if (url.endsWith("/api/notes")) return j({ id: 2, judul: "Logika", potongan: 3 });
  if (url.includes("/api/memory")) return j({ facts: [{ id: 1, predicate: "kos", object: "jl. mawar" }], facts_count: 1 });
  if (url.endsWith("/api/greeting")) return j({ text: "" });
  return j({});
};
window.URL.createObjectURL = () => "blob:x";
window.URL.revokeObjectURL = () => {};
window.Audio = class { play() { setTimeout(() => this.onended && this.onended(), 20); return Promise.resolve(); } pause() {} };
window.webkitSpeechRecognition = class { constructor() {} start() { setTimeout(() => this.onstart && this.onstart(), 1); } stop() {} abort() {} };
window.speechSynthesis = { getVoices: () => [], speak: () => {}, cancel: () => {} };
window.SpeechSynthesisUtterance = class {};
window.localStorage.clear();
Object.defineProperty(window.navigator, "wakeLock", { value: { request: async () => ({}) }, configurable: true });
Object.defineProperty(window.navigator, "mediaDevices", { value: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) }, configurable: true });

let evalErr = null;
try { window.eval(fs.readFileSync(WEB + "/app.js", "utf8")); } catch (e) { evalErr = e.message; }
try { window.eval(fs.readFileSync(WEB + "/extras.js", "utf8")); } catch (e) { evalErr = (evalErr || "") + " | extras: " + e.message; }

(async () => {
  await wait(2000); // tunggu inisialisasi awal selesai, biar status tidak ketimpa
  const doc = window.document;
  const out = { eval_error: evalErr, js_errors: errs };

  // sheet aksi
  doc.getElementById("actBtn").click();
  await wait(300);
  out.aksi_terbuka = doc.getElementById("actSheet").classList.contains("open");
  out.kartu = doc.querySelectorAll(".card").length;
  out.gambar = Array.from(doc.querySelectorAll(".card img")).map((i) => i.getAttribute("src"));
  out.reminder_terbaca = doc.getElementById("remindList").textContent.trim().slice(0, 30);
  out.jurnal_terbaca = doc.getElementById("journalList").textContent.trim().slice(0, 30);
  out.usage = doc.getElementById("usageBox").textContent.trim();

  // fokus
  const ttsAwal = TTS.length;
  doc.querySelector('[data-focus="15"]').click();
  await wait(600);
  out.fokus_diumumkan = (TTS[ttsAwal] || "").slice(0, 40);
  out.fokus_stop_tampil = !doc.getElementById("focusStop").hidden;
  doc.getElementById("focusStop").click();

  // reminder via chip
  doc.getElementById("remindTeks").value = "minum air";
  doc.querySelector('[data-kapan="5 menit"]').click();
  await wait(700);
  out.reminder_dikirim = CALLS.filter((c) => c.startsWith("POST /api/reminders")).length;

  // jurnal
  const ttsJurnal = TTS.length;
  doc.getElementById("journalDay").click();
  await wait(900);
  out.jurnal_dipanggil = CALLS.filter((c) => c.startsWith("POST /api/journal")).length;
  out.jurnal_diucapkan = (TTS[ttsJurnal] || "").slice(0, 40);

  // personality render
  out.persona_fields = doc.querySelectorAll("#personaFields [data-teks]").length;
  out.tone_ada = !!doc.getElementById("teks_tone");

  // catatan
  out.notes_list = doc.getElementById("notesList").textContent.trim().slice(0, 30);

  // wake word toggle (registry ada)
  out.wake_tombol = !!doc.getElementById("setWake");

  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
})();
