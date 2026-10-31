import pathlib

# 1) setelan baru: target panjang cerita
p = pathlib.Path("/root/kosmate/kos/settings.py")
t = p.read_text()
if "story_words" not in t:
    t = t.replace(
        '    "memory_chars":',
        '    "story_words":         {"default": 1500,  "min": 300,   "max": 8000,  "step": 100, "label": "Story target (words)",\n'
        '                            "hint": "Di mode Story, cerita dilanjutkan otomatis sampai panjang ini. 130 kata ≈ 1 menit suara."},\n'
        '    "memory_chars":')
    t = t.replace(
        '        "llm_timeout": 240,\n        "tts_timeout": 240,',
        '        "llm_timeout": 240,\n        "tts_timeout": 240,\n        "story_words": 1800,')
    p.write_text(t)
    print("settings: story_words ditambahkan")

# 2) app.py: lanjut sampai target kata di mode cerita
a = pathlib.Path("/root/kosmate/kos/app.py")
s = a.read_text()
if "story_words" not in s:
    s = s.replace(
        '            # kena batas token? lanjut otomatis, jangan biarkan kepotong di tengah kalimat\n            lanjut = 0',
        '            # target panjang untuk mode cerita (pengantar tidur)\n'
        '            target = int(setelan.get("story_words")) if CFG.persona_mode == "cerita" else 0\n'
        '            batas_lanjut = max(CFG.llm_continue_max, 8) if target else CFG.llm_continue_max\n'
        '            lanjut = 0')
    s = s.replace(
        'while lanjut < CFG.llm_continue_max and (\n'
        '                info.get("finish_reason") == "length" or _kepotong("".join(buf))\n'
        '            ):',
        'while lanjut < batas_lanjut and (\n'
        '                info.get("finish_reason") == "length"\n'
        '                or _kepotong("".join(buf))\n'
        '                or (target and len("".join(buf).split()) < target)\n'
        '            ):')
    s = s.replace(
        '                cont = messages + [\n'
        '                    {"role": "assistant", "content": "".join(buf)},\n'
        '                    {"role": "user", "content": "Lanjutkan tepat dari kata terakhir. Jangan ulangi kalimat sebelumnya, jangan beri pembuka baru."},\n'
        '                ]',
        '                sisa = max(0, target - len("".join(buf).split())) if target else 0\n'
        '                arahan = (\n'
        '                    f"Lanjutkan cerita tepat dari kalimat terakhir. Jangan ulangi, jangan beri pembuka. "\n'
        '                    f"Tulis minimal {sisa} kata lagi dengan suasana tenang, lalu tutup cerita dengan penutup yang menenangkan."\n'
        '                    if sisa > 100 else\n'
        '                    "Lanjutkan tepat dari kata terakhir. Jangan ulangi kalimat sebelumnya, jangan beri pembuka baru."\n'
        '                )\n'
        '                cont = messages + [\n'
        '                    {"role": "assistant", "content": "".join(buf)},\n'
        '                    {"role": "user", "content": arahan},\n'
        '                ]')
    s = s.replace(
        'print(f"[chat] jawaban kepotong (finish={info.get(\'finish_reason\')}), lanjut otomatis #{lanjut}")',
        'print(f"[chat] lanjut #{lanjut}: finish={info.get(\'finish_reason\')} kata={len(\'\'.join(buf).split())} target={target}")')
    a.write_text(s)
    print("app: target cerita aktif:", "story_words" in s)
