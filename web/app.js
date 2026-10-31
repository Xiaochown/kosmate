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
};

/* ---------------- settings ---------------- */
function loadSettings() {
  try {
    const s = JSON.parse(localStorage.getItem(LS) || "{}");
    Object.assign(S, {
      autoListen: !!s.autoListen,
      speakReply: s.speakReply !== false,
      silenceMs: Number(s.silenceMs || 900),
      voice: s.voice || "id-ID-GadisNeural",
    });
  } catch (e) {}
}
function saveSettings() {
  localStorage.setItem(LS, JSON.stringify({
    autoListen: S.autoListen, speakReply: S.speakReply,
    silenceMs: S.silenceMs, voice: S.voice,
  }));
}

/* ---------------- ui helpers ---------------- */
function setState(st) {
  S.state = st;
  document.body.dataset.state = st;
  const label = {
    idle: "santai… ketuk orb buat ngobrol",
    listening: "gue dengerin…",
    thinking: "mikir sebentar…",
    speaking: "lagi ngomong…",
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
  $("replyYou").textContent = S.youSaid ? "lu: " + S.youSaid : "";
  $("replyText").textContent = S.replyText;
  if (S.replyText) r.classList.add("show");
}
function clearReply() { $("reply").classList.remove("show"); }

/* ---------------- TTS ---------------- */
let speakChain = Promise.resolve();
const audioQueue = [];
let playing = false;
let currentAudio = null;

function speakable(t) {
  return (t || "").replace(/[*_`#>~]/g, "").replace(/\[(.*?)\]\(.*?\)/g, "$1").trim();
}

function enqueueSpeech(text) {
  const t = speakable(text);
  if (!t || !S.speakReply) return;
  speakChain = speakChain.then(() => speakOne(t)).catch(() => {});
}

async function speakOne(text) {
  try {
    setState("speaking");
    const res = await fetch("/api/tts", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text, voice: S.voice }),
    });
    if (!res.ok) throw new Error("tts " + res.status);
    const blob = await res.blob();
    await playBlob(blob);
  } catch (e) {
    console.warn("tts gagal", e);
  } finally {
    if (!playing) {
      setState(S.listening ? "listening" : "idle");
      if (S.autoListen) startListening(true);
    }
  }
}

function playBlob(blob) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(blob);
    const a = new Audio(url);
    a.crossOrigin = "anonymous";
    currentAudio = a;
    S.speaking = true;
    stopRecognition(true);
    const done = () => {
      URL.revokeObjectURL(url);
      S.speaking = false;
      currentAudio = null;
      resolve();
    };
    a.onended = done;
    a.onerror = done;
    a.play().catch(done);
  });
}

/* ---------------- sentence streaming ---------------- */
function boundaryIndex(t) {
  for (let i = 0; i < t.length; i++) {
    if (".!?…\n".includes(t[i])) return i;
  }
  return -1;
}

function feedDelta(chunk) {
  S.replyText += chunk;
  showReply();
  let buf = (S.replyBuf || "") + chunk;
  let idx = boundaryIndex(buf);
  while (idx !== -1) {
    const sentence = buf.slice(0, idx + 1);
    buf = buf.slice(idx + 1);
    if (sentence.trim().length >= 6) enqueueSpeech(sentence);
    idx = boundaryIndex(buf);
  }
  S.replyBuf = buf;
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
          if (S.replyBuf && S.replyBuf.trim().length >= 3) enqueueSpeech(S.replyBuf);
          S.replyBuf = "";
          if (evt.memory) $("memCount").textContent = evt.memory.facts + " fakta";
        }
      }
    }
  } catch (e) {
    S.replyText = "Koneksi ke otak gue putus. Cek server masih jalan? (" + e.message + ")";
    showReply();
    enqueueSpeech("Koneksi ke otak gue putus. Cek server-nya ya.");
  } finally {
    S.busy = false;
    speakChain.then(() => {
      if (!S.speaking) setState(S.listening ? "listening" : "idle");
      if (S.autoListen) startListening(true);
    });
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
    if (e.error === "not-allowed" || e.error === "service-not-allowed") {
      setStatus("izin mic ditolak. Buka <strong>chrome://settings</strong> → Site settings → Microphone.");
      S.autoListen = false;
      syncToggles();
    }
  };
  rec.onend = () => {
    S.listening = false;
    clearTimeout(S.silenceTimer);
    const said = S.finalText.trim();
    S.finalText = "";
    if (said) {
      showLive("", "");
      sendMessage(said);
    } else if (S.autoListen && !S.speaking && !S.busy) {
      setTimeout(() => startListening(true), 400);
    } else if (!S.speaking) {
      setState("idle");
      showLive("", "");
    }
  };
  return rec;
}

function startListening(auto) {
  if (!S.rec) return;
  if (S.speaking) return;
  if (S.listening) return;
  try { S.rec.start(); } catch (e) {}
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
        else { setState("idle"); setStatus("gak kedengeran, coba lagi"); }
      } catch (e) {
        setState("idle");
        setStatus("gagal transkripsi: " + e.message);
      }
    };
    S.mediaRec = mr;
    mr.start();
    setState("listening");
    setStatus("ngerekam… ketuk mic lagi buat kirim");
  } catch (e) {
    setStatus("mic gak bisa diakses: " + e.message);
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
    if (S.speaking && currentAudio) { currentAudio.pause(); currentAudio = null; S.speaking = false; setState("idle"); return; }
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
      setStatus("mode <strong>" + b.dataset.mode + "</strong> aktif");
    };
  });

  $("gear").onclick = () => openSheet("settings");
  $("memBtn").onclick = () => openSheet("memory");
  $("closeSheet").onclick = () => $("sheet").classList.remove("open");

  $("setMode").onchange = (e) => {
    const m = e.target.value;
    document.querySelectorAll(".mode-chip").forEach((x) => x.classList.toggle("active", x.dataset.mode === m));
    fetch("/api/mode", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ mode: m }),
    });
  };
  $("setVoice").onchange = (e) => { S.voice = e.target.value; saveSettings(); };
  $("setAutoListen").onclick = () => { S.autoListen = !S.autoListen; saveSettings(); syncToggles(); };
  $("setSpeak").onclick = () => { S.speakReply = !S.speakReply; saveSettings(); syncToggles(); };
  $("setSilence").onchange = (e) => {
    const n = Math.max(300, Math.min(4000, parseInt(e.target.value || "900", 10) || 900));
    S.silenceMs = n; e.target.value = String(n); saveSettings();
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
  $("setVoice").value = S.voice;
  $("setSilence").value = String(S.silenceMs);
}

/* ---------------- sheet ---------------- */
async function openSheet(tab) {
  $("sheet").classList.add("open");
  if (tab === "memory") {
    $("sheetTitle").textContent = "Memori Kosmate";
    $("sheetHint").textContent = "Fakta yang Kosmate ingat tentang kamu. Hapus yang salah — dia langsung lupa.";
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
    $("memStats").textContent = facts.length + " fakta";
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
    wrap.innerHTML = '<div class="tiny">gagal memuat memori</div>';
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
    $("micBtn").title = "rekam lalu kirim (STT server)";
  }
  try {
    const h = await (await fetch("/api/health")).json();
    $("brandName").textContent = h.name || "Kosmate";
    $("healthDot").className = "dot " + (h.llm_key ? "ok" : "err");
    $("memCount").textContent = (h.memory ? h.memory.facts : 0) + " fakta";
    $("brandSub").textContent = h.llm + " · " + (h.tts_providers || []).join("/");
    setStatus(h.llm_key ? "ketuk orb buat mulai ngobrol" : "isi API key dulu di file .env");
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
