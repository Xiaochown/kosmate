/* ============================================================
   Wake word "Hei Kai" — versi 2
   Masalah versi lama: instance recognition kedua bertabrakan dengan
   recognition utama (Chrome cuma boleh satu), tidak tersimpan setelah
   reload, dan tidak pernah lanjut sendiri setelah error.
   ============================================================ */
(function () {
  const KEY = "kosmate.wake";
  const POLA =
    /\b(?:hai|hei|hey|hi|halo|hallo|woi|oi|oke|ok|dengar)\s*,?\s*(?:kai|kay|khai|kaii|kayee)\b|\b(?:kai|kay|khai)\b/i;

  EX.wakePaused = false;
  EX.wakeGagal = 0;

  function simpan(on) {
    try { localStorage.setItem(KEY, on ? "1" : "0"); } catch (e) {}
  }
  function hapusRec() {
    if (EX.wakeRec) {
      try { EX.wakeRec.abort(); } catch (e) {}
      EX.wakeRec = null;
    }
  }
  function tandai(on) {
    const b = $x("setWake");
    if (b) {
      b.classList.toggle("on", !!on);
      b.innerHTML = '<span class="dot' + (on ? " ok" : "") + '"></span>' + (on ? "on" : "off");
    }
  }

  /* berhenti sementara: setting tetap ON, cuma mic-nya dilepas
     supaya recognition utama bisa dipakai */
  EX.stopWake = function (dariUser) {
    hapusRec();
    EX.wakePaused = true;
    if (dariUser) {
      EX.wake = false;
      simpan(false);
      tandai(false);
      setStatus("Wake word off");
      diag("stt", "wake word dimatikan");
    }
  };

  EX.mulaiWake = function (diam) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setStatus("Wake word butuh Chrome (browser ini tidak punya speech recognition)");
      diag("stt", "wake word: SpeechRecognition tidak ada");
      return;
    }
    if (S.autoListen) {
      // auto-listen sudah menyalakan mic terus; wake word jadi tidak perlu
      setStatus("Wake word tidak dipakai — matikan “Auto listen” dulu");
      diag("stt", "wake word dibatalkan: Auto listen aktif");
      return;
    }
    hapusRec();
    EX.wakePaused = false;
    const r = new SR();
    r.lang = "id-ID";
    r.continuous = true;
    r.interimResults = true;
    r.maxAlternatives = 1;

    r.onresult = (e) => {
      let teks = "";
      for (let i = e.resultIndex; i < e.results.length; i++) teks += " " + e.results[i][0].transcript;
      teks = teks.trim();
      if (!teks) return;
      if (POLA.test(teks)) {
        diag("stt", "wake word kena: " + teks.slice(0, 40));
        EX.wakeGagal = 0;
        hapusRec();          // lepas mic dulu
        EX.wakePaused = true;
        setStatus("Yes?");
        setTimeout(() => {
          if (!S.speaking && !S.listening) startListening(true);
        }, 260);
      }
    };

    r.onerror = (e) => {
      const err = (e && e.error) || "unknown";
      diag("stt", "wake word error: " + err);
      if (err === "not-allowed" || err === "service-not-allowed") {
        EX.stopWake(true);
        setStatus("Mic diblokir browser — izinkan lalu nyalakan lagi");
        return;
      }
      // no-speech / aborted / network -> coba lagi dengan jeda naik
      if (EX.wake && !EX.wakePaused) {
        EX.wakeGagal++;
        const jeda = Math.min(8000, 600 * EX.wakeGagal);
        setTimeout(() => { if (EX.wake && !EX.wakePaused) EX.mulaiWake(true); }, jeda);
      }
    };

    r.onend = () => {
      // Chrome menutup recognition sendiri setelah diam beberapa saat
      if (EX.wake && !EX.wakePaused && !S.listening && !S.speaking) {
        setTimeout(() => {
          if (EX.wake && !EX.wakePaused && !S.listening && !S.speaking) EX.mulaiWake(true);
        }, 500);
      }
    };

    EX.wakeRec = r;
    try {
      r.start();
      if (!diam) {
        setStatus('Wake word on — bilang "Hei Kai"');
        diag("stt", "wake word aktif");
      }
    } catch (e) {
      // InvalidStateError: masih ada recognition lain jalan -> coba lagi nanti
      EX.wakeRec = null;
      EX.wakeGagal++;
      setTimeout(() => { if (EX.wake && !EX.wakePaused) EX.mulaiWake(true); }, 900);
    }
  };

  EX.toggleWake = function () {
    if (EX.wake) {
      EX.stopWake(true);
      return;
    }
    EX.wake = true;
    EX.wakeGagal = 0;
    simpan(true);
    tandai(true);
    EX.mulaiWake(false);
  };

  /* ikut state utama: saat mic dipakai (listening/thinking/speaking) lepas,
     saat kembali idle nyalakan lagi */
  document.addEventListener("kos:state", (ev) => {
    const st = ev.detail;
    if (!EX.wake) return;
    if (st === "listening" || st === "thinking" || st === "speaking") {
      if (EX.wakeRec) { hapusRec(); EX.wakePaused = true; }
    } else if (st === "idle") {
      if (EX.wakePaused) setTimeout(() => { if (EX.wake && !EX.wakePaused) EX.mulaiWake(true); }, 800);
    }
  });

  /* pulihkan setting terakhir setelah reload */
  try {
    if (localStorage.getItem(KEY) === "1") {
      EX.wake = true;
      tandai(true);
      setTimeout(() => EX.mulaiWake(true), 1500);
    }
  } catch (e) {}
})();
