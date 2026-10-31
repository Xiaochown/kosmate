import pathlib

p = pathlib.Path("/root/kosmate/web/app.js")
t = p.read_text()
t = t.replace('    $("brandName").textContent = h.name || "Kosmate";\n', "")
t = t.replace('const engine = h.voice ? h.voice.label : (h.fish_key ? "Fish" : "edge · Gadis");\n    $("brandSub").textContent = engine;',
              'const engine = h.voice ? h.voice.label : (h.fish_key ? "Fish" : "edge");\n    if ($("brandSub")) $("brandSub").textContent = engine;')
p.write_text(t)
print("brandName refs:", t.count("brandName"), "| brandSub guard:", 'if ($("brandSub"))' in t)
