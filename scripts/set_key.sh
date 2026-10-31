#!/usr/bin/env bash
# Kosmate :: isi FISH_API_KEY dengan aman (input tidak kelihatan, tidak masuk history)
# pakai: bash scripts/set_key.sh
set -u
cd "$(dirname "$0")/.." || exit 1
[ -f .env ] || cp .env.example .env

echo "Tempel Fish Audio API key, lalu Enter (input gak kelihatan):"
printf '  key: '
read -rs K || true
echo

K="$(printf '%s' "${K:-}" | tr -d '[:space:]')"
if [ -z "$K" ]; then
  echo "  [!!] kosong — dibatalkan"
  exit 1
fi
if [ "${#K}" -lt 12 ]; then
  echo "  [!!] kepanjangan kurang (${#K} karakter) — kayaknya kepotong, ulangi"
  exit 1
fi

python - "$K" <<'PY'
import pathlib, sys
key = sys.argv[1]
p = pathlib.Path(".env")
lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
out, done = [], False
for line in lines:
    s = line.strip()
    if s.startswith("FISH_API_KEY="):
        out.append(f"FISH_API_KEY={key}")
        done = True
    elif s.startswith("FISH_API_KEY") and "=" not in s:
        continue
    else:
        out.append(line)
if not done:
    out.append(f"FISH_API_KEY={key}")
# buang duplikat kalau ada
seen, final = set(), []
for line in out:
    k = line.split("=", 1)[0].strip()
    if k and k in seen and line.startswith(k + "="):
        continue
    if line.startswith(k + "="):
        seen.add(k)
    final.append(line)
p.write_text("\n".join(final) + "\n", encoding="utf-8")
print(f"  [ok] FISH_API_KEY tersimpan ({len(key)} karakter)")
PY

echo
echo "cek cepat:"
grep -c '^FISH_API_KEY=..' .env | sed 's/^/  baris FISH_API_KEY valid: /'
echo
echo "lanjut: bash scripts/restart.sh"
