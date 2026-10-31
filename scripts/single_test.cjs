// Uji single.html: semua inline, tidak butuh request lain.
const { JSDOM, VirtualConsole } = require("/tmp/uitest/node_modules/jsdom");
const fs = require("fs");

const errs = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errs.push(e.message));
const file = "/root/kosmate/demo/single.html";
const dom = new JSDOM(fs.readFileSync(file, "utf8"), {
  runScripts: "outside-only", virtualConsole: vc,
  url: "https://xiaochown.github.io/companion-demo/single.html",
});
const { window } = dom;
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

window.URL.createObjectURL = () => "blob:x";
window.URL.revokeObjectURL = () => {};
window.Audio = class { play() { setTimeout(() => this.onended && this.onended(), 10); return Promise.resolve(); } pause() {} };
window.webkitSpeechRecognition = class { start() {} stop() {} abort() {} };
window.speechSynthesis = { getVoices: () => [], speak: () => {}, cancel: () => {} };
window.SpeechSynthesisUtterance = class {};
window.localStorage.clear();
Object.defineProperty(window.navigator, "wakeLock", { value: { request: async () => ({}) }, configurable: true });
Object.defineProperty(window.navigator, "mediaDevices", { value: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) }, configurable: true });

const scripts = [...window.document.querySelectorAll("script")].map((s) => s.textContent).filter(Boolean);
let evalErr = null;
for (const s of scripts) {
  try { window.eval(s); } catch (e) { evalErr = (evalErr || "") + e.message + "; "; }
}

(async () => {
  await wait(2200);
  const d = window.document;
  const out = {
    scripts_inline: scripts.length,
    eval_error: evalErr,
    js_errors: errs.slice(0, 3),
    status: d.getElementById("status").textContent.slice(0, 40),
    voice_sub: d.getElementById("brandSub").textContent.slice(0, 40),
    banner_demo: !!Array.from(d.body.children).find((n) => (n.textContent || "").startsWith("DEMO")),
    kartu: d.querySelectorAll(".card").length,
    gambar_inline: (d.querySelector(".card img") || { getAttribute: () => "" }).getAttribute("src").slice(0, 24),
    style_terpasang: !!d.querySelector("style"),
  };
  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
})();
