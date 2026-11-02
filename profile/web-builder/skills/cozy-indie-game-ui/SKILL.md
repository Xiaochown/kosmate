---
name: cozy-indie-game-ui
description: Use when building cozy indie-game style web UI or PWA.
---

# Cozy Indie-Game UI (Stardew-like)

Design system + asset pipeline for warm, chunky, "handcrafted game" interfaces.
Proven on a real shipped PWA (voice assistant, 640-line CSS, mobile-first 360–414px).

## When to use

- Product should feel like a **cozy indie game**: farm sim, life sim, companion app, kids app, journal, bedtime/story app.
- User asks for "Stardew Valley vibe", "game-like", "not a SaaS template", "hangat/kayu/krem".
- Any UI needing mascots, parchment panels, wooden headers, pressable chunky buttons.

**Do NOT use** for: SaaS dashboards, developer tools, fintech, anything that must read as
serious/corporate. Those get the monochrome Linear treatment instead (see `popular-web-designs`).
If the user gave a reference URL, extract that site's real palette/fonts/motifs instead of freehanding.

## Design intent (non-negotiables)

1. **Warm over clean.** Oat linen paper, walnut wood, harvest gold, sage. Never pure white panels, never `#000` text.
2. **Chunky over airy.** 3px borders, hard shadows (no blur), radius 8–16px. Buttons physically press down 2px.
3. **Layered panels.** Every panel = wood/dark outline + cream face + inner 1px highlight. Flat cards read as "template".
4. **One mascot, several poses** tied to app state (idle/listening/thinking/speaking). Same character, same scale, same background across poses.
5. **Texture, not noise.** Paper grain must be ≤5 luminance levels of variation. Visible stains/splotches = broken.

## Tokens

```css
:root {
  /* paper — warm oat linen, NOT buttery yellow */
  --parch:#f3e9d5; --parch-2:#ebdfc5; --parch-3:#dfcfa9;
  --card:#fbf4e4;  --card-edge:#efe3c8;
  /* ink — dark umber, never #000 */
  --ink:#40301f;   --ink-2:#6b5136;  --ink-3:#8c7351;
  /* wood — walnut */
  --wood:#8a6039;  --wood-d:#5c3f24; --wood-l:#ab8253; --wood-hi:#cba36c;
  /* accents — muted, not neon */
  --amber:#cf9a4a; --amber-d:#a2742c;
  --leaf:#7d9159;  --leaf-d:#566839;
  --moon:#2d3c57;  --red:#b25c42;

  --r-sm:8px; --r-md:12px; --r-lg:16px; --r-pill:999px;
  --shadow-sm:0 2px 0 var(--wood-l);
  --shadow-md:0 4px 0 var(--wood-l);
  --shadow-btn:0 3px 0 var(--amber-d);

  --font-head:"Pixelify Sans","Trebuchet MS",system-ui,sans-serif;
  --font-body:"Nunito",-apple-system,"Segoe UI",Roboto,sans-serif;
  --wood-line:2px solid var(--wood-d);
  --wood-line-thick:3px solid var(--wood-d);
}
```

Full token file with panel/button/mascot recipes: `references/tokens.css`.

## Layout rules (mobile PWA)

| Part | Rule |
|---|---|
| Header | one row, ≤56px tall. `grid-template-columns:minmax(0,1fr) auto`. Icon-only nav under 440px |
| Banner art | `object-fit:cover`, max-height 110–120px |
| Hero/mascot orb | `clamp(112px,34vw,140px)` |
| Chips row | `flex-wrap:nowrap` + `overflow-x:auto`, never wrap to 2 lines |
| Cards | image on TOP (`aspect-ratio:16/10`), text below. Never image-beside-text with `height:auto` |
| Content column | `html,body{max-width:100%;overflow-x:hidden}`; verify `scrollWidth == viewport` |
| Touch | min 44px targets, body text ≥15px |
| Sheets/modals | sticky header inside sheet, `max-height:42dvh` scroll for replies |

## Asset pipeline (this is where "patchwork" comes from)

Generate art, then **always** normalize before shipping:

1. **Fixed aspect per slot** — cards 640×400 (16:10), banner 1000×280, mascot 520×520.
   Center-crop, never stretch.
2. **Match panel background** — sample the generated image's corner colour, rescale channels so it equals your `--card`. Otherwise every image looks pasted-on.
3. **Equalize luminance** — target mean 150–180 for card art. Grey out-of-range images toward it (gamma), 8–10% warm blend, saturation 0.92.
4. **Equal character scale** — crop by fixed *fraction* of frame (e.g. 86% width), not by object bounding box. bbox cropping makes poses without props look zoomed-in.
5. **Textures**: prefer procedural (PIL noise ≤5 levels) over AI "paper texture" — AI grain has blotches that become ugly speckles at UI scale.
6. Export **WebP** (quality 85–88), MP3 audio, PNG only for PWA icons.

Script that does 1–6 in one run: `references/asset_pipeline.py`.

## Verification without a browser (headless/container)

Chromium often cannot run in proot/containers (dbus/netlink hang, `page.goto` never returns).
Do not conclude "looks fine" from code. Instead:

1. **jsdom** with `runScripts:'dangerously'` + stubbed `fetch`/`SpeechRecognition`/`Audio` → assert 0 `jsErrors`, expected element counts.
2. **Geometry** via WeasyPrint at 390×844 → catch header wrapping (real bug: 74pt header from nav wrapping).
3. **Debug overlay** `?debug=1` printing `header/banner/orb/composer` sizes + horizontal overflow detection, read by the user on device.
4. **Vision** on generated assets (aspect, background, scale consistency) — but not on the whole layout if the renderer lacks flex/grid.
5. If a vision model is available: screenshot → critique → fix → screenshot. Expect real findings (noisy paper, stark contrast, inconsistent poses).

## PWA checklist (Android Chrome)

- `manifest.json`: relative `start_url`/icon paths (`./?src=pwa`, `assets/...`) — absolute 404s on GH Pages subpaths.
- **Service worker required** for installability: needs a `fetch` handler. `/api/*` never cached.
- HTML/CSS/JS = **network-first** (cache-first hides new deploys — users see the old theme after update).
- Icons: 192 + 512 `any` + 512 `maskable` (safe zone 78%, solid background).
- `theme-color` = your wood tone; `background-color` = paper tone.
- Bump `CACHE` version name on every asset change.
- TTS/audio: unlock on first user gesture (`audio.play()` inside click), else autoplay-blocked silence.

## Pitfalls (all hit for real)

- **Pure-white image backgrounds** on cream panels → looks like stickers. Recolor.
- **Stretch instead of crop** → squashed art. Always cover/crop.
- **`height:auto` on a side image** → card height follows text, images misaligned.
- **AI paper texture** → dirty blotches. Use procedural grain.
- **bbox crop per pose** → character size jumps between states. Use fixed-fraction crop.
- **Flex/grid-heavy CSS assessed via WeasyPrint** → false layout reports. Cross-check with jsdom numbers or on-device debug overlay.
- **Cache-first SW** → user sees stale UI and thinks the update failed.
- **`pkg install ffmpeg`** (50MB) blocks Termux installs — make audio processing optional and fail with a clear message.

## Delivery

Ship a single-file variant for preview (`inline CSS/JS/images as base64`) so a link can never show "just an icon", plus the real multi-file app for production. Demo data must be clearly labelled and never shipped to production builds.
