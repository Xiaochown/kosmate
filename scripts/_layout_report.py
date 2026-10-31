import pathlib

a = pathlib.Path("/root/kosmate/web/app.js")
s = a.read_text()

if "LAPORAN LAYOUT" not in s:
    s = s.replace(
        '    tulis("UA: " + navigator.userAgent.slice(0, 90));',
        '''    tulis("UA: " + navigator.userAgent.slice(0, 90));
    setTimeout(() => {
      const vw = innerWidth, vh = innerHeight;
      const R = (sel) => {
        const el = document.querySelector(sel);
        if (!el) return "-";
        const r = el.getBoundingClientRect();
        return Math.round(r.width) + "x" + Math.round(r.height);
      };
      tulis("LAPORAN LAYOUT · layar " + vw + "x" + vh);
      tulis("  dokumen  " + document.documentElement.scrollWidth + "x" + document.body.scrollHeight);
      tulis("  header   " + R(".topbar") + "  nav " + R(".topnav"));
      tulis("  banner   " + R(".banner img") + "  chips " + R(".mode-row"));
      tulis("  orb      " + R(".orb") + "  composer " + R(".composer"));
      const luber = [...document.querySelectorAll("body *")]
        .map((e) => ({ t: e.tagName.toLowerCase() + "." + String(e.className).split(" ")[0], r: e.getBoundingClientRect() }))
        .filter((o) => o.r.right > vw + 1 || o.r.width > vw + 1)
        .slice(0, 6)
        .map((o) => o.t + "(" + Math.round(o.r.width) + ")");
      tulis("  luber    " + (luber.length ? luber.join(", ") : "tidak ada"));
    }, 1200);''')
    a.write_text(s)
print("overlay laporan layout:", "LAPORAN LAYOUT" in s)
