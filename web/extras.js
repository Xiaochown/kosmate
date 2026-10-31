/* Kosmate — fitur lanjutan: aksi cepat, fokus, pengingat, jurnal, catatan (RAG),
   kuota, ekspor/impor, wake word. Dimuat setelah app.js (pakai S & helper-nya). */

const $x = (id) => document.getElementById(id);
const EX = {
  wake: false,
  wakeRec: null,
  focusTimer: null,
  focusLeft: 0,
  focusTotal: 0,
  usageTimer: null,
};

/* ------------------------------- AKSI CEPAT ------------------------------- */
function bukaAksi() {
  $x("actSheet").classList.add("open");
  muatPengingat();
  muatJurnal();
  muatKuota();
}

async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error("HTTP " + res.status + (txt ? " · " + txt.slice(0, 120) : ""));
  }
  return res.json().catch(() => ({}));
}

/* ------------------------------- FOKUS ------------------------------- */
function mulaiFokus(menit) {
  hentikanFokus(false);
  EX.focusTotal = menit * 60;
  EX.focusLeft = EX.focusTotal;
  enqueueSpeech(`Oke, fokus ${menit} menit. Gue temenin, jangan kemana-mana dulu.`);
  setStatus(`Focus · ${menit}:00 left`);
  EX.focusTimer = setInterval(() => {
    EX.focusLeft--;
    const m = Math.floor(EX.focusLeft / 60);
    const s = String(EX.focusLeft % 60).padStart(2, "0");
    setStatus(`Focus · ${m}:${s} left`);
    if (EX.focusLeft === Math.floor(EX.focusTotal / 2)) {
      enqueueSpeech("Setengah jalan. Bagus, lanjutin dikit lagi.");
    }
    if (EX.focusLeft <= 0) {
      hentikanFokus(false);
      enqueueSpeech("Selesai. Berdiri, minum air, istirahat lima menit ya.");
      setState("idle");
    }
  }, 1000);
}

function hentikanFokus(bilang = true) {
  if (EX.focusTimer) clearInterval(EX.focusTimer);
  EX.focusTimer = null;
  const tombol = $x("focusStop");
  if (tombol) tombol.hidden = true;
  if (bilang) setStatus("Focus stopped");
}

async function pasangCerita() {
  await api("/api/settings", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ preset: "story" }),
  });
  await api("/api/mode", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ mode: "cerita" }),
  });
  document.querySelectorAll(".mode-chip").forEach((c) => c.classList.toggle("active", c.dataset.mode === "cerita"));
  setStatus("Story mode ready — just say what story you want");
  enqueueSpeech("Siap. Mau cerita tentang apa? Bilang aja, gue bacain sampai lu tidur.");
}

/* ------------------------------- PENGINGAT ------------------------------- */
async function muatPengingat() {
  const box = $x("remindList");
  if (!box) return;
  try {
    const j = await api("/api/reminders");
    const items = j.items || [];
    box.innerHTML = items.length
      ? items.map((r) => {
          const d = new Date(r.due_ts * 1000);
          const jam = d.toLocaleString("id-ID", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
          return `<div class="fact"><div><b>${esc(r.teks)}</b><br><span class="tiny">${jam}</span></div><button data-rid="${r.id}">×</button></div>`;
        }).join("")
      : '<p class="tiny">No reminders yet.</p>';
    box.querySelectorAll("button[data-rid]").forEach((b) => {
      b.onclick = async () => {
        await api("/api/reminders/" + b.dataset.rid, { method: "DELETE" });
        muatPengingat();
      };
    });
  } catch (e) {
    box.innerHTML = '<p class="tiny">Could not load reminders.</p>';
  }
}

async function tambahPengingat(teks, kapan) {
  if (!teks) return;
  try {
    const r = await api("/api/reminders", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ teks, kapan }),
    });
    const jam = new Date(r.due_ts * 1000).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
    setStatus("Reminder set for " + jam);
    muatPengingat();
    $x("remindTeks").value = "";
  } catch (e) {
    setStatus("Could not set reminder: " + e.message);
  }
}

