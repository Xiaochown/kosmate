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
let speechQueue = 0; // jumlah kalimat yang belum selesai diucapkan
let speechGen = 0; // naik setiap kali user memotong; antrean lama jadi basi
let currentAudio = null;

function speakable(t) {
  return (t || "").replace(/[*_`#>~]/g, "").replace(/\[(.*?)\]\(.*?\)/g, "$1").trim();
}

function enqueueSpeech(text) {
  const t = speakable(text);
  if (!t || !S.speakReply) return;
  speechQueue++;
  const gen = speechGen;
  speakChain = speakChain
    .then(() => {
      if (gen !== speechGen) return; // sudah dipotong, jangan diucapkan
      return speakOne(t);
    })
    .catch(() => {});
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

async function speakOne(text) {
  setState("speaking");
  try {
    if (S.ttsMode !== "browser") {
      try {
        const t0 = performance.now();
        const res = await fetch("/api/tts", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ text, voice: S.voice, rate: S.tempo }),
        });
        if (!res.ok) throw new Error("server " + res.status);
        const blob = await res.blob();
        if (blob.size < 800) throw new Error("audio kosong (" + blob.size + " byte)");
        await playBlob(blob);
        diag("tts", "server OK · " + blob.size + " byte · " + Math.round(performance.now() - t0) + "ms");
        return;
      } catch (e) {
        diag("tts", "server gagal: " + e.message);
        if (S.ttsMode === "server") throw e;
        if (!S.browserFallback) {
          throw new Error(e.message + " (cadangan suara HP dimatikan biar suara gak ganti)");
        }
      }
    }
    // cadangan: suara bawaan HP
    await speakBrowser(text);
    diag("tts", "pakai suara bawaan browser (offline)");
  } catch (e) {
    diag("tts", "SEMUA jalur suara gagal: " + e.message);
    setStatus("suara gak keluar — buka ⚙ → Diagnostik");
  } finally {
    speechQueue = Math.max(0, speechQueue - 1);
    if (speechQueue === 0) {
      // seluruh jawaban sudah selesai diucapkan -> baru boleh dengar lagi
      S.speaking = false;
      S.lastSpoken = speakable(S.replyText || "");
      setState(S.autoListen ? "listening" : "idle");
      if (S.autoListen) scheduleListen();
    }
  }
}

/* jeda sebelum mic nyala lagi: kasih waktu gema speaker hilang */
function scheduleListen() {
  clearTimeout(S.listenTimer);
  const wait = Math.max(200, Number(S.cooldownMs) || 900);
  S.listenTimer = setTimeout(() => {
    if (!S.autoListen || S.speaking || S.busy || speechQueue > 0) return;
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
  speechQueue = 0;
  speakChain = Promise.resolve();
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
    const err = e.error || "unknown";
    S.recErrors = (S.recErrors || 0) + 1;
    diag("stt", "error: " + err + " (ke-" + S.recErrors + ")");
    if (err === "not-allowed" || err === "service-not-allowed") {
      setStatus("izin mic ditolak. Chrome → Site settings → Microphone → izinkan 127.0.0.1");
      S.autoListen = false;
      syncToggles();
    } else if (err === "no-speech" || err === "aborted") {
      // normal: user diam. biarkan onend yang nyalain ulang
    } else if (err === "network") {
      setStatus("STT butuh internet — cek koneksi");
    } else if (err === "audio-capture") {
      setStatus("mic dipakai app lain? tutup app yang pakai mic");
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
  if (!S.rec || S.speaking || S.busy || S.listening || speechQueue > 0) return;
  scheduleListen();
}

/* heartbeat: kalau karena alasan apa pun pendengar mati diam-diam, nyalain lagi */
function heartbeat() {
  if (!S.autoListen || !S.rec) return;
  if (S.listening || S.speaking || S.busy) return;
  if (speechQueue > 0) return; // masih ada kalimat yang belum selesai diucapkan
  if (S.state === "listening") return;
  diag("stt", "heartbeat: pendengar mati, dinyalakan ulang");
  startListening(true);
}

function startListening(auto) {
  if (!S.rec) {
    setStatus("browser ini gak dukung STT — buka di Chrome (bukan Fully Kiosk)");
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
    if (S.speaking || speechQueue > 0) {
      stopSpeaking();
      setStatus("dipotong. ketuk lagi kalau mau ngomong");
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
      setStatus("mode <strong>" + b.dataset.mode + "</strong> aktif");
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
      diag("stt", "auto-dengerin dinyalakan");
      if (!S.rec) {
        setStatus("auto-dengerin butuh Chrome (browser ini gak punya STT)");
      } else {
        startListening(true);
      }
    } else {
      stopRecognition(false);
      setState("idle");
    }
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
    setStatus("jeda dengerin: <strong>" + n + " ms</strong> (" + (n / 1000).toFixed(1) + " detik)");
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
        ? "Fish Audio siap. Pilih salah satu — kalau Fish gagal, Kosmate <b>diam</b>, tidak ganti suara lain."
        : "FISH_API_KEY belum diisi di .env — voice Fish belum bisa dipakai. Isi dulu, lalu muat ulang halaman.";
    }
  } catch (e) {
    diag("tts", "gagal muat daftar suara: " + e.message);
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
    setStatus("suara: <strong>" + j.active.label + "</strong> · " + j.active.rate);
    await runTtsTest();
  } catch (e) {
    diag("tts", "gagal ganti voice: " + e.message);
    setStatus("gagal ganti suara: " + e.message);
  }
}

/* ---------------- diagnostik ---------------- */
async function testMic() {
  try {
    const st = await navigator.mediaDevices.getUserMedia({ audio: true });
    st.getTracks().forEach((t) => t.stop());
    diag("mic", "akses OK");
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
    ["Suara dipakai", (S.serverInfo && S.serverInfo.engine ? S.serverInfo.engine : "belum tahu") + " · tempo " + ((S.serverInfo && S.serverInfo.rate) || "-20%"), true],
    ["Cadangan suara HP", S.browserFallback ? "aktif (bisa ganti timbre kalau server gagal)" : "mati (suara tetap satu)", true],
    ["STT (Web Speech)", hasSR ? "ada" : "TIDAK ADA → pakai Chrome, bukan Fully Kiosk", hasSR],
    ["TTS server", S.diag.tts || "belum dites", !!S.diag.tts && !/GAGAL|gagal/i.test(S.diag.tts)],
    ["TTS browser", hasSS ? "ada · " + nVoices + " suara" + (idVoice ? " · " + idVoice.name : " · (voice id-ID gak ketemu)") : "TIDAK ADA", hasSS],
    ["Bicara otomatis", S.speakReply ? "aktif" : "nonaktif", S.speakReply],
    ["Dengerin otomatis", S.autoListen ? "aktif" : "nonaktif", S.autoListen],
    ["Log terakhir STT", S.diag.stt || "-", !!S.diag.stt && !/error|gagal/i.test(S.diag.stt)],
    ["Mic (tes manual)", S.diag.mic || "belum dites", S.diag.mic === "akses OK"],
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
    diag("stt", "browser ini gak punya SpeechRecognition (Fully Kiosk/WebView?)");
  }
  if ("speechSynthesis" in window) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
  }
  setInterval(heartbeat, 3000);
  try {
    const h = await (await fetch("/api/health")).json();
    $("brandName").textContent = h.name || "Kosmate";
    $("healthDot").className = "dot " + (h.llm_key ? "ok" : "err");
    $("memCount").textContent = (h.memory ? h.memory.facts : 0) + " fakta";
    const engine = h.voice ? h.voice.label : (h.fish_key ? "Fish" : "edge · Gadis");
    $("brandSub").textContent = engine;
    S.serverInfo = { voice: h.tts_voice, rate: h.tts_rate, strict: h.tts_strict, fish: h.fish_key, ref: h.fish_ref, engine, active: h.voice };
    await loadVoices();
    // kalau voice aktif berbasis Fish, matikan cadangan suara HP biar timbre gak ganti
    if (h.voice && h.voice.engine === "fish") {
      S.browserFallback = false;
      syncToggles();
    }
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
