// Uji demo statis: demo.js + app.js + extras.js jalan tanpa server.
const { JSDOM, VirtualConsole } = require("/tmp/uitest/node_modules/jsdom");
const fs = require("fs");
const DIR = "/root/kosmate/demo";

const errs = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => errs.push(e.message));
const dom = new JSDOM(fs.readFileSync(DIR + "/index.html", "utf8"), {
  runScripts: "outside-only", virtualConsole: vc, url: "https://xiaochown.github.io/companion-demo/",
});
const { window } = dom;
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// jsdom belum punya API yang dipakai UI
window.URL.createObjectURL = () => "blob:x";
window.URL.revokeObjectURL = () => {};
window.Audio = class { play() { setTimeout(() => this.onended && this.onended(), 15); return Promise.resolve(); } pause() {} };
window.webkitSpeechRecognition = class { start() {} stop() {} abort() {} };
window.speechSynthesis = { getVoices: () => [], speak: () => {}, cancel: () => {} };
window.SpeechSynthesisUtterance = class {};
window.TextEncoder = window.TextEncoder || require("util").TextEncoder;
window.localStorage.clear();
Object.defineProperty(window.navigator, "wakeLock", { value: { request: async () => ({}) }, configurable: true });
Object.defineProperty(window.navigator, "mediaDevices", { value: { getUserMedia: async () => ({ getTracks: () => [{ stop() {} }] }) }, configurable: true });

let evalErr = null;
for (const f of ["demo.js", "app.js", "extras.js"]) {
  try { window.eval(fs.readFileSync(DIR + "/" + f, "utf8")); }
  catch (e) { evalErr = (evalErr || "") + ` [${f}] ${e.message}`; }
}

(async () => {
  await wait(2200);
  const doc = window.document;
  const out = {
    eval_error: evalErr,
    js_errors: errs,
    status: doc.getElementById("status").textContent.slice(0, 60),
    brand_sub: doc.getElementById("brandSub").textContent.slice(0, 60),
    memori: doc.getElementById("memCount").textContent,
    banner_demo: !!Array.from(doc.body.children).find((n) => (n.textContent || "").startsWith("DEMO")),
  };

  // aksi
  doc.getElementById("actBtn").click();
  await wait(300);
  out.aksi = doc.getElementById("actSheet").classList.contains("open");
  out.kartu = doc.querySelectorAll(".card").length;
  out.reminder = doc.getElementById("remindList").textContent.trim().slice(0, 40);
  out.usage = doc.getElementById("usageBox").textContent.trim().slice(0, 60);

  // setelan
  doc.getElementById("gear").click();
  await wait(300);
  out.setelan_terbuka = doc.getElementById("sheet").classList.contains("open");
  out.advanced_inputs = doc.querySelectorAll("#advFields input[data-key]").length;
  out.persona_inputs = doc.querySelectorAll("#personaFields [data-teks]").length;
  out.notes = doc.getElementById("notesList").textContent.trim().slice(0, 40);

  // chat demo (stream palsu)
  const ttsAwal = doc.getElementById("replyText").textContent;
  window.document.getElementById("input").value = "halo";
  window.eval("sendMessage('halo')");
  await wait(1200);
  out.chat_terisi = doc.getElementById("replyText").textContent.length > 10;
  out.chat_cuplikan = doc.getElementById("replyText").textContent.slice(0, 50);

  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
})();
