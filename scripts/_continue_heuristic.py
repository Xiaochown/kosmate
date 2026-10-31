import pathlib

a = pathlib.Path("/root/kosmate/kos/app.py")
s = a.read_text()

# helper: deteksi jawaban yang berhenti di tengah kalimat
if "_kepotong" not in s:
    s = s.replace(
        "def _dedupe(prev: str, new: str) -> str:",
        '''AKHIR_SAH = ".!?…\\"'”’)]}"'


def _kepotong(t: str) -> bool:
    """True kalau teks berhenti tanpa tanda akhir kalimat (indikasi stream dipotong)."""
    t = (t or "").rstrip()
    if len(t) < 40:
        return False
    return t[-1] not in AKHIR_SAH


def _dedupe(prev: str, new: str) -> str:''')

# lanjut kalau kehabisan token ATAU kalimat belum selesai
s = s.replace(
    'while info.get("finish_reason") == "length" and lanjut < CFG.llm_continue_max:',
    'while lanjut < CFG.llm_continue_max and (\n'
    '                info.get("finish_reason") == "length" or _kepotong("".join(buf))\n'
    '            ):')
s = s.replace(
    'print(f"[chat] jawaban kena batas token, lanjut otomatis #{lanjut}")',
    'print(f"[chat] jawaban kepotong (finish={info.get(\'finish_reason\')}), lanjut otomatis #{lanjut}")')

a.write_text(s)
print("_kepotong:", "_kepotong" in s, "| loop:", "or _kepotong" in s)

# naikin jatah lanjut default: cerita panjang butuh lebih dari 2
c = pathlib.Path("/root/kosmate/kos/config.py")
t = c.read_text().replace('get("LLM_CONTINUE_MAX", "2")', 'get("LLM_CONTINUE_MAX", "4")')
c.write_text(t)
print("continue_max default 4:", 'LLM_CONTINUE_MAX", "4"' in t)
