import pathlib

p = pathlib.Path("/root/kosmate/scripts/ui_v11_lang_test.cjs")
s = p.read_text()
s = s.replace(
    '  const semua = ["app.js", "extras.js", "wake.js", "i18n.js"].map((f) => fs.readFileSync(`${WEB}/${f}`, "utf8")).join("\\n;\\n");',
    '  const semua = ["app.js", "extras.js", "wake.js", "i18n.js"].map((f) => fs.readFileSync(`${WEB}/${f}`, "utf8")).join("\\n;\\n")\n    + "\\n;window.EX = EX; window.bolehHapus = bolehHapus;";  // jsdom: eval terpisah tidak lihat const',
)
s = s.replace('window.eval("EX.setLang(\'id\')")', 'window.EX.setLang("id")')
s = s.replace('window.eval("EX.setLang(\'en\')")', 'window.EX.setLang("en")')
s = s.replace('window.eval("EX.setZoom(1.2)")', 'window.EX.setZoom(1.2)')
p.write_text(s)
print("patched:", "window.EX.setLang" in s)