function cekPengingat() {
  api("/api/reminders/due")
    .then((j) => {
      (j.items || []).forEach((r) => {
        enqueueSpeech("Pengingat: " + r.teks);
        setStatus("Reminder: " + esc(r.teks));
        if (window.Notification && Notification.permission === "granted") {
          try { new Notification("Kosmate", { body: r.teks }); } catch (e) {}
        }
      });
      if ((j.items || []).length) muatPengingat();
    })
    .catch(() => {});
}

/* ------------------------------- JURNAL ------------------------------- */
async function muatJurnal() {
  const box = $x("journalList");
  if (!box) return;
  try {
    const j = await api("/api/journal");
    const items = j.items || [];
    box.innerHTML = items.length
      ? items.map((r) => `<div class="fact"><div><b>${r.hari}</b><br><span class="tiny">${esc(r.teks.slice(0, 140))}…</span></div></div>`).join("")
      : '<p class="tiny">No entries yet.</p>';
  } catch (e) {
    box.innerHTML = '<p class="tiny">Could not load journal.</p>';
  }
}

async function tulisJurnal(period) {
  setStatus("Writing summary…");
  try {
    const r = await api("/api/journal", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ period }),
    });
    S.replyText = r.teks;
    S.youSaid = "summary";
    showReply();
    enqueueSpeech(r.teks);
    muatJurnal();
    setStatus("Saved to journal");
  } catch (e) {
    setStatus("Could not write summary: " + e.message);
  }
}

/* ------------------------------- CATATAN (RAG) ------------------------------- */
async function muatCatatan() {
  const box = $x("notesList");
  if (!box) return;
  try {
    const j = await api("/api/notes");
    const items = j.items || [];
    box.innerHTML = items.length
      ? items.map((r) => `<div class="fact"><div><b>${esc(r.judul)}</b><br><span class="tiny">${r.potongan} potongan</span></div><button data-did="${r.id}">×</button></div>`).join("")
      : '<p class="tiny">No notes yet. Upload your lecture notes and Kai can quiz you.</p>';
    box.querySelectorAll("button[data-did]").forEach((b) => {
      b.onclick = async () => {
        await api("/api/notes/" + b.dataset.did, { method: "DELETE" });
        muatCatatan();
      };
    });
  } catch (e) {
    box.innerHTML = '<p class="tiny">Could not load notes.</p>';
  }
}

async function unggahCatatan(file) {
  if (!file) return;
  setStatus("Uploading " + file.name + "…");
  const fd = new FormData();
  fd.append("file", file);
  fd.append("judul", file.name.replace(/\.[a-z]+$/i, ""));
  try {
    const r = await api("/api/notes", { method: "POST", body: fd });
    setStatus(`Added “${r.judul}” · ${r.potongan} chunks`);
    muatCatatan();
  } catch (e) {
    setStatus("Upload failed: " + e.message);
  }
}

/* ------------------------------- KUOTA ------------------------------- */
function fmt(n) {
  if (n >= 1000) return (n / 1000).toFixed(1) + "k";
  return String(n);
}

async function muatKuota() {
  try {
    const u = await api("/api/usage");
    const el = $x("usageBox");
    if (el) {
      el.innerHTML =
        `Today · LLM <b>${fmt(u.llm_tokens)}</b> tokens · TTS <b>${fmt(u.tts_chars)}</b> chars` +
        ` (${u.tts_calls} calls)`;
    }
    const hdr = $x("quotaPill");
    if (hdr) hdr.textContent = fmt(u.llm_tokens) + " tok";
  } catch (e) {}
}

/* ------------------------------- EKSPOR / IMPOR ------------------------------- */
function eksporMemori() {
  window.location.href = "/api/export";
  setStatus("Downloading memory backup…");
}

async function imporMemori(file) {
  if (!file) return;
  try {
    const teks = await file.text();
    const data = JSON.parse(teks);
    const r = await api("/api/import", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(data),
    });
    setStatus(`Imported ${r.episodes} messages · ${r.facts} facts`);
  } catch (e) {
    setStatus("Import failed: " + e.message);
  }
}

