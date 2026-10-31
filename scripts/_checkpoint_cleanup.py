"""Checkpoint housekeeping: berhenti track runtime state + sampel besar, rotasi PIN."""
import pathlib
import secrets
import subprocess

ROOT = pathlib.Path("/root/kosmate")


def sh(*args: str) -> str:
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0 and "did not match" not in r.stderr:
        print("  !", " ".join(args), "->", r.stderr.strip()[:160])
    return r.stdout.strip()


# 1) lepas file runtime & sampel dari index (tetap ada di disk)
tracked = sh("git", "ls-files", "data").splitlines()
buang = [f for f in tracked if f.startswith(("data/samples/", "data/pin.txt", "data/mode.txt",
                                             "data/voice.json", "data/settings.json"))]
print("file dilepas dari git:", len(buang))
if buang:
    sh("git", "rm", "--cached", "-q", *buang)

# 2) .gitignore: tambah state runtime
gi = ROOT / ".gitignore"
t = gi.read_text()
tambahan = [x for x in ("data/pin.txt", "data/mode.txt", "data/voice.json", "data/settings.json")
            if x not in t]
if tambahan:
    t = t.rstrip() + "\n\n# state runtime (jangan pernah masuk repo)\n" + "\n".join(tambahan) + "\n"
    gi.write_text(t)
print("ditambahkan ke .gitignore:", tambahan)

# 3) rotasi PIN (yang lama sempat ke-commit)
pin = ROOT / "data" / "pin.txt"
baru = "".join(secrets.choice("0123456789") for _ in range(6))
pin.parent.mkdir(parents=True, exist_ok=True)
pin.write_text(baru + "\n", encoding="utf-8")
print("PIN baru:", baru)
