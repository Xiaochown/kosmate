/* Service worker: bikin app installable + shell tetap kebuka saat offline.
   Catatan: request /api/* TIDAK pernah di-cache (biar data selalu segar).

   CACHE dinaikkan versinya tiap kali aset berubah, supaya HP tidak menyajikan
   CSS/gambar lama setelah update (penyebab "temanya gak berubah").
*/
const CACHE = "kai-shell-v2";
const SHELL = [
  "./",
  "./index.html",
  "./style.css",
  "./app.js",
  "./extras.js",
  "./manifest.json",
  "./assets/icon-192.png",
  "./assets/icon-512.png",
  "./assets/mascot.webp",
  "./assets/mascot-listen.webp",
  "./assets/mascot-think.webp",
  "./assets/mascot-speak.webp",
  "./assets/banner.webp",
  "./assets/tex-paper.webp",
  "./assets/tex-wood-dark.webp",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches
      .open(CACHE)
      .then((c) => c.addAll(SHELL))
      .catch(() => {})
      .then(() => self.skipWaiting())
  );
});

/* Halaman bisa minta "buang semua cache" setelah update kode */
self.addEventListener("message", (e) => {
  if (e.data === "bersihkan-cache") {
    e.waitUntil(caches.keys().then((ks) => Promise.all(ks.map((k) => caches.delete(k)))));
  }
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.includes("/api/")) return; // data selalu dari jaringan

  /* Jaringan dulu untuk HTML/CSS/JS supaya update langsung kelihatan,
     cache hanya jadi cadangan saat offline. */
  const segarDulu = /\.(html|json)$|\/(index\.html)?$/.test(url.pathname) ||
    /\.(css|js)$/.test(url.pathname);

  if (segarDulu) {
    e.respondWith(
      fetch(req)
        .then((res) => {
          if (res && res.ok && res.type === "basic") {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
          }
          return res;
        })
        .catch(() => caches.match(req).then((hit) => hit || caches.match("./index.html")))
    );
    return;
  }

  /* gambar/ikon: cache dulu, biar cepat & hemat kuota */
  e.respondWith(
    caches.match(req).then(
      (hit) =>
        hit ||
        fetch(req)
          .then((res) => {
            if (res && res.ok && res.type === "basic") {
              const copy = res.clone();
              caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
            }
            return res;
          })
          .catch(() => caches.match("./index.html"))
    )
  );
});
