import pathlib

p = pathlib.Path("/root/kosmate/scripts/ui_v10_wake_test.cjs")
s = p.read_text()

s = s.replace(
    'out.listening = window.eval("S.listening");',
    'out.listening = doc.body.dataset.state === "listening";',
)
s = s.replace(
    '''window.eval('document.dispatchEvent(new CustomEvent("kos:state", { detail: "idle" }))');''',
    '''doc.dispatchEvent(new window.CustomEvent("kos:state", { detail: "idle" }));''',
)
p.write_text(s)
print("patched:", "S.listening" not in s)
