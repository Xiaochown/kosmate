"""Tulis .env dari nilai KOSMATE_* di environment. Aman untuk key yang berisi / & = dll."""
import os
import pathlib
import stat

MAP = {
    "KOSMATE_BASE_URL": "LLM_BASE_URL",
    "KOSMATE_LLM_KEY": "LLM_API_KEY",
    "KOSMATE_MODEL": "LLM_MODEL",
    "KOSMATE_FALLBACK": "LLM_MODEL_FALLBACK",
    "KOSMATE_FISH_KEY": "FISH_API_KEY",
    "KOSMATE_FISH_MODEL": "FISH_MODEL",
    "KOSMATE_VOICE": "TTS_VOICE",
    "KOSMATE_TTS": "TTS_PROVIDER",
    "KOSMATE_NAME": "ASSISTANT_NAME",
    "KOSMATE_USER": "USER_NAME",
    "KOSMATE_PORT": "PORT",
}

updates = {}
for env_key, env_val in MAP.items():
    val = os.environ.get(env_key, "").strip()
    if val:
        updates[env_val] = val

src = pathlib.Path(".env.example")
dst = pathlib.Path(".env")

lines = []
if src.exists():
    for line in src.read_text(encoding="utf-8").splitlines():
        key = line.split("=", 1)[0].strip() if "=" in line and not line.strip().startswith("#") else None
        if key and key in updates:
            lines.append(f"{key}={updates[key]}")
            updates.pop(key)
        else:
            lines.append(line)
else:
    lines = ["# dibuat otomatis oleh Kosmate"]
for key, val in updates.items():
    lines.append(f"{key}={val}")

dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
dst.chmod(stat.S_IRUSR | stat.S_IWUSR)

print("   .env ditulis:")
for k in ("LLM_BASE_URL", "LLM_MODEL", "LLM_MODEL_FALLBACK", "TTS_PROVIDER", "TTS_VOICE"):
    v = os.environ.get({v2: k2 for k2, v2 in MAP.items()}.get(k, ""), "")
    if v:
        print(f"     {k} = {v}")
for k in ("LLM_API_KEY", "FISH_API_KEY"):
    ek = {v2: k2 for k2, v2 in MAP.items()}.get(k, "")
    v = os.environ.get(ek, "")
    print(f"     {k} = {'terisi (' + str(len(v)) + ' karakter)' if v else 'kosong'}")
