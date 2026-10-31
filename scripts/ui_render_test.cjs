// Muat web/index.html di jsdom dengan stub fetch/Audio, pastikan boot() jalan
// tanpa exception dan status/health ter-update. (Chromium gak bisa dipakai di box ini.)
const { JSDOM, VirtualConsole } = require("/tmp/uitest/node_modules/jsdom");
const fs = require("fs");
const path = require("path");

const WEB = "/root/kosmate/web";
const html = fs.readFileSync(path.join(WEB, "index.html"), "utf8");
const js = fs.readFileSync(path.join(WEB, "app.js"), "utf8");

const calls = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => calls.push({ err: e.message }));
vc.on("error", (m) => calls.push({ consoleError: String(m) }));

const dom = new JSDOM(html, { runScripts: "outside-only", virtualConsole: vc, url: "http://127.0.0.1:8080/" });
const { window } = dom;

// ---- stubs ----
window.fetch = async (url, opts = {}) => {
  calls.push({ fetch: url, method: (opts.method || "GET") });
  const body = (obj) => ({ ok: true, status: 200, json: async () => obj, body: null });
  if (url.endsWith("/api/health"))
    return body({ ok: true, name: "Kai", llm: "deepseek-v4-flash-free", llm_key: true, tts_providers: ["edge"], memory: { facts: 8 } });
  if (url.endsWith("/api/greeting")) return body({ text: "Hai Faa, malam Sabtu nih. Gimana harinya?" });
  if (url.endsWith("/api/memory/facts?limit=40"))
    return body({ facts: [{ id: 1, predicate: "alergi", object: "kacang" }] });
  return body({ ok: true });
};
window.Audio = class {
  constructor(src) { this.src = src; }
  play() { return Promise.resolve(); }
  pause() {}
};
window.URL.createObjectURL = () => "blob:x";
window.URL.revokeObjectURL = () => {};
Object.defineProperty(window.navigator, "wakeLock", { value: { request: async () => ({}) }, configurable: true });
window.localStorage.clear();

let err = null;
try {
  window.eval(js);
} catch (e) {
  err = e.message;
}

setTimeout(() => {
  const doc = window.document;
  const out = {
    eval_error: err,
    js_errors: calls.filter((c) => c.err || c.consoleError),
    api_calls: calls.filter((c) => c.fetch).map((c) => c.method + " " + c.fetch),
    brand: doc.getElementById("brandName").textContent,
    sub: doc.getElementById("brandSub").textContent,
    memBadge: doc.getElementById("memCount").textContent,
    status: doc.getElementById("status").textContent,
    reply: doc.getElementById("replyText").textContent,
    replyVisible: doc.getElementById("reply").classList.contains("show"),
    bodyState: doc.body.dataset.state,
  };
  console.log(JSON.stringify(out, null, 2));
  process.exit(0);
}, 900);
