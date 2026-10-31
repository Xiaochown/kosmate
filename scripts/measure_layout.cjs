// Ukur layout nyata di Chromium headless (file://): rect tiap elemen penting.
const { chromium } = require("/tmp/uitest/node_modules/playwright") || {};
const path = "/root/kosmate/web/index.html";

(async () => {
  const { chromium: pw } = require("/tmp/uitest/node_modules/playwright");
  const browser = await pw.chromium.launch({
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--single-process"],
  });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 120)));
  await page.goto("file://" + path, { timeout: 12000, waitUntil: "domcontentloaded" });
  await page.waitForTimeout(800);

  const out = await page.evaluate(() => {
    const rect = (sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) };
    };
    const w = window.innerWidth;
    const over = [...document.querySelectorAll("body *")]
      .map((el) => ({ t: el.tagName.toLowerCase() + "." + (el.className || "").toString().split(" ")[0], r: el.getBoundingClientRect() }))
      .filter((o) => o.r.width > w + 1 || o.r.right > w + 1)
      .slice(0, 6)
      .map((o) => `${o.t} w=${Math.round(o.r.width)} right=${Math.round(o.r.right)}`);

    return {
      viewport: { w, h: window.innerHeight },
      scrollWidth: document.documentElement.scrollWidth,
      header: rect(".topbar"),
      nav: rect(".topnav"),
      banner: rect(".banner img"),
      modeRow: rect(".mode-row"),
      orb: rect(".orb"),
      mascot: rect(".orb .mascot"),
      status: rect("#status"),
      voicechip: rect("#voicechip, .voicechip"),
      composer: rect(".composer"),
      docHeight: document.body.scrollHeight,
      overflow: over,
    };
  });
  console.log(JSON.stringify({ ...out, errors }, null, 2));
  await browser.close();
})().catch((e) => {
  console.log("GAGAL PLAYWRIGHT:", String(e).slice(0, 200));
  process.exit(1);
});
