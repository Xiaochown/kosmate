import pathlib

p = pathlib.Path("/root/kosmate/web/app.js")
src = p.read_text().splitlines(keepends=True)

start = next(i for i, l in enumerate(src) if l.startswith("async function speakOne("))
depth = 0
end = start
for i in range(start, len(src)):
    depth += src[i].count("{") - src[i].count("}")
    if depth == 0 and i > start:
        end = i
        break
print("hapus baris", start + 1, "..", end + 1)
cut_end = end + 2 if end + 1 < len(src) and src[end + 1].strip() == "" else end + 1
del src[start:cut_end]
t = "".join(src)
t = t.replace("speechQueue > 0", "adaUcapan()")
t = t.replace("speechQueue = 0;\n  speakChain = Promise.resolve();", "speechJobs = [];")
p.write_text(t)
print("sisa speechQueue:", t.count("speechQueue"), "| speakChain:", t.count("speakChain"), "| speakOne:", t.count("speakOne"))
