# PWA shell for a cozy indie-game web app (Android Chrome)

Copy-paste, then change names/colours. Verified installable: manifest + icons +
service worker **with a fetch handler**. Icons alone are not enough.

## web/manifest.json

```json
{
  "name": "Kai — cozy companion",
  "short_name": "Kai",
  "id": "/",
  "start_url": "./?src=pwa",
  "scope": "./",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#f3e9d5",
  "theme_color": "#8a6039",
  "icons": [
    { "src": "assets/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "assets/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

**Relative paths matter.** On GitHub Pages a project lives at
`/repo-name/`, so `start_url:"/"` and `src:"/assets/x.png"` both 404 — and Chrome
then says *"This app cannot be installed"*. Use `./` and `assets/...`.

## web/sw.js

```js
const CACHE = "app-shell-v3";           // bump on EVERY asset change
const SHELL = [
  "./", "./index.html", "./style.css",
  "./app.js", "./extras.js", "./manifest.json",
  "./assets/mascot.webp", "./assets/banner.webp",
  "./assets/icon-192.png", "./assets/icon-512.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.startsWith("/api/")) return;            // never cache data

  const shell = /\.(?:html|css|js|json)$/i.test(url.pathname) || url.pathname.endsWith("/");
  if (shell) {
    // NETWORK-FIRST: otherwise users keep seeing the previous deploy's theme
    e.respondWith(
      fetch(e.request)
        .then((r) => {
          const copy = r.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
          return r;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }
  // images/audio: cache-first
  e.respondWith(caches.match(e.request).then((hit) => hit || fetch(e.request)));
});
```

## index.html head

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#8a6039">
<link rel="manifest" href="manifest.json">
<link rel="icon" href="assets/icon-192.png">
<link rel="apple-touch-icon" href="assets/icon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400;600;700&family=Nunito:wght@400;600;700&display=swap" rel="stylesheet">
```

Register at the end of `app.js`:

```js
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}
```

## Audio / TTS in a PWA

Autoplay is blocked until a user gesture. Create/resume the AudioContext (or call
`audio.play()`) **inside** a click/tap handler once, then reuse it. Otherwise the
app is mute after reload and users blame the TTS.

## Cache-busting on top of the SW

Also append `?v=2` to `style.css` / `app.js` links. Two independent layers: the SW
handles offline + updates, the query string handles browsers without a SW yet.

## Version badge (so you can tell what's deployed)

Write a `VERSION` file at repo root and render it in a debug panel reached by
`?debug=1`. When a user says "it's still the old design", the badge answers it
without a round-trip.
