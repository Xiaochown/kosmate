const { JSDOM, VirtualConsole } = require("/tmp/uitest/node_modules/jsdom");
const fs = require("fs");
const WEB = "/root/kosmate/web";
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => console.log("  jsdomError:", String(e.message).slice(0, 120)));
const html = fs.readFileSync(WEB + "/index.html", "utf8").replace(/<script src="[^"]*"><\/script>/g, "");
const dom = new JSDOM(html, { runScripts: "dangerously", url: "http://127.0.0.1:8080/", virtualConsole: vc });
const { window } = dom;
window.fetch = async () => ({ ok: true, status: 200, json: async () => ({ values: {}, skema: { fields: {}, teks: {} }, items: [] }), text: async () => "{}", blob: async () => ({ size: 30000 }) });

const semua = ["app.js", "extras.js", "wake.js", "i18n.js"].map((f) => fs.readFileSync(`${WEB}/${f}`, "utf8")).join("\n;\n");
try {
  window.eval(semua);
  console.log("eval gabungan OK");
} catch (e) {
  console.log("eval gagal:", e.message);
}
// cari tahu EX kelihatan atau tidak dari eval terpisah
try { console.log("typeof EX (eval baru):", window.eval("typeof EX")); } catch (e) { console.log("cek EX gagal:", e.message); }
process.exit(0);
