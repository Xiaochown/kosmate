const { JSDOM, VirtualConsole } = require("/tmp/uitest/node_modules/jsdom");
const fs = require("fs");
const WEB = "/root/kosmate/web";
const vc = new VirtualConsole();
const errs = [];
vc.on("jsdomError", (e) => errs.push(e.message));
const errLog = [];
vc.on("error", (e) => errLog.push(String(e)));
const dom = new JSDOM(fs.readFileSync(WEB + "/index.html", "utf8"), {
  runScripts: "outside-only", virtualConsole: vc, url: "http://127.0.0.1:8080/",
});
const { window } = dom;
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
window.fetch = async (url) => {
  const j = (o) => ({ ok: true, status: 200, json: async () => o, text: async () => "{}", blob: async () => ({ size: 30000 }) });
  if (url.endsWith("/api/health")) return j({ ok: true, llm_key: true, fish_key: true, memory: { facts: 1 }, voice: { label: "M", engine: "fish", rate: "-20%" } });
  if (url.endsWith("/api/settings")) return j({ spec: {}, teks: {}, values: {} });
  if (url.endsWith("/api/usage")) return j({ llm_tokens: 0, tts_chars: 0, tts_calls: 0 });
  if (url.includes("due")) return j({ items: [] });
  if (url.endsWith("/api/reminders")) return j({ items: [] });
  if (url.endsWith("/api/journal")) return j({ items: [] });
  if (url.endsWith("/api/notes")) return j({ items: [] });
  if (url.endsWith("/api/greeting")) return j({ text: "" });
  return j({});
};
window.URL.createObjectURL = () => "blob:x";
window.URL.revokeObjectURL = () => {};
window.Audio = class { play() { return Promise.resolve(); } pause() {} };
window.webkitSpeechRecognition = class { start() {} stop() {} abort() {} };
window.speechSynthesis = { getVoices: () => [], speak: () => {}, cancel: () => {} };
window.SpeechSynthesisUtterance = class {};
window.localStorage.clear();
Object.defineProperty(window.navigator, "wakeLock", { value: { request: async () => ({}) }, configurable: true });
window.eval(fs.readFileSync(WEB + "/app.js", "utf8"));
window.eval(fs.readFileSync(WEB + "/extras.js", "utf8"));

(async () => {
  await wait(900);
  const doc = window.document;
  doc.getElementById("actBtn").click();
  await wait(100);
  const b = doc.querySelector('[data-focus="15"]');
  const out = { tombol_ada: !!b, handler: typeof (b && b.onclick) };
  try { b.click(); } catch (e) { out.click_error = String(e); }
  await wait(120);
  out.status = doc.getElementById("status").textContent;
  try { out.ex = window.eval("typeof EX"); } catch (e) { out.ex = "ERR " + e.message; }
  out.status2 = doc.getElementById("status").textContent;
  out.data_focus = !!doc.querySelector("[data-focus]");
  out.errs = errs;
  out.err_log = errLog.slice(0, 3);
  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
})();
