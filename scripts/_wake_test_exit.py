import pathlib

p = pathlib.Path("/root/kosmate/scripts/ui_v10_wake_test.cjs")
s = p.read_text()
if "process.exit(0)" not in s:
    s = s.replace(
        "  console.log(JSON.stringify(out, null, 2));",
        "  console.log(JSON.stringify(out, null, 2));\n  try { window.close(); } catch (e) {}\n  process.exit(0);",
    )
    p.write_text(s)
print("process.exit(0) ada:", "process.exit(0)" in s)
