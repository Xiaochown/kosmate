import pathlib

a = pathlib.Path("/root/kosmate/web/app.js")
s = a.read_text()

# 1) overlay debug: buka ?debug=1 -> error JS tampil di layar (buat HP tanpa DevTools)
if "debug=1" not in s:
    s = s.replace(
        "function clearReply() { $(\"reply\").classList.remove(\"show\"); }",
        '''function clearReply() { $("reply").classList.remove("show"); }

/* ?debug=1 -> tampilkan error JavaScript langsung di layar HP */
if (location.search.indexOf("debug=1") >= 0) {
  const box = document.createElement("pre");
  box.style.cssText =
    "position:fixed;left:0;right:0;top:0;max-height:45vh;overflow:auto;z-index:9999;margin:0;" +
    "padding:8px;background:#111;color:#6f6;font:11px/1.45 monospace;white-space:pre-wrap";
  const tulis = (m) => { box.textContent += m + "\\n"; };
  document.addEventListener("DOMContentLoaded", () => {
    document.body.appendChild(box);
    tulis("debug on · " + location.href);
    tulis("UA: " + navigator.userAgent.slice(0, 90));
  });
  window.addEventListener("error", (e) =>
    tulis("ERR " + e.message + " @" + (e.filename || "").split("/").pop() + ":" + (e.lineno || "")));
  window.addEventListener("unhandledrejection", (e) =>
    tulis("REJ " + ((e.reason && e.reason.message) || e.reason)));
}''')

# 2) daftarkan service worker (syarat Chrome "Install app")
if "serviceWorker.register" not in s:
    s = s.replace(
        "    await loadVoices();",
        '''    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("sw.js", { scope: "./" })
        .then(() => diag("app", "service worker aktif"))
        .catch((e) => diag("app", "SW gagal: " + e.message));
    }
    await loadVoices();''')

# 3) chip suara di beranda: tampilkan suara aktif + buka setelan saat diketuk
if "voiceChip" not in s:
    s = s.replace(
        "function clearReply() { $(\"reply\").classList.remove(\"show\"); }",
        '''function clearReply() { $("reply").classList.remove("show"); }

function updateVoiceChip() {
  const el = $("voiceChip");
  if (!el) return;
  const o = (S.voiceOptions || []).find((x) => x.key === S.voiceKey) || (S.voiceOptions || [])[0] || {};
  const label = o.label || "Voice";
  const nama = label.split("—")[0].split("(")[0].trim();
  el.textContent = nama + " · " + String(S.tempo || "").replace("%", "") + "%";
  el.onclick = () => { $("sheet").classList.add("open"); loadSettingsPanel(); };
}''')

s = s.replace("    await loadVoices();", "    await loadVoices();\n    updateVoiceChip();", 1) if "updateVoiceChip();" not in s else s
s = s.replace("  S.voiceKey = key;", "  S.voiceKey = key;\n  updateVoiceChip();")

a.write_text(s)
for k in ("debug=1", "serviceWorker.register", "voiceChip", "updateVoiceChip();"):
    print(f"{k:26s}", "ada" if k in s else "TIDAK ADA")
