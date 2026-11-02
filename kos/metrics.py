"""Metrik latency per komponen + briefing pagi (Sprint C)."""
from __future__ import annotations

import statistics
import time
from collections import deque

# 30 sampel terakhir per komponen (cukup buat lihat pola, tidak makan memori)
_sampel: dict[str, deque] = {
    "llm_first_token": deque(maxlen=30),
    "llm_total": deque(maxlen=30),
    "tts_first_byte": deque(maxlen=30),
    "tts_total": deque(maxlen=30),
    "stt": deque(maxlen=30),
    "sing": deque(maxlen=30),
}


def catat(komponen: str, ms: float) -> None:
    if komponen in _sampel and ms >= 0:
        _sampel[komponen].append(float(ms))


class ukur:
    """Context manager: catat durasi ke komponen tertentu."""

    def __init__(self, komponen: str):
        self.komponen = komponen
        self.mulai = 0.0

    def __enter__(self):
        self.mulai = time.perf_counter()
        return self

    def __exit__(self, *exc):
        catat(self.komponen, (time.perf_counter() - self.mulai) * 1000)
        return False


def _ringkas(nilai: deque) -> dict:
    if not nilai:
        return {"n": 0, "rata": None, "p95": None, "akhir": None}
    data = list(nilai)
    return {
        "n": len(data),
        "rata": round(statistics.fmean(data), 1),
        "p95": round(sorted(data)[max(0, int(len(data) * 0.95) - 1)], 1),
        "akhir": round(data[-1], 1),
    }


def laporan() -> dict:
    return {k: _ringkas(v) for k, v in _sampel.items()}
