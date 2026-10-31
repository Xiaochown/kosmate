import pathlib

# ---------- 1) settings: tone / humor / nickname ----------
s = pathlib.Path("/root/kosmate/kos/settings.py")
t = s.read_text()
if "TEKS" not in t:
    t = t.replace(
        'PRESETS: dict[str, dict[str, Any]] = {',
        '''TEKS: dict[str, dict[str, Any]] = {
    "tone":     {"default": "santai", "pilihan": ["santai", "lembut", "tegas"],
                 "label": "Tone", "hint": "santai = kayak teman, lembut = lebih kalem & penyabar, tegas = to the point."},
    "humor":    {"default": "1", "pilihan": ["0", "1", "2"],
                 "label": "Humor (0-2)", "hint": "0 serius, 1 secukupnya, 2 banyak nyeletuk."},
    "nickname": {"default": "", "pilihan": [],
                 "label": "Nickname", "hint": "Dia manggil lu apa. Kosongkan = pakai nama default."},
}

PRESETS: dict[str, dict[str, Any]] = {''')
    t = t.replace(
        '''def load() -> dict[str, Any]:
    data: dict[str, Any] = {k: v["default"] for k, v in SPEK.items()}''',
        '''def _bersih_teks(kunci: str, val: Any) -> str:
    s = TEKS[kunci]
    v = str(val or "").strip()[:40]
    if s["pilihan"]:
        return v if v in s["pilihan"] else s["default"]
    return v


def load() -> dict[str, Any]:
    data: dict[str, Any] = {k: v["default"] for k, v in SPEK.items()}
    data.update({k: v["default"] for k, v in TEKS.items()})''')
    t = t.replace(
        '''            for k in SPEK:
                if k in saved:
                    data[k] = _clamp(k, saved[k])''',
        '''            for k in SPEK:
                if k in saved:
                    data[k] = _clamp(k, saved[k])
            for k in TEKS:
                if k in saved:
                    data[k] = _bersih_teks(k, saved[k])''')
    t = t.replace(
        '''    for k, v in (baru or {}).items():
        if k in SPEK:
            data[k] = _clamp(k, v)''',
        '''    for k, v in (baru or {}).items():
        if k in SPEK:
            data[k] = _clamp(k, v)
        elif k in TEKS:
            data[k] = _bersih_teks(k, v)''')
    t = t.replace(
        '    base = {k: v["default"] for k, v in SPEK.items()}\n    base.update(PRESETS[nama])',
        '    base = {k: v["default"] for k, v in SPEK.items()}\n    base.update({k: v["default"] for k, v in TEKS.items()})\n    base.update(PRESETS[nama])')
    t = t.replace(
        '    return {"spec": SPEK, "presets": list(PRESETS), "values": load()}',
        '    return {"spec": SPEK, "teks": TEKS, "presets": list(PRESETS), "values": load()}')
    s.write_text(t)
    print("settings: TEKS ditambahkan")

# ---------- 2) persona: pakai tone/humor/nickname ----------
p = pathlib.Path("/root/kosmate/kos/persona.py")
t = p.read_text()
if "TONE" not in t:
    t = t.replace("from .config import CFG", "from .config import CFG\nfrom . import settings as setelan")
    t = t.replace(
        "    system += \"\\n\" + _MODE.get(CFG.persona_mode, _MODE[\"temen\"])",
        '''    system += "\\n" + _MODE.get(CFG.persona_mode, _MODE["temen"])

    # personality dari setelan runtime
    tone = setelan.get("tone")
    humor = str(setelan.get("humor"))
    nick = setelan.get("nickname")
    gaya = {
        "santai": "Gaya: santai, akrab, kayak teman sebaya.",
        "lembut": "Gaya: lembut, penyabar, kalimat tenang, jangan pernah nyindir.",
        "tegas": "Gaya: tegas dan to the point, kalimat pendek, langsung ke inti.",
    }.get(tone, "")
    if gaya:
        system += "\\n" + gaya
    system += "\\nHumor: " + {"0": "serius, tanpa becanda.", "1": "sesekali nyeletuk halus.",
                               "2": "sering becanda ringan, tapi tetap nyambung."}.get(humor, "secukupnya.")
    if nick:
        system += "\\nPanggil user dengan \\"" + nick + "\\"."''')
    p.write_text(t)
    print("persona: tone/humor/nickname dipakai:", "TONE" not in t)
