"""Cari voice perempuan Indonesia di Fish Audio (endpoint publik, tanpa API key)."""
import json
import math
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("/root/kosmate/data/samples/fish")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://api.fish.audio/model"


def fetch(params: dict) -> dict:
    url = BASE + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"User-Agent": "kosmate"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def main() -> None:
    items: dict[str, dict] = {}
    for sort in ("task_count", "like_count"):
        for page in (1, 2, 3):
            try:
                d = fetch({"language": "id", "page_size": 100, "page_number": page, "sort_by": sort})
            except Exception as e:  # noqa: BLE001
                print("gagal", sort, page, e)
                continue
            for it in d.get("items", []):
                items[it["_id"]] = it

    print(f"total model Indonesia terkumpul: {len(items)}")

    females = []
    for it in items.values():
        tags = [t.lower() for t in it.get("tags", [])]
        if "female" not in tags:
            continue
        likes = it.get("like_count", 0) or 0
        tasks = it.get("task_count", 0) or 0
        score = likes * 3 + math.log10(tasks + 1) * 12
        samples = it.get("samples") or []
        audio = samples[0]["audio"] if samples else None
        if not audio:
            continue
        females.append(
            {
                "id": it["_id"],
                "title": it.get("title", "?"),
                "tags": ",".join(tags[:7]),
                "likes": likes,
                "tasks": tasks,
                "score": round(score, 1),
                "audio": audio,
                "sample_text": (samples[0].get("text") or "")[:70],
            }
        )

    females.sort(key=lambda x: -x["score"])
    print(f"perempuan: {len(females)}\n")
    top = females[:12]
    for i, f in enumerate(top, 1):
        print(f"{i:2d}. {f['title'][:40]:40s} likes={f['likes']:4d} tasks={f['tasks']:6d} score={f['score']:6.1f}")
        print(f"    id={f['id']}")
        print(f"    tags={f['tags']}")
        print(f"    contoh: {f['sample_text']}")

    # unduh preview 6 teratas
    print("\nunduh preview:")
    for i, f in enumerate(top[:6], 1):
        mp3 = OUT / f"{i:02d}_{f['id'][:8]}.mp3"
        try:
            req = urllib.request.Request(f["audio"], headers={"User-Agent": "kosmate"})
            with urllib.request.urlopen(req, timeout=60) as r:
                mp3.write_bytes(r.read())
            ogg = mp3.with_suffix(".ogg")
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-c:a", "libopus",
                 "-b:a", "48k", "-ar", "48000", "-ac", "1", str(ogg)],
                env={"LD_LIBRARY_PATH": "/usr/lib/aarch64-linux-gnu/blas:/usr/lib/aarch64-linux-gnu/lapack",
                     "PATH": "/usr/bin:/bin"},
                check=False,
            )
            print(f"  {i}. {f['title'][:34]:34s} -> {mp3.name} {mp3.stat().st_size} byte  ogg={ogg.exists()}")
        except Exception as e:  # noqa: BLE001
            print(f"  {i}. gagal: {e}")

    (OUT.parent / "fish_candidates.json").write_text(json.dumps(top, indent=2, ensure_ascii=False))
    print("\ndisimpan:", OUT.parent / "fish_candidates.json")


if __name__ == "__main__":
    main()
