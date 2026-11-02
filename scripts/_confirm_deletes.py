"""Pasang konfirmasi di semua tombol hapus (pengingat, catatan, fakta)."""
import pathlib

e = pathlib.Path("/root/kosmate/web/extras.js")
t = e.read_text()

# pengingat
t = t.replace(
    '        await api("/api/reminders/" + b.dataset.rid, { method: "DELETE" });',
    '''        if (!bolehHapus("pengingat ini")) return;
        await api("/api/reminders/" + b.dataset.rid, { method: "DELETE" });''',
)
# catatan
t = t.replace(
    '        await api("/api/notes/" + b.dataset.did, { method: "DELETE" });',
    '''        if (!bolehHapus("catatan ini")) return;
        await api("/api/notes/" + b.dataset.did, { method: "DELETE" });''',
)
e.write_text(t)

a = pathlib.Path("/root/kosmate/web/app.js")
s = a.read_text()
if "kofirmasiHapusFakta" not in s:
    s = s.replace(
        '        await fetch("/api/memory/facts/" + f.id, { method: "DELETE" });',
        '''        const tanya = window.bolehHapus || ((x) => confirm("Hapus " + x + "?"));
        if (!tanya("fakta ini")) return;
        await fetch("/api/memory/facts/" + f.id, { method: "DELETE" });''',
    )
a.write_text(s)

print("pengingat:", "bolehHapus(\"pengingat ini\")" in t)
print("catatan  :", "bolehHapus(\"catatan ini\")" in t)
print("fakta    :", "tanya(\"fakta ini\")" in s)
