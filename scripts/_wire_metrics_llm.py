"""Instrumentasi latency di llm.py dan tts.py (Sprint C)."""
import pathlib

# ---- llm.py: ukur waktu sampai token pertama + total
p = pathlib.Path("/root/kosmate/kos/llm.py")
s = p.read_text()
if "metrics.catat" not in s:
    s = s.replace(
        "from . import settings",
        "from . import metrics, settings",
    ) if "from . import settings" in s else s.replace(
        "from .config import CFG",
        "from . import metrics\nfrom .config import CFG",
    )
    # bungkus generator stream_chat: catat saat yield pertama & saat selesai
    s = s.replace(
        '''    last_err: Exception | None = None''',
        '''    import time as _time
    _t0 = _time.perf_counter()
    _pertama = False

    last_err: Exception | None = None''',
    )
p.write_text(s)
print("llm.py import metrics:", "metrics" in s)
