/* ============================================================
   i18n: Bahasa Indonesia awam <-> English
   Dipakai Bu Sari: istilah teknis disembunyikan, label jadi bahasa sehari-hari.
   Cara kerja: kamus id/teks asli -> teks Indonesia, diterapkan lewat selector.
   ============================================================ */
(function () {
  const KEY = "kosmate.lang";

  /* [selector, teks-EN-asli, teks-ID] */
  const KAMUS = [
    ["#status", null, null],
    [".mode-chip[data-mode='temen']", "Companion", "Teman"],
    [".mode-chip[data-mode='tutor']", "Tutor", "Belajar"],
    [".mode-chip[data-mode='kerja']", "Work", "Kerja"],
    [".mode-chip[data-mode='cerita']", "Story", "Cerita"],
    ["#actBtn .lbl", "Actions", "Menu"],
    ["#memBtn .lbl", "Memory", "Ingatan"],
    ["#diagBtn .lbl", "Diagnostics", "Cek Suara"],
    ["#gear .lbl", "Settings", "Setelan"],
    ["#actTitle", "Quick actions", "Menu Cepat"],
    ["#sheetTitle", "Settings", "Setelan"],
    ["#diagTitle", "Diagnostics", "Cek Suara"],
    ["#input", "__placeholder__", "Tulis pesan…"],
    [".voicechip", null, null],
  ];

  /* label grup setelan: EN -> ID */
  const GRUP = {
    Voice: "Suara",
    Listening: "Dengar & jawab",
    Advanced: "Lanjutan",
    Personality: "Kepribadian",
    "Notes (quiz me)": "Catatan (buat kuis)",
    "Data & usage": "Data & pemakaian",
    Memory: "Ingatan",
    "Display & language": "Tampilan & Bahasa",
  };

  /* teks EN di dalam grup -> ID */
  const TEKS = {
    "Tap to talk": "Ketuk buat ngobrol",
    "Listening…": "Lagi dengerin…",
    "Thinking…": "Lagi mikir…",
    "Speaking…": "Lagi ngomong…",
    Close: "Tutup",
    Done: "Selesai",
    "Test voice": "Tes suara",
    "Test mic": "Tes mic",
    "Export memory": "Simpan ingatan",
    "Import memory": "Pulihkan ingatan",
    "Choose file": "Pilih file",
    "Bedtime story": "Cerita tidur",
    "Fast chat": "Ngobrol cepat",
    Reset: "Kembalikan awal",
    "Stop focus": "Stop fokus",
    "Set up story": "Atur cerita",
    "Wake word “Hei Kai”": "Panggil “Hei Kai”",
    "Auto listen": "Dengar terus",
    "Speak replies": "Bacakan jawaban",
    "Device voice fallback": "Suara cadangan HP",
    Speed: "Kecepatan",
    "Speech engine": "Mesin suara",
    "Speak in": "Cara baca",
    "Silence wait (ms)": "Tunggu diam (ms)",
    "Post-speech delay (ms)": "Jeda setelah ngomong (ms)",
    Today: "Hari ini",
    "This week": "Minggu ini",
    Reminder: "Pengingat",
    Focus: "Fokus",
    Journal: "Jurnal",
  };

  let lang = "id";
  try { lang = localStorage.getItem(KEY) || "id"; } catch (e) {}

  function terapkan() {
    const id = lang === "id";
    document.documentElement.setAttribute("data-lang", lang);

    /* grup setelan */
    document.querySelectorAll(".group-title").forEach((el) => {
      const asli = el.dataset.en || el.textContent.trim();
      el.dataset.en = asli;
      el.textContent = id && GRUP[asli] ? GRUP[asli] : asli;
    });

    /* teks tombol/label yang isinya persis cocok */
    document.querySelectorAll("button, .btn, .hint, .status, .tiny, label, h3, p").forEach((el) => {
      if (el.children.length) return;
      const asli = el.dataset.en || el.textContent.trim();
      if (!asli) return;
      if (!el.dataset.en) el.dataset.en = asli;
      if (id && TEKS[asli]) el.textContent = TEKS[asli];
      else if (!id) el.textContent = asli;
    });

    /* mode chip */
    const chipId = { temen: "Teman", tutor: "Belajar", kerja: "Kerja", cerita: "Cerita" };
    const chipEn = { temen: "Companion", tutor: "Tutor", kerja: "Work", cerita: "Story" };
    document.querySelectorAll(".mode-chip").forEach((c) => {
      const m = c.dataset.mode;
      if (m) c.textContent = id ? chipId[m] : chipEn[m];
    });

    /* nav */
    const nav = { actBtn: ["Menu", "Actions"], memBtn: ["Ingatan", "Memory"],
                  diagBtn: ["Cek Suara", "Diagnostics"], gear: ["Setelan", "Settings"] };
    Object.entries(nav).forEach(([idEl, [i, e]]) => {
      const lbl = document.querySelector("#" + idEl + " .lbl");
      if (lbl) lbl.textContent = id ? i : e;
    });

    /* judul sheet + placeholder input */
    const at = document.getElementById("actTitle");
    if (at) at.textContent = id ? "Menu Cepat" : "Quick actions";
    const st = document.getElementById("sheetTitle");
    if (st) st.textContent = id ? "Setelan" : "Settings";
    const dt = document.getElementById("diagTitle");
    if (dt) dt.textContent = id ? "Cek Suara" : "Diagnostics";
    const inp = document.getElementById("input");
    if (inp) inp.placeholder = id ? "Tulis pesan…" : "Message";
  }

  EX.setLang = function (v) {
    lang = v === "en" ? "en" : "id";
    try { localStorage.setItem(KEY, lang); } catch (e) {}
    terapkan();
    setStatus(lang === "id" ? "Bahasa: Indonesia" : "Language: English");
  };
  EX.lang = () => lang;

  /* terapkan setelah DOM siap (setelan di-render JS, jadi ulang setelah 1.2s) */
  if (document.readyState !== "loading") {
    terapkan();
    setTimeout(terapkan, 1200);
  } else {
    document.addEventListener("DOMContentLoaded", () => {
      terapkan();
      setTimeout(terapkan, 1200);
    });
  }
})();

/* ============================================================
   Ukuran tampilan: kecil / sedang / besar
   Dipakai zoom supaya semua elemen (tombol, ikon, teks) ikut membesar
   tanpa perlu mengubah ratusan nilai px.
   ============================================================ */
(function () {
  const KEY = "kosmate.zoom";
  let skala = 1;
  try { skala = Number(localStorage.getItem(KEY)) || 1; } catch (e) {}

  function pasang() {
    const app = document.querySelector(".app");
    if (app) app.style.zoom = String(skala);
    document.documentElement.style.setProperty("--skala", String(skala));
  }

  EX.setZoom = function (v) {
    skala = [0.95, 1, 1.1, 1.2].includes(Number(v)) ? Number(v) : 1;
    try { localStorage.setItem(KEY, String(skala)); } catch (e) {}
    pasang();
    setStatus("Ukuran tampilan: " + Math.round(skala * 100) + "%");
  };
  EX.zoom = () => skala;

  if (document.readyState !== "loading") pasang();
  else document.addEventListener("DOMContentLoaded", pasang);
})();
