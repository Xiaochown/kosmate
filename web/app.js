/* KOSMATE client — STT browser, streaming chat, TTS queue, memori. */
const $ = (id) => document.getElementById(id);
const LS = "kosmate.settings.v1";

const S = {
  state: "idle",
  speaking: false,
  autoListen: false,
  speakReply: true,
  silenceMs: 900,
  voice: "id-ID-GadisNeural",
  ttsMode: "auto",
  tempo: "-20%",
  browserFallback: true,
  session: "live-" + Date.now(),
  replyText: "",
  youSaid: "",
  unlocked: false,
  pendingGreeting: "",
  rec: null,
  listening: false,
  finalText: "",
  silenceTimer: null,
  mediaRec: null,
  chunks: [],
  busy: false,
  diag: {},
  recErrors: 0,
  lastSpoken: "",
  cooldownMs: 900,
  speechChunk: "block", // "block" = satu blok utuh (intonasi nyambung) | "sentence" = per kalimat
  chunkChars: 400, // potongan maksimum; potongan berikutnya di-prefetch saat yang ini diputar
  ttsParallel: 2,
  listenTimer: null,
  stopRequested: false,
  cancelSpeech: null,
};
try { window.__S = S; } catch (e) {}

/* ---------------- settings ---------------- */
function loadSettings() {
  try {
    const s = JSON.parse(localStorage.getItem(LS) || "{}");
    Object.assign(S, {
      autoListen: !!s.autoListen,
      speakReply: s.speakReply !== false,
      silenceMs: Math.max(300, Math.min(60000, Number(s.silenceMs || 900))),
      cooldownMs: Math.max(200, Math.min(15000, Number(s.cooldownMs || 900))),
      speechChunk: s.speechChunk === "sentence" ? "sentence" : "block",
      voice: s.voice || "id-ID-GadisNeural",
      ttsMode: s.ttsMode || "auto",
      tempo: s.tempo || "-20%",
      browserFallback: s.browserFallback !== false,
    });
  } catch (e) {}
}
function saveSettings() {
  localStorage.setItem(LS, JSON.stringify({
    autoListen: S.autoListen, speakReply: S.speakReply,
    silenceMs: S.silenceMs, voice: S.voice, ttsMode: S.ttsMode,
    tempo: S.tempo, browserFallback: S.browserFallback, cooldownMs: S.cooldownMs,
    speechChunk: S.speechChunk,
  }));
}

/* ---------------- ui helpers ---------------- */
function setState(st) {
  S.state = st;
  document.body.dataset.state = st;
  const label = {
    idle: "Tap to talk",
    listening: "Listening…",
    thinking: "Thinking…",
    speaking: "Speaking…",
  }[st] || "";
  setStatus(label);
}
function setStatus(html) { $("status").innerHTML = html; }
function showLive(final, interim) {
  const el = $("live");
  if (!final && !interim) { el.classList.remove("show"); el.innerHTML = ""; return; }
  el.classList.add("show");
  el.innerHTML = escapeHtml(final || "") + ' <span class="interim">' + escapeHtml(interim || "") + "</span>";
}
function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function showReply() {
  const r = $("reply");
  $("replyYou").textContent = S.youSaid ? "You: " + S.youSaid : "";
  $("replyText").textContent = S.replyText;
  if (S.replyText) r.classList.add("show");
}
function clearReply() { $("reply").classList.remove("show"); }

function updateVoiceChip() {
  const el = $("voiceChip");
  if (!el) return;
  const o = (S.voiceOptions || []).find((x) => x.key === S.voiceKey) || (S.voiceOptions || [])[0] || {};
  const label = o.label || "Voice";
  const nama = label.split("—")[0].split("(")[0].trim();
  el.textContent = nama + " · " + String(S.tempo || "").replace("%", "") + "%";
  el.onclick = () => {
    openSheet("settings");
    const sel = $("setVoice");
    if (sel) setTimeout(() => sel.scrollIntoView({ behavior: "smooth", block: "center" }), 120);
  };
}