/* ------------------------------- WAKE WORD ------------------------------- */
function stopWake() {
  EX.wake = false;
  if (EX.wakeRec) {
    try { EX.wakeRec.abort(); } catch (e) {}
    EX.wakeRec = null;
  }
  const b = $x("setWake");
  if (b) { b.classList.remove("on"); b.innerHTML = '<span class="dot"></span>off'; }
}

function startWake() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    setStatus("Wake word needs Chrome (no speech recognition here)");
    return;
  }
  EX.wake = true;
  const r = new SR();
  r.lang = "id-ID";
  r.continuous = true;
  r.interimResults = true;
  r.onresult = (e) => {
    let t = "";
    for (let i = e.resultIndex; i < e.results.length; i++) t += e.results[i][0].transcript;
    if (/\b(hai|hei|hey|halo|woi)?\s*kai\b/i.test(t)) {
      diag("stt", "wake word: " + t.slice(0, 30));
      try { r.abort(); } catch (err) {}
      EX.wakeRec = null;
      S.finalText = "";
      setStatus("Yes?");
      setTimeout(() => startListening(true), 250);
    }
  };
  r.onerror = (e) => {
    if (e.error === "not-allowed") { stopWake(); setStatus("Mic blocked — wake word off"); }
  };
  r.onend = () => {
    if (EX.wake && !S.speaking && !S.listening && !S.busy) {
      setTimeout(() => { try { r.start(); } catch (err) {} }, 700);
    }
  };
  EX.wakeRec = r;
  try { r.start(); } catch (e) {}
  const b = $x("setWake");
  if (b) { b.classList.add("on"); b.innerHTML = '<span class="dot ok"></span>on'; }
  setStatus('Wake word on — say "Hei Kai"');
}

/* ------------------------------- util ------------------------------- */
function esc(s) {
  return String(s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

/* ------------------------------- BIND ------------------------------- */
function initExtras() {
  const on = (id, fn) => { const el = $x(id); if (el) el.addEventListener("click", fn); };

  on("actBtn", bukaAksi);
  on("closeAct", () => $x("actSheet").classList.remove("open"));

  // kartu aksi
  on("cardStory", () => { pasangCerita(); $x("actSheet").classList.remove("open"); });
  // delegasi klik: tahan terhadap elemen yang di-render ulang & innerHTML
  document.addEventListener("click", (ev) => {
    const t = ev.target && ev.target.closest ? ev.target.closest("[data-focus],[data-kapan]") : null;
    if (!t) return;
    if (t.dataset.focus) {
      mulaiFokus(Number(t.dataset.focus));
      const stop = $x("focusStop");
      if (stop) stop.hidden = false;
      return;
    }
    if (t.dataset.kapan) {
      const teks = ($x("remindTeks").value || "").trim();
      if (!teks) { setStatus("Type what to remind first"); return; }
      tambahPengingat(teks, t.dataset.kapan);
    }
  });
  on("focusStop", () => { hentikanFokus(true); enqueueSpeech("Oke, fokus gue stop."); });

  // pengingat
  on("remindAdd", () => {
    const teks = ($x("remindTeks").value || "").trim();
    const kapan = $x("remindKapan").value || "10 menit";
    tambahPengingat(teks, kapan);
  });

  // jurnal
  on("journalDay", () => tulisJurnal("day"));
  on("journalWeek", () => tulisJurnal("week"));

  // catatan
  const fi = $x("notesFile");
  if (fi) fi.addEventListener("change", (e) => unggahCatatan(e.target.files && e.target.files[0]));

  // data
  on("btnExport", eksporMemori);
  const imp = $x("importFile");
  if (imp) imp.addEventListener("change", (e) => imporMemori(e.target.files && e.target.files[0]));

  // wake word
  on("setWake", () => {
    if (EX.wake) { stopWake(); setStatus("Wake word off"); }
    else startWake();
  });

  // poll
  setInterval(cekPengingat, 20000);
  setInterval(muatKuota, 60000);
  muatKuota();
  muatCatatan();
}

setTimeout(initExtras, 400);
