/* Demo layer: semua API dipalsukan supaya UI bisa dilihat tanpa server. */
(function () {
  const now = Math.floor(Date.now() / 1000);

  const VOICE = { key: "miyaa", label: "Miyaa — perempuan muda, ceria", engine: "fish", rate: "-20%", ref: "demo" };
  const VOICES = [
    VOICE,
    { key: "kdm", label: "Kang Dedi — laki-laki, ceria, ekspresif", engine: "fish", rate: "-15%", ref: "d2", ready: true },
    { key: "prabowo", label: "Prabowo — laki-laki, dalam, tegas", engine: "fish", rate: "-20%", ref: "d3", ready: true },
    { key: "gadis", label: "Gadis — edge-tts (tanpa Fish)", engine: "edge", rate: "-15%", ref: "", ready: true },
  ].map((v) => ({ ready: true, ...v }));

  const SPEC = {
    max_tokens: { label: "Max output tokens", min: 200, max: 32000, step: 100, hint: "Panjang jawaban maksimum. Cerpen 20–30 menit butuh 12000–24000." },
    temperature: { label: "Creativity (temperature)", min: 0, max: 1.5, step: 0.05, hint: "Rendah = konsisten, tinggi = lebih bebas." },
    llm_timeout: { label: "LLM read timeout (s)", min: 20, max: 600, step: 10, hint: "Jeda antar-chunk sebelum dianggap putus." },
    tts_timeout: { label: "TTS timeout (s)", min: 20, max: 600, step: 10, hint: "Batas waktu satu request suara." },
    tts_max_chars: { label: "Max chars per TTS request", min: 500, max: 60000, step: 500, hint: "Batas teks sekali kirim ke mesin suara." },
    chunk_chars: { label: "Speech chunk size (chars)", min: 120, max: 3000, step: 20, hint: "Kecil = mulai lebih cepat." },
    tts_parallel: { label: "Parallel TTS requests", min: 1, max: 4, step: 1, hint: "2–3 aman; 4 bisa kena rate limit." },
    history_messages: { label: "Conversation history", min: 0, max: 40, step: 1, hint: "Berapa pesan terakhir dikirim ulang." },
    memory_chars: { label: "Memory context (chars)", min: 0, max: 6000, step: 100, hint: "Berapa banyak memori disisipkan ke prompt." },
    story_words: { label: "Story target (words)", min: 300, max: 8000, step: 100, hint: "130 kata ≈ 1 menit suara." },
  };
  const TEKS = {
    tone: { label: "Tone", pilihan: ["santai", "lembut", "tegas"], hint: "santai = kayak teman, lembut = kalem, tegas = to the point." },
    humor: { label: "Humor (0-2)", pilihan: ["0", "1", "2"], hint: "0 serius, 1 secukupnya, 2 banyak nyeletuk." },
    nickname: { label: "Nickname", pilihan: [], hint: "Dia manggil lu apa." },
  };
  let VALUES = {
    max_tokens: 8000, temperature: 0.75, llm_timeout: 120, tts_timeout: 120, tts_max_chars: 20000,
    chunk_chars: 400, tts_parallel: 2, history_messages: 8, memory_chars: 1400, story_words: 1500,
    tone: "santai", humor: "1", nickname: "Faa",
  };
  const PRESET = {
    default: { max_tokens: 8000, temperature: 0.75, chunk_chars: 400, tts_parallel: 2 },
    story: { max_tokens: 16000, temperature: 0.9, chunk_chars: 800, tts_parallel: 3, story_words: 1800 },
    chat: { max_tokens: 4000, temperature: 0.8, chunk_chars: 400, tts_parallel: 2 },
  };

  let REMINDERS = [
    { id: 1, teks: "minum air", due_ts: now + 900 },
    { id: 2, teks: "kelas SBD jam 9", due_ts: now + 5400 },
  ];
  const FACTS = [
    { id: 1, predicate: "kuliah", object: "S1 TI UDINUS, semester 3" },
    { id: 2, predicate: "kos", object: "Semarang, dekat kampus" },
    { id: 3, predicate: "suka", object: "cerita pengantar tidur sebelum tidur" },
    { id: 4, predicate: "target", object: "network engineer + AI automation" },
  ];
  let JOURNALS = [
    { id: 1, hari: "2026-10-31", pilih: "day", teks: "Hari ini gue ngerjain catatan basis data sambil dengerin hujan. Agak capek, tapi lega karena tugasnya kelar." },
  ];
  let NOTES = [
    { id: 1, judul: "logika-informatika-pert7", potongan: 9 },
    { id: 2, judul: "sistem-basis-data-er", potongan: 6 },
  ];
  const TTS_CHARS = { n: 0 };

  const ok = (obj) => ({
    ok: true, status: 200,
    json: async () => obj,
    text: async () => JSON.stringify(obj),
    blob: async () => new Blob([new Uint8Array(4000)], { type: "audio/mpeg" }),
  });

  function sse(parts) {
    const enc = new TextEncoder();
    const frames = parts.map((p) => enc.encode("data: " + JSON.stringify(p) + "\n\n"));
    let i = 0;
    return {
      ok: true, status: 200,
      text: async () => "",
      body: {
        getReader: () => ({
          read: async () => (i < frames.length ? { value: frames[i++], done: false } : { done: true }),
        }),
      },
    };
  }

  const BALASAN = [
    "Oke, gue dengerin. ",
    "Ini versi demo, jadi gue jawab pura-pura ya. ",
    "Tapi tampilan, tombol, kartu, dan panel setelan di sini semuanya asli. ",
    "Coba buka Actions buat lihat kartu cerita, fokus, pengingat, sama jurnal. ",
    "Kalau mau versi yang beneran ngobrol, itu yang jalan di HP lu.",
  ];

  window.fetch = async function (url, opts) {
    const u = String(url);
    const path = u.replace(/^https?:\/\/[^/]+/, "").split("?")[0];
    const method = (opts && opts.method) || "GET";
    await new Promise((r) => setTimeout(r, 60));

    if (path === "/api/health")
      return ok({ ok: true, name: "Kai", llm: "demo-mode", llm_key: true, fish_key: true, fish_ref: true,
        tts_strict: true, tts_voice: "id-ID-GadisNeural", tts_rate: "-20%", voice: VOICE, stt: "demo",
        mode: "temen", tts_last_ok: "", tts_last_error: "", memory: { episodes: 42, facts: FACTS.length, notes: NOTES.length } });
    if (path === "/api/greeting") return ok({ text: "Halo Faa. Ini demo tampilan — saranku, buka Actions dulu." });
    if (path === "/api/voice")
      return method === "POST" ? ok({ active: VOICE, options: VOICES }) : ok({ active: VOICE, options: VOICES, fish_key: true });
    if (path === "/api/settings") {
      if (method === "POST") {
        const b = JSON.parse((opts && opts.body) || "{}");
        if (b.preset) VALUES = { ...VALUES, ...PRESET[b.preset] };
        else Object.assign(VALUES, b.values || b);
      }
      return ok({ spec: SPEC, teks: TEKS, presets: Object.keys(PRESET), values: VALUES });
    }
    if (path === "/api/usage") return ok({ hari: "demo", llm_tokens: 18400, tts_chars: 41200, tts_calls: 96,
      limits: { max_tokens: VALUES.max_tokens, tts_max_chars: VALUES.tts_max_chars } });
    if (path === "/api/reminders/due") return ok({ items: [] });
    if (path === "/api/reminders") {
      if (method === "POST") {
        const b = JSON.parse((opts && opts.body) || "{}");
        const r = { id: Date.now() % 1000, teks: b.teks || "pengingat", due_ts: now + 600 };
        REMINDERS.push(r);
        return ok(r);
      }
      return ok({ items: REMINDERS });
    }
    if (path.startsWith("/api/reminders/") && method === "DELETE") {
      REMINDERS = REMINDERS.filter((r) => String(r.id) !== path.split("/").pop());
      return ok({ ok: true });
    }
    if (path === "/api/journal") {
      if (method === "POST") {
        const j = { id: Date.now() % 1000, hari: "today", pilih: "day",
          teks: "Hari ini gue belajar basis data, sempat ngobrol soal normalisasi, lalu minta cerita sebelum tidur. Tenang, dan gue ngerasa lebih siap buat besok." };
        JOURNALS.unshift(j);
        return ok(j);
      }
      return ok({ items: JOURNALS });
    }
    if (path === "/api/notes") {
      if (method === "POST") {
        const n = { id: Date.now() % 1000, judul: "catatan-baru", potongan: 7 };
        NOTES.unshift(n);
        return ok(n);
      }
      return ok({ items: NOTES });
    }
    if (path.startsWith("/api/notes/") && method === "DELETE") {
      NOTES = NOTES.filter((n) => String(n.id) !== path.split("/").pop());
      return ok({ ok: true });
    }
    if (path.startsWith("/api/memory/facts")) return ok({ facts: FACTS });
    if (path === "/api/memory/stats") return ok({ episodes: 42, facts: FACTS.length, notes: NOTES.length });
    if (path === "/api/memory/context") return ok({ block: "demo" });
    if (path === "/api/export") return ok({ episodes: [], facts: FACTS, notes: [], exported_at: "demo" });
    if (path === "/api/import") return ok({ ok: true, episodes: 0, facts: 0 });
    if (path === "/api/mode") return ok({ mode: "temen" });
    if (path === "/api/chat") return sse(BALASAN.map((t) => ({ type: "delta", text: t })).concat([{ type: "done", text: "", memory: { facts: FACTS.length } }]));
    if (path === "/api/sing/songs")
      return ok({ items: [
        { kunci: "pelangi", judul: "Pelangi (nada Twinkle Twinkle)", bpm: 100, not: 14 },
        { kunci: "balon", judul: "Balonku (lagu anak)", bpm: 112, not: 12 },
      ] });
    if (path === "/api/sing") {
      const blob = new Blob([new Uint8Array(8192)], { type: "audio/mpeg" });
      return { ok: true, status: 200, json: async () => ({}), text: async () => "", blob: async () => blob };
    }
    if (path === "/api/announce") return ok({ items: [] });
    if (path === "/api/tokens") return ok({ items: [] });
    if (path === "/api/briefing")
      return ok({ ada: true, teks: "Selamat pagi. Jurnal terakhir: semalam gue belajar resolusi. Pengingat hari ini: 09:00 kelas SBD." });
    if (path === "/api/metrics")
      return ok({
        llm_first_token: { n: 12, rata: 640.2, p95: 910.0, akhir: 702.1 },
        llm_total: { n: 12, rata: 3200.5, p95: 4100.0, akhir: 3010.0 },
        tts_first_byte: { n: 20, rata: 780.4, p95: 1200.0, akhir: 690.0 },
        tts_total: { n: 20, rata: 2100.0, p95: 2900.0, akhir: 1980.0 },
        stt: { n: 8, rata: 900.0, p95: 1400.0, akhir: 880.0 },
        sing: { n: 0, rata: null, p95: null, akhir: null },
      });
    if (path === "/api/tts") { TTS_CHARS.n += 100; return ok({}); }
    if (path === "/api/stt") return ok({ text: "tes suara demo" });
    return ok({});
  };

  document.addEventListener("DOMContentLoaded", () => {
    const bar = document.createElement("div");
    bar.textContent = "DEMO — data tiruan, tanpa server. Versi asli jalan di HP.";
    bar.style.cssText = "position:fixed;left:0;right:0;bottom:0;z-index:99;padding:6px 10px;font:11px/1.4 Inter,system-ui;text-align:center;background:#1d2433;color:#f7f1e3";
    document.body.appendChild(bar);
    document.body.style.paddingBottom = "26px";
  });
})();