/* ?debug=1 -> tampilkan error JavaScript langsung di layar HP */
if (location.search.indexOf("debug=1") >= 0) {
  const box = document.createElement("pre");
  box.style.cssText =
    "position:fixed;left:0;right:0;top:0;max-height:45vh;overflow:auto;z-index:9999;margin:0;" +
    "padding:8px;background:#111;color:#6f6;font:11px/1.45 monospace;white-space:pre-wrap";
  const tulis = (m) => { box.textContent += m + "\n"; };
  document.addEventListener("DOMContentLoaded", () => {
    document.body.appendChild(box);
    tulis("debug on · " + location.href);
    tulis("UA: " + navigator.userAgent.slice(0, 90));
    setTimeout(() => {
      const vw = innerWidth, vh = innerHeight;
      const R = (sel) => {
        const el = document.querySelector(sel);
        if (!el) return "-";
        const r = el.getBoundingClientRect();
        return Math.round(r.width) + "x" + Math.round(r.height);
      };
      tulis("LAPORAN LAYOUT · layar " + vw + "x" + vh);
      tulis("  dokumen  " + document.documentElement.scrollWidth + "x" + document.body.scrollHeight);
      tulis("  header   " + R(".topbar") + "  nav " + R(".topnav"));
      tulis("  banner   " + R(".banner img") + "  chips " + R(".mode-row"));
      tulis("  orb      " + R(".orb") + "  composer " + R(".composer"));
      const luber = [...document.querySelectorAll("body *")]
        .map((e) => ({ t: e.tagName.toLowerCase() + "." + String(e.className).split(" ")[0], r: e.getBoundingClientRect() }))
        .filter((o) => o.r.right > vw + 1 || o.r.width > vw + 1)
        .slice(0, 6)
        .map((o) => o.t + "(" + Math.round(o.r.width) + ")");
      tulis("  luber    " + (luber.length ? luber.join(", ") : "tidak ada"));
    }, 1200);
  });
  window.addEventListener("error", (e) =>
    tulis("ERR " + e.message + " @" + (e.filename || "").split("/").pop() + ":" + (e.lineno || "")));
  window.addEventListener("unhandledrejection", (e) =>
    tulis("REJ " + ((e.reason && e.reason.message) || e.reason)));
}

/* ---------------- TTS ---------------- */
let speechGen = 0;      // naik tiap kali user motong ucapan
let speechJobs = [];    // {gen, text, audio: Promise<{blob}|{browser}>}
let draining = false;   // sedang memutar antrean
let currentAudio = null;

