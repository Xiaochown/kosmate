// Uji setelan jeda: 14000 ms harus tersimpan, bukan balik ke 4000.
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

window.fetch = async (url) => {
  const j = (o) => ({ ok: true, status: 200, json: async () => o, text: async () => "{}", blob: async () => ({ size: 1000 }) });
  if (url.endsWith("/api/health")) return j({ ok: true, name: "Kai", llm_key: true, fish_key: true, tts_voice: "x", tts_rate: "-20%", voice: { key: "miyaa", label: "Miyaa", engine: "fish", rate: "-20%" }, memory: { facts: 0 } });
  if (url.endsWith("/api/greeting")) return j({ text: "" });
  if (url.endsWith("/api/voice")) return j({ active: { key: "miyaa", label: "Miyaa", engine: "fish", rate: "-20%" }, options: [], fish_key: true });
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
Object.defineProperty(window.navigator, "mediaDevices", { value: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) }, configurable: true });

let evalErr = null;
try { window.eval(fs.readFileSync(WEB + "/app.js", "utf8")); } catch (e) { evalErr = e.message; }

(async () => {
  await wait(350);
  const doc = window.document;
  const S = window.__S;
  const out = { eval_error: evalErr, js_errors: errs };

  const el = doc.getElementById("setSilence");
  for (const val of ["14000", "500", "999999", "abc"]) {
    el.value = val;
    el.dispatchEvent(new window.Event("change"));
    await wait(60);
    out["input_" + val] = { S: S.silenceMs, tampil: el.value };
  }
  out.tersimpan = JSON.parse(window.localStorage.getItem("kosmate.settings.v1") || "{}").silenceMs;
  out.status = doc.getElementById("status") ? doc.getElementById("status").textContent.slice(0, 60) : "(tak ada #status)";
  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
})();