function speakable(t) {
  return (t || "").replace(/[*_`#>~]/g, "").replace(/\[(.*?)\]\(.*?\)/g, "$1").trim();
}

/* Antrean TTS ber-prefetch: sampai 2 potongan digenerate paralel, jadi saat
   potongan sekarang sedang diputar, potongan berikutnya sudah siap. */
let ttsInFlight = 0;
const ttsWaiting = [];

function mulaiFetch(job) {
  const batas = Math.max(1, Math.min(4, Number(S.ttsParallel) || 2));
  if (ttsInFlight >= batas) {
    ttsWaiting.push(job);
    return;
  }
  ttsInFlight++;
  job.audio = fetchSpeechAudio(job.text).finally(() => {
    ttsInFlight--;
    const next = ttsWaiting.shift();
    if (next) mulaiFetch(next);
  });
}

function enqueueSpeech(text) {
  const t = speakable(text);
  if (!t || !S.speakReply) return;
  const job = { gen: speechGen, text: t, audio: null };
  speechJobs.push(job);
  mulaiFetch(job);
  drainSpeech();
}

async function fetchSpeechAudio(text) {
  if (S.ttsMode !== "browser") {
    try {
      const t0 = performance.now();
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text, voice: S.voice, rate: S.tempo }),
      });
      if (!res.ok) {
        const why = (await res.text().catch(() => "")).slice(0, 120);
        throw new Error("server " + res.status + (why ? " · " + why : ""));
      }
      const blob = await res.blob();
      if (blob.size < 800) throw new Error("audio kosong (" + blob.size + " byte)");
      diag("tts", "siap " + blob.size + " byte · " + Math.round(performance.now() - t0) + "ms");
      return { blob };
    } catch (e) {
      diag("tts", "server gagal: " + e.message);
      if (S.ttsMode === "server" || !S.browserFallback) throw e;
    }
  }
  return { browser: true };
}

async function drainSpeech() {
  if (draining) return;
  draining = true;
  setState("speaking");
  try {
    while (speechJobs.length) {
      const item = speechJobs.shift();
      if (item.gen !== speechGen) continue;
      if (!item.audio) mulaiFetch(item);
      try {
        const out = await item.audio;
        if (item.gen !== speechGen) continue;
        if (out && out.blob) await playBlob(out.blob);
        else await speakBrowser(item.text);
      } catch (e) {
        diag("tts", "gagal diputar: " + e.message);
        setStatus("No audio — check Settings → Diagnostics");
      }
    }
  } finally {
    draining = false;
    if (!speechJobs.length) {
      S.speaking = false;
      S.lastSpoken = speakable(S.replyText || "");
      setState(S.autoListen ? "listening" : "idle");
      if (S.autoListen) scheduleListen();
    }
  }
}

function adaUcapan() {
  return draining || speechJobs.length > 0;
}

/* deteksi kalau yang ditangkap mic sebenarnya suara Kosmate sendiri */
function normText(s) {
  return (s || "").toLowerCase().replace(/[^\w\s]/g, " ").replace(/\s+/g, " ").trim();
}
function looksLikeEcho(text) {
  const said = normText(text);
  const last = normText(S.lastSpoken || "");
  if (said.length < 6 || !last) return false;
  if (last.includes(said)) return true;
  const words = said.split(" ").filter(Boolean);
  if (words.length < 2) return false;
  const hit = words.filter((w) => last.includes(w)).length;
  return hit / words.length >= 0.6;
}

/* log diagnosa: kelihatan di panel Diagnostik, bukan cuma console */
function diag(key, msg) {
  S.diag[key] = msg + " · " + new Date().toLocaleTimeString("id-ID");
  console.log("[diag]", key, msg);
  if (document.getElementById("diagBox")) renderDiag();
}

/* suara cadangan: speechSynthesis bawaan Android (offline, tanpa server) */
function speakBrowser(text) {
  return new Promise((resolve, reject) => {
    if (!("speechSynthesis" in window)) {
      return reject(new Error("browser ini gak punya speechSynthesis"));
    }
    const u = new SpeechSynthesisUtterance(speakable(text));
    u.lang = "id-ID";
    u.rate = 1.02;
    const voices = window.speechSynthesis.getVoices() || [];
    const idv =
      voices.find((v) => /^id[-_]ID/i.test(v.lang)) || voices.find((v) => /^id/i.test(v.lang));
    if (idv) u.voice = idv;
    S.speaking = true;
    stopRecognition(true);
    const done = () => {
      S.speaking = false;
      resolve();
    };
    u.onend = done;
    u.onerror = (e) => {
      S.speaking = false;
      reject(new Error("speechSynthesis: " + (e.error || "error")));
    };
    try {
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    } catch (e) {
      S.speaking = false;
      reject(e);
    }
  });
}

/* jeda sebelum mic nyala lagi: kasih waktu gema speaker hilang */
function scheduleListen() {
  clearTimeout(S.listenTimer);
  const wait = Math.max(200, Number(S.cooldownMs) || 900);
  S.listenTimer = setTimeout(() => {
    if (!S.autoListen || S.speaking || S.busy || adaUcapan()) return;
    startListening(true);
  }, wait);
}

/* hentikan semua ucapan (dipakai kalau user ketuk orb saat Kai ngomong) */
function stopSpeaking() {
  speechGen++; // semua kalimat di antrean lama dianggap basi
  if (S.cancelSpeech) {
    try { S.cancelSpeech(); } catch (e) {}
  }
  if ("speechSynthesis" in window) {
    try { window.speechSynthesis.cancel(); } catch (e) {}
  }
  speechJobs = [];
  S.speaking = false;
  currentAudio = null;
  setState("idle");
}

function playBlob(blob) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(blob);
    const a = new Audio(url);
    currentAudio = a;
    S.speaking = true;
    stopRecognition(true);
    let settled = false;
    const finish = (err) => {
      if (settled) return;
      settled = true;
      S.cancelSpeech = null;
      URL.revokeObjectURL(url);
      S.speaking = false;
      currentAudio = null;
      err ? reject(err) : resolve();
    };
    S.cancelSpeech = () => finish(new Error("dibatalkan"));
    a.onended = () => finish(null);
    a.onerror = () => finish(new Error("audio gagal diputar (autoplay diblok? tap layar)"));
    a.play().catch((e) => finish(new Error("play() ditolak: " + (e.name || e.message))));
  });
}

/* ---------------- potong teks buat TTS ----------------
   Satu blok utuh = satu request TTS = intonasi nyambung, tanpa jeda di tiap titik.
   Kalau teks panjang (> chunkChars), potong di batas kalimat TERAKHIR biar tetap wajar.
*/
function boundaryIndex(t, from = 0) {
  for (let i = from; i < t.length; i++) {
    if (".!?…\n".includes(t[i])) return i;
  }
  return -1;
}

function takeChunk(buf, flush) {
  if (flush) return { take: buf, rest: "" };
  const min = Number(S.chunkChars) || 3000;
  if (buf.length < min) return { take: "", rest: buf };
  // cari batas kalimat terakhir di 60% terakhir buffer
  let cut = -1;
  for (let i = buf.length - 1; i >= Math.floor(buf.length * 0.6); i--) {
    if (".!?…\n".includes(buf[i])) { cut = i + 1; break; }
  }
  if (cut === -1) return { take: "", rest: buf };
  return { take: buf.slice(0, cut), rest: buf.slice(cut) };
}

function feedDelta(chunk) {
  S.replyText += chunk;
  showReply();
  S.replyBuf = (S.replyBuf || "") + chunk;

  if (S.speechChunk === "sentence") {
    // mode lama: potong tiap kalimat (intonasi ke-reset, tapi mulai lebih cepat)
    let idx = boundaryIndex(S.replyBuf);
    while (idx !== -1) {
      const sentence = S.replyBuf.slice(0, idx + 1);
      S.replyBuf = S.replyBuf.slice(idx + 1);
      if (sentence.trim().length >= 6) enqueueSpeech(sentence);
      idx = boundaryIndex(S.replyBuf);
    }
    return;
  }

  const { take, rest } = takeChunk(S.replyBuf, false);
  if (take.trim().length >= 20) enqueueSpeech(take);
  S.replyBuf = rest;
}

/* ---------------- chat ---------------- */
async function sendMessage(text) {
  if (!text || S.busy) return;
  S.busy = true;
  S.youSaid = text;
  S.replyText = "";
  S.replyBuf = "";
  showLive("", "");
  showReply();
  setState("thinking");
  stopRecognition(true);
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ message: text, session: S.session }),
    });
    if (!res.ok) throw new Error("chat " + res.status);
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let acc = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      acc += dec.decode(value, { stream: true });
      let i;
      while ((i = acc.indexOf("\n\n")) !== -1) {
        const raw = acc.slice(0, i).trim();
        acc = acc.slice(i + 2);
        if (!raw.startsWith("data:")) continue;
        let evt;
        try { evt = JSON.parse(raw.slice(5).trim()); } catch (e) { continue; }
        if (evt.type === "delta") {
          if (S.state !== "speaking") setState("thinking");
          feedDelta(evt.text);
        } else if (evt.type === "error") {
          S.replyText = evt.text;
          showReply();
          enqueueSpeech(evt.text);
        } else if (evt.type === "done") {
          // sisa teks diucapkan utuh (satu request TTS) biar intonasinya nyambung
          const sisa = takeChunk(S.replyBuf || "", true).take;
          if (sisa && sisa.trim().length >= 3) enqueueSpeech(sisa);
          S.replyBuf = "";
          if (evt.memory) $("memCount").textContent = evt.memory.facts + " facts";
          if (evt.truncated) {
            setStatus("Reply hit the token limit — raise <code>LLM_MAX_TOKENS</code> in .env");
            diag("stt", "jawaban truncated: finish_reason=length");
          }
        }
      }
    }
  } catch (e) {
    S.replyText = "Koneksi ke otak gue putus. Cek server masih jalan? (" + e.message + ")";
    showReply();
    enqueueSpeech("Koneksi ke otak gue putus. Cek server-nya ya.");
  } finally {
    S.busy = false;
    // tunggu antrean suara kosong dulu, baru mic nyala lagi
    const tunggu = setInterval(() => {
      if (adaUcapan()) return;
      clearInterval(tunggu);
      if (!S.speaking) setState(S.listening ? "listening" : "idle");
      if (S.autoListen) startListening(true);
    }, 250);
  }
}

/* ---------------- STT: Web Speech API ---------------- */
function initRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return null;
  const rec = new SR();
  rec.lang = "id-ID";
  rec.continuous = false;
  rec.interimResults = true;
  rec.maxAlternatives = 1;

  rec.onstart = () => {
    S.listening = true;
    if (!S.speaking) setState("listening");
  };
  rec.onresult = (e) => {
    let interim = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const r = e.results[i];
      if (r.isFinal) S.finalText += r[0].transcript;
      else interim += r[0].transcript;
    }
    showLive(S.finalText, interim);
    clearTimeout(S.silenceTimer);
    S.silenceTimer = setTimeout(() => {
      if (S.listening && !S.finalText) { try { rec.stop(); } catch (err) {} }
    }, S.silenceMs + 700);
  };
  rec.onerror = (e) => {
    const err = e.error || "unknown";
    S.recErrors = (S.recErrors || 0) + 1;
    diag("stt", "error: " + err + " (ke-" + S.recErrors + ")");
    if (err === "not-allowed" || err === "service-not-allowed") {
      setStatus("Microphone blocked. Chrome → Site settings → Microphone → allow 127.0.0.1");
      S.autoListen = false;
      syncToggles();
    } else if (err === "no-speech" || err === "aborted") {
      // normal: user diam. biarkan onend yang nyalain ulang
    } else if (err === "network") {
      setStatus("STT butuh internet — cek koneksi");
    } else if (err === "audio-capture") {
      setStatus("Microphone busy? Close the app using it");
    }
  };
  rec.onend = () => {
    S.listening = false;
    clearTimeout(S.silenceTimer);
    const said = S.finalText.trim();
    S.finalText = "";
    if (said) {
      showLive("", "");
      if (looksLikeEcho(said)) {
        diag("stt", "abaikan suara sendiri: " + said.slice(0, 40));
        if (S.autoListen) scheduleListen();
        return;
      }
      S.recErrors = 0;
      sendMessage(said);
    } else if (S.autoListen && !S.speaking && !S.busy) {
      armListening();
    } else if (!S.speaking) {
      setState("idle");
      showLive("", "");
    }
  };
  return rec;
}

/* nyalain lagi pendengar otomatis dengan jeda yang makin panjang kalau error */
function armListening() {
  if (!S.rec || S.speaking || S.busy || S.listening || adaUcapan()) return;
  scheduleListen();
}

/* heartbeat: kalau karena alasan apa pun pendengar mati diam-diam, nyalain lagi */
function heartbeat() {
  if (!S.autoListen || !S.rec) return;
  if (S.listening || S.speaking || S.busy) return;
  if (adaUcapan()) return; // masih ada kalimat yang belum selesai diucapkan
  if (S.state === "listening") return;
  diag("stt", "heartbeat: pendengar mati, dinyalakan ulang");
  startListening(true);
}

function startListening(auto) {
  if (!S.rec) {
    setStatus("This browser has no speech recognition — open in Chrome");
    return;
  }
  if (S.speaking || S.listening) return;
  try {
    S.rec.start();
    diag("stt", "start ok" + (auto ? " (auto)" : ""));
  } catch (e) {
    diag("stt", "start gagal: " + (e.name || e.message));
    armListening();
  }
}
function stopRecognition(silent) {
  if (!S.rec) return;
  try { S.rec.abort(); } catch (e) {}
  S.listening = false;
  if (!silent) showLive("", "");
}

/* ---------------- STT fallback (MediaRecorder) ---------------- */
async function startMediaRec() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mr = new MediaRecorder(stream, { mimeType: pickMime() });
    S.chunks = [];
    mr.ondataavailable = (e) => { if (e.data.size > 0) S.chunks.push(e.data); };
    mr.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(S.chunks, { type: mr.mimeType });
      setState("thinking");
      setStatus("transkripsi…");
      try {
        const fd = new FormData();
        fd.append("audio", blob, "voice.webm");
        const r = await fetch("/api/stt", { method: "POST", body: fd });
        const j = await r.json();
        if (j.text) sendMessage(j.text);
        else { setState("idle"); setStatus("Didn't catch that, try again"); }
      } catch (e) {
        setState("idle");
        setStatus("Transcription failed: " + e.message);
      }
    };
    S.mediaRec = mr;
    mr.start();
    setState("listening");
    setStatus("Recording… tap mic again to send");
  } catch (e) {
    setStatus("Mic unavailable: " + e.message);
  }
}
function pickMime() {
  const list = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
  for (const m of list) if (window.MediaRecorder && MediaRecorder.isTypeSupported(m)) return m;
  return "";
}

/* ---------------- events ---------------- */
function bind() {
  $("orb").onclick = () => {
    unlockAudio();
    if (S.speaking || adaUcapan()) {
      stopSpeaking();
      setStatus("Stopped. Tap again to talk");
      return;
    }
    if (S.listening) stopRecognition(false);
    else startListening();
  };

  $("micBtn").onclick = () => {
    unlockAudio();
    if (S.rec) {
      if (S.listening) stopRecognition(false);
      else startListening();
    } else if (S.mediaRec && S.mediaRec.state === "recording") {
      S.mediaRec.stop();
      $("micBtn").classList.remove("rec");
    } else {
      startMediaRec();
      $("micBtn").classList.add("rec");
    }
  };

  $("sendBtn").onclick = () => {
    unlockAudio();
    const v = $("input").value.trim();
    if (v) { $("input").value = ""; sendMessage(v); }
  };
  $("input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); $("sendBtn").click(); }
  });

  document.querySelectorAll(".mode-chip").forEach((b) => {
    b.onclick = async () => {
      document.querySelectorAll(".mode-chip").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      $("setMode").value = b.dataset.mode;
      await fetch("/api/mode", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ mode: b.dataset.mode }),
      });
      setStatus("Mode: <strong>" + b.dataset.mode + "</strong>");
    };
  });

  $("gear").onclick = () => openSheet("settings");
  $("memBtn").onclick = () => openSheet("memory");
  $("closeSheet").onclick = () => $("sheet").classList.remove("open");
  $("closeDiag").onclick = () => $("diagSheet").classList.remove("open");

  $("setMode").onchange = (e) => {
    const m = e.target.value;
    document.querySelectorAll(".mode-chip").forEach((x) => x.classList.toggle("active", x.dataset.mode === m));
    fetch("/api/mode", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ mode: m }),
    });
  };
  $("setVoice").onchange = (e) => pilihVoice(e.target.value);
  $("setAutoListen").onclick = () => {
    S.autoListen = !S.autoListen;
    saveSettings();
    syncToggles();
    if (S.autoListen) {
      unlockAudio();
      diag("stt", "auto listen enabled");
      if (!S.rec) {
        setStatus("Auto listen needs Chrome (no speech recognition here)");
      } else {
        startListening(true);
      }
    } else {
      stopRecognition(false);
      setState("idle");
    }
  };
  document.querySelectorAll(".preset").forEach((b) => {
    b.onclick = () => applyPreset(b.dataset.preset || "default");
  });
  $("setSpeechChunk").onchange = (e) => {
    S.speechChunk = e.target.value === "sentence" ? "sentence" : "block";
    saveSettings();
    diag("tts", "potong teks: " + S.speechChunk);
  };
  $("setTempo").onchange = (e) => {
    S.tempo = e.target.value;
    saveSettings();
    diag("tts", "tempo: " + S.tempo);
  };
  $("setTtsMode").onchange = (e) => {
    S.ttsMode = e.target.value;
    saveSettings();
    diag("tts", "mode suara: " + S.ttsMode);
  };
  $("diagBtn").onclick = () => openSheet("diag");
  $("setFallback").onclick = () => {
    S.browserFallback = !S.browserFallback;
    saveSettings();
    syncToggles();
    diag("tts", "cadangan suara HP: " + (S.browserFallback ? "aktif" : "mati"));
  };
  $("diagTtsTest").onclick = runTtsTest;
  $("diagMicTest").onclick = testMic;
  $("setCooldown").onchange = (e) => {
    const n = Math.max(200, Math.min(15000, parseInt(e.target.value || "900", 10) || 900));
    S.cooldownMs = n;
    e.target.value = String(n);
    saveSettings();
  };
  $("setSpeak").onclick = () => { S.speakReply = !S.speakReply; saveSettings(); syncToggles(); };
  $("setSilence").onchange = (e) => {
    const n = Math.max(300, Math.min(60000, parseInt(e.target.value || "900", 10) || 900));
    S.silenceMs = n; e.target.value = String(n); saveSettings();
    setStatus("Silence wait: <strong>" + n + " ms</strong> (" + (n / 1000).toFixed(1) + "s)");
  };

  document.addEventListener("visibilitychange", async () => {
    if (document.visibilityState === "visible") requestWakeLock();
  });
  document.addEventListener("click", () => unlockAudio(), { once: true });
}

function syncToggles() {
  const a = $("setAutoListen"), s = $("setSpeak");
  a.classList.toggle("on", S.autoListen);
  a.innerHTML = '<span class="dot' + (S.autoListen ? " ok" : "") + '"></span>' + (S.autoListen ? "aktif" : "nonaktif");
  s.classList.toggle("on", S.speakReply);
  s.innerHTML = '<span class="dot' + (S.speakReply ? " ok" : "") + '"></span>' + (S.speakReply ? "aktif" : "nonaktif");
  if ($("setVoice") && S.voiceKey) {
    const ada = Array.from($("setVoice").options).some((o) => o.value === S.voiceKey);
    if (ada) $("setVoice").value = S.voiceKey;
  }
  $("setSilence").value = String(S.silenceMs);
  if ($("setCooldown")) $("setCooldown").value = String(S.cooldownMs);
  if ($("setTtsMode")) $("setTtsMode").value = S.ttsMode;
  if ($("setTempo")) $("setTempo").value = S.tempo;
  if ($("setSpeechChunk")) $("setSpeechChunk").value = S.speechChunk;
  const fb = $("setFallback");
  if (fb) {
    fb.classList.toggle("on", S.browserFallback);
    fb.innerHTML = '<span class="dot' + (S.browserFallback ? " ok" : "") + '"></span>' + (S.browserFallback ? "aktif" : "mati");
  }
}

/* ---------------- pemilih suara ---------------- */
async function loadVoices() {
  try {
    const r = await fetch("/api/voice");
    const j = await r.json();
    const sel = $("setVoice");
    if (!sel) return;
    sel.innerHTML = "";
    S.voiceOptions = j.options || [];
    (j.options || []).forEach((o) => {
      const opt = document.createElement("option");
      opt.value = o.key;
      opt.textContent = o.label + " · " + o.rate.replace("-", "−");
      if (!o.ready) opt.textContent += " (butuh FISH_API_KEY)";
      sel.appendChild(opt);
    });
    if (j.active) {
      sel.value = j.active.key;
      S.voiceKey = j.active.key;
      $("voiceNote").innerHTML = j.fish_key
        ? "Fish Audio ready. Pick one — if it fails, it stays <b>silent</b> instead of switching voice."
        : "FISH_API_KEY is missing in .env — Fish voices are unavailable. Add it, then reload.";
    }
    updateVoiceChip();
  } catch (e) {
    diag("tts", "voice list failed: " + e.message);
  }
}

async function pilihVoice(key) {
  try {
    const r = await fetch("/api/voice", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ key }),
    });
    if (!r.ok) throw new Error("server " + r.status);
    const j = await r.json();
    S.voiceKey = j.active.key;
    S.tempo = j.active.rate;
    if (j.active.engine === "fish") S.browserFallback = false; // no fallback = no suara lain
    saveSettings();
    syncToggles();
    diag("tts", "voice diganti: " + j.active.key + " (" + j.active.rate + ")");
    setStatus("Voice: <strong>" + j.active.label + "</strong> · " + j.active.rate);
    await runTtsTest();
  } catch (e) {
    diag("tts", "gagal ganti voice: " + e.message);
    setStatus("Could not change voice: " + e.message);
  }
}

/* ---------------- setelan runtime dari server ---------------- */
function applyServerValues(v) {
  if (!v) return;
  if (v.chunk_chars) S.chunkChars = Number(v.chunk_chars);
  if (v.tts_parallel) S.ttsParallel = Number(v.tts_parallel);
}

function renderAdv(j) {
  const box = $("advFields");
  if (!box) return;
  const vals = j.values || {};
  box.innerHTML = Object.entries(j.spec || {})
    .map(([k, s]) => {
      return (
        '<div class="field">' +
        '<label for="adv_' + k + '">' + s.label + "</label>" +
        '<input id="adv_' + k + '" data-key="' + k + '" type="number" inputmode="decimal"' +
        ' min="' + s.min + '" max="' + s.max + '" step="' + s.step + '" value="' + vals[k] + '">' +
        '<p class="tiny">' + (s.hint || "") + "</p>" +
        "</div>"
      );
    })
    .join("");
  box.querySelectorAll("input[data-key]").forEach((inp) => {
    inp.onchange = () => postSettings({ [inp.dataset.key]: inp.value });
  });

  // setelan teks (tone / humor / nickname)
  const pb = $("personaFields");
  if (pb && j.teks) {
    pb.innerHTML = Object.entries(j.teks)
      .map(([k, s]) => {
        if (s.pilihan && s.pilihan.length) {
          return (
            '<div class="field"><label for="teks_' + k + '">' + s.label + "</label>" +
            '<select id="teks_' + k + '" data-teks="' + k + '">' +
            s.pilihan.map((v) => '<option value="' + v + '"' + (vals[k] === v ? " selected" : "") + ">" + v + "</option>").join("") +
            "</select><p class=\"tiny\">" + (s.hint || "") + "</p></div>"
          );
        }
        return (
          '<div class="field"><label for="teks_' + k + '">' + s.label + "</label>" +
          '<input id="teks_' + k + '" data-teks="' + k + '" type="text" value="' + (vals[k] || "") + '">' +
          '<p class="tiny">' + (s.hint || "") + "</p></div>"
        );
      })
      .join("");
    pb.querySelectorAll("[data-teks]").forEach((el) => {
      el.onchange = () => postSettings({ [el.dataset.teks]: el.value });
    });
  }
}

async function postSettings(values) {
  try {
    const r = await fetch("/api/settings", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ values }),
    });
    if (!r.ok) throw new Error("server " + r.status);
    const j = await r.json();
    applyServerValues(j.values);
    renderAdv(j);
    setStatus("Settings saved");
    diag("tts", "settings: " + JSON.stringify(values));
  } catch (e) {
    setStatus("Could not save settings: " + e.message);
  }
}

async function applyPreset(name) {
  try {
    const r = await fetch("/api/settings", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ preset: name }),
    });
    if (!r.ok) throw new Error("server " + r.status);
    const j = await r.json();
    applyServerValues(j.values);
    renderAdv(j);
    setStatus(name === "story" ? "Bedtime story ready — tokens 16000, 3× parallel" : "Preset: " + name);
  } catch (e) {
    setStatus("Could not apply preset: " + e.message);
  }
}

async function loadServerSettings() {
  try {
    const j = await (await fetch("/api/settings")).json();
    applyServerValues(j.values);
    renderAdv(j);
  } catch (e) {
    diag("tts", "settings gagal dimuat: " + e.message);
  }
}

/* ---------------- diagnostik ---------------- */
async function testMic() {
  try {
    const st = await navigator.mediaDevices.getUserMedia({ audio: true });
    st.getTracks().forEach((t) => t.stop());
    diag("mic", "access OK");
  } catch (e) {
    diag("mic", "GAGAL: " + (e.name || e.message));
  }
  renderDiag();
}

async function runTtsTest() {
  diag("tts", "tes server…");
  renderDiag();
  try {
    const t0 = performance.now();
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text: "Tes suara dari panel diagnosa.", voice: S.voice, rate: S.tempo }),
    });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(res.status + " " + body.slice(0, 90));
    }
    const blob = await res.blob();
    const ms = Math.round(performance.now() - t0);
    diag("tts", "server OK · " + blob.size + " byte · " + ms + "ms");
    await playBlob(blob);
  } catch (e) {
    diag("tts", "server GAGAL: " + e.message);
    try {
      await speakBrowser("Tes suara bawaan HP.");
      diag("tts", "cadangan browser OK");
    } catch (e2) {
      diag("tts", "cadangan browser GAGAL: " + e2.message);
    }
  }
  renderDiag();
}

function renderDiag() {
  const box = $("diagBox");
  if (!box) return;
  const hasSR = !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  const hasSS = "speechSynthesis" in window;
  const nVoices = hasSS ? (window.speechSynthesis.getVoices() || []).length : 0;
  const idVoice = hasSS
    ? (window.speechSynthesis.getVoices() || []).find((v) => /^id/i.test(v.lang))
    : null;
  const rows = [
    ["Voice", (S.serverInfo && S.serverInfo.engine ? S.serverInfo.engine : "unknown") + " · speed " + ((S.serverInfo && S.serverInfo.rate) || "-20%"), true],
    ["Device fallback", S.browserFallback ? "on (timbre may change if the server fails)" : "off (single voice)", true],
    ["Speech recognition", hasSR ? "available" : "MISSING — use Chrome, not a WebView", hasSR],
    ["TTS server", S.diag.tts || "not tested", !!S.diag.tts && !/GAGAL|gagal/i.test(S.diag.tts)],
    ["TTS browser", hasSS ? "available · " + nVoices + " voices" + (idVoice ? " · " + idVoice.name : " · (no Indonesian voice)") : "MISSING", hasSS],
    ["Speak replies", S.speakReply ? "on" : "off", S.speakReply],
    ["Auto listen", S.autoListen ? "on" : "off", S.autoListen],
    ["Last speech log", S.diag.stt || "-", !!S.diag.stt && !/error|gagal/i.test(S.diag.stt)],
    ["Mic test", S.diag.mic || "not tested", S.diag.mic === "access OK"],
  ];
  box.innerHTML = rows
    .map((r) => {
      const color = r[2] ? "#3ecf8e" : "#e0a458";
      return '<div class="fact"><div><b>' + escapeHtml(r[0]) + "</b><br><span style='color:" + color + "'>" +
        escapeHtml(String(r[1])) + "</span></div></div>";
    })
    .join("");
}

/* ---------------- sheet ---------------- */
async function openSheet(tab) {
  const main = $("sheet"), diagS = $("diagSheet");
  if (tab === "diag") {
    main.classList.remove("open");
    diagS.classList.add("open");
    $("diagTitle").textContent = "Diagnostik";
    renderDiag();
    return;
  }
  diagS.classList.remove("open");
  main.classList.add("open");
  if (tab === "memory") {
    $("sheetTitle").textContent = "Memori Kosmate";
    $("sheetHint").textContent = "Facts remembered about you. Delete a wrong one and it forgets immediately.";
    await loadFacts();
  } else {
    $("sheetTitle").textContent = "Pengaturan";
    $("sheetHint").textContent = "Data memori disimpan lokal di HP ini (SQLite). Yang keluar cuma teks ke provider LLM dan teks ke TTS.";
  }
}

async function loadFacts() {
  const wrap = $("facts");
  wrap.innerHTML = '<div class="tiny">memuat…</div>';
  try {
    const r = await fetch("/api/memory/facts?limit=40");
    const j = await r.json();
    const facts = j.facts || [];
    $("memStats").textContent = facts.length + " facts";
    if (!facts.length) {
      wrap.innerHTML = "";
      $("factHint").style.display = "block";
      return;
    }
    $("factHint").style.display = "none";
    wrap.innerHTML = "";
    facts.forEach((f) => {
      const d = document.createElement("div");
      d.className = "fact";
      d.innerHTML = "<div><b>" + escapeHtml(f.predicate) + "</b> " + escapeHtml(f.object) + "</div>";
      const b = document.createElement("button");
      b.textContent = "×";
      b.onclick = async () => {
        await fetch("/api/memory/facts/" + f.id, { method: "DELETE" });
        d.remove();
      };
      d.appendChild(b);
      wrap.appendChild(d);
    });
  } catch (e) {
    wrap.innerHTML = '<div class="tiny">Could not load memory</div>';
  }
}

/* ---------------- misc ---------------- */
let wakeLock = null;
async function requestWakeLock() {
  try {
    if ("wakeLock" in navigator) wakeLock = await navigator.wakeLock.request("screen");
  } catch (e) {}
}
function unlockAudio() {
  if (S.unlocked) return;
  S.unlocked = true;
  const a = new Audio("data:audio/mp3;base64,//uQxAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAACcQCA");
  a.play().catch(() => {});
  if (S.pendingGreeting) { enqueueSpeech(S.pendingGreeting); S.pendingGreeting = ""; }
}

async function boot() {
  loadSettings();
  syncToggles();
  bind();
  S.rec = initRecognition();
  if (!S.rec) {
    $("micBtn").title = "record and send (server STT)";
    diag("stt", "browser ini gak punya SpeechRecognition (Fully Kiosk/WebView?)");
  }
  if ("speechSynthesis" in window) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
  }
  setInterval(heartbeat, 3000);
  try {
    const h = await (await fetch("/api/health")).json();
    $("healthDot").className = "dot " + (h.llm_key ? "ok" : "err");
    $("memCount").textContent = (h.memory ? h.memory.facts : 0) + " facts";
    const engine = h.voice ? h.voice.label : (h.fish_key ? "Fish" : "edge");
    if ($("brandSub")) $("brandSub").textContent = engine;
    S.serverInfo = { voice: h.tts_voice, rate: h.tts_rate, strict: h.tts_strict, fish: h.fish_key, ref: h.fish_ref, engine, active: h.voice };
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("sw.js", { scope: "./" })
        .then(() => diag("app", "service worker aktif"))
        .catch((e) => diag("app", "SW gagal: " + e.message));
    }
    await loadVoices();
    updateVoiceChip();
    await loadServerSettings();
    // kalau voice aktif berbasis Fish, matikan cadangan suara HP biar timbre gak ganti
    if (h.voice && h.voice.engine === "fish") {
      S.browserFallback = false;
      syncToggles();
    }
    setStatus(h.llm_key ? "Tap to talk" : "Add your API key in .env first");
  } catch (e) {
    $("healthDot").className = "dot err";
    setStatus("server gak nyahut");
  }
  requestWakeLock();
  setState("idle");

  try {
    const g = await (await fetch("/api/greeting", { method: "POST" })).json();
    if (g.text) {
      S.replyText = g.text;
      S.youSaid = "";
      showReply();
      if (S.unlocked) enqueueSpeech(g.text);
      else S.pendingGreeting = g.text;
    }
  } catch (e) {}
}

boot();
