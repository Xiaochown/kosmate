#!/usr/bin/env bash
# Ambil proyek Kosmate + pasang profile 'web-builder' di device ini.
# Satu perintah, tidak menyentuh profile lain, tidak menimpa data yang sudah ada.
set -u

REPO="https://github.com/Xiaochown/kosmate"
ZIP="https://codeload.github.com/Xiaochown/kosmate/zip/refs/heads/main"
RAW="https://raw.githubusercontent.com/Xiaochown/kosmate/main/profile/web-builder"
DIR="${KOSMATE_DIR:-$HOME/kosmate}"
H="${HERMES_HOME:-$HOME/.hermes}"
SK="$H/profiles/web-builder/skills"

echo "== 1/4 ambil kode ke $DIR"
if [ -d "$DIR/.git" ]; then
  ( cd "$DIR" && git pull --ff-only -q 2>/dev/null ) && echo "  [ok] git pull" || echo "  [ok] pakai versi lokal"
elif command -v git >/dev/null 2>&1; then
  if git clone --depth 1 -q "$REPO" "$DIR" 2>/dev/null; then
    echo "  [ok] git clone"
  else
    echo "  [!!] clone gagal, coba ZIP…"
    command -v git >/dev/null && rm -rf "$DIR"
  fi
fi

if [ ! -f "$DIR/AGENTS.md" ]; then
  python3 - "$DIR" "$ZIP" <<'PY'
import io, sys, zipfile, urllib.request
from pathlib import Path

tujuan, url = Path(sys.argv[1]), sys.argv[2]
tujuan.parent.mkdir(parents=True, exist_ok=True)
with urllib.request.urlopen(url, timeout=120) as r:
    data = r.read()
z = zipfile.ZipFile(io.BytesIO(data))
akar = z.namelist()[0].split("/")[0]
tujuan.mkdir(parents=True, exist_ok=True)
for n in z.namelist():
    if not n.startswith(akar + "/") or n.endswith("/"):
        continue
    rel = n[len(akar) + 1:]
    if rel.startswith("data/") or rel in (".env",):
        continue                      # jangan bawa data/rahasia
    out = tujuan / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(z.read(n))
print("  [ok] ZIP diekstrak:", len(z.namelist()), "entri")
PY
fi

echo "== 2/4 dependency python"
cd "$DIR" || { echo "  [!!] folder tidak bisa dibuka"; exit 1; }

cari_uv() {
  for k in "$(command -v uv 2>/dev/null)" "$HOME/.local/bin/uv" "$HOME/.hermes/bin/uv" \
           "$HOME/.cargo/bin/uv" /root/.hermes/bin/uv; do
    [ -n "$k" ] && [ -x "$k" ] && { printf '%s' "$k"; return 0; }
  done
  return 1
}

PYBIN=""
if [ -x .venv/bin/python ] && .venv/bin/python -c "import starlette" 2>/dev/null; then
  PYBIN="$DIR/.venv/bin/python"; echo "  [ok] venv lama dipakai"
else
  UV="$(cari_uv || true)"
  if [ -n "$UV" ]; then
    UV_LINK_MODE=copy "$UV" venv .venv -q 2>/dev/null && PYBIN="$DIR/.venv/bin/python" \
      && echo "  [ok] venv dibuat (uv)"
  fi
  if [ -z "$PYBIN" ] && python3 -m venv .venv 2>/dev/null && [ -x .venv/bin/python ]; then
    PYBIN="$DIR/.venv/bin/python"; echo "  [ok] venv dibuat (python3 -m venv)"
  fi
fi

pasang_dep() {
  local py="$1"
  if "$py" -m pip --version >/dev/null 2>&1; then
    "$py" -m pip install -q --upgrade pip 2>/dev/null
    "$py" -m pip install -q -r requirements.txt 2>/dev/null
  else
    local uv="$(cari_uv || true)"
    [ -n "$uv" ] && UV_LINK_MODE=copy "$uv" pip install -q --python "$py" -r requirements.txt 2>/dev/null
  fi
  "$py" -c "import starlette, uvicorn, httpx" 2>/dev/null
}

if [ -n "$PYBIN" ] && pasang_dep "$PYBIN"; then
  echo "  [ok] dependency siap di venv"
else
  # jalan terakhir: pakai python sistem + --user (venv sering gagal di Termux)
  echo "  [..] venv tidak bisa dipakai, coba python sistem"
  if python3 -c "import starlette, uvicorn, httpx" 2>/dev/null; then
    PYBIN="$(command -v python3)"; echo "  [ok] pakai python sistem (dependency sudah ada)"
  elif python3 -m pip install -q --user -r requirements.txt 2>/dev/null \
       && python3 -c "import starlette, uvicorn, httpx" 2>/dev/null; then
    PYBIN="$(command -v python3)"; echo "  [ok] dependency dipasang ke python sistem"
  else
    echo "  [!!] dependency BELUM terpasang. Coba manual:"
    echo "       pkg install python        # Termux"
    echo "       python3 -m pip install -r requirements.txt"
    PYBIN=""
  fi
fi
printf '%s\n' "$PYBIN" > .kosmate-runtime 2>/dev/null || true

echo "== 3/4 pasang profile web-builder"
mkdir -p "$SK/cozy-indie-game-ui/references" "$SK/kosmate-project" || exit 1
ambil() {
  python3 - "$1" "$2" <<'PY'
import sys, urllib.request
tujuan, url = sys.argv[1], sys.argv[2]
with urllib.request.urlopen(url, timeout=45) as r:
    d = r.read()
if len(d) < 40:
    raise SystemExit("kosong")
open(tujuan, "wb").write(d)
PY
}
coba_ambil() {
  local out="$1" url="$2" i=1
  while [ "$i" -le 3 ]; do
    if ambil "$out" "$url" 2>/dev/null; then return 0; fi
    sleep 2
    i=$((i+1))
  done
  return 1
}

n=0
for pair in \
  "SOUL.md|$H/profiles/web-builder/SOUL.md" \
  "skills/kosmate-project/SKILL.md|$SK/kosmate-project/SKILL.md" \
  "skills/cozy-indie-game-ui/SKILL.md|$SK/cozy-indie-game-ui/SKILL.md" \
  "skills/cozy-indie-game-ui/references/tokens.css|$SK/cozy-indie-game-ui/references/tokens.css" \
  "skills/cozy-indie-game-ui/references/pwa_shell.md|$SK/cozy-indie-game-ui/references/pwa_shell.md" \
  "skills/cozy-indie-game-ui/references/asset_pipeline.py|$SK/cozy-indie-game-ui/references/asset_pipeline.py"
do
  rel="${pair%%|*}"; out="${pair##*|}"
  mkdir -p "$(dirname "$out")"
  if coba_ambil "$out" "$RAW/$rel"; then n=$((n+1)); else echo "  [!!] gagal: $rel"; fi
done
echo "  [ok] $n/6 file profile terpasang"

echo "== 4/4 status"
if [ -f .env ]; then
  echo "  [ok] .env ada (key tersimpan)"
else
  echo "  [!!] .env BELUM ada — jalankan: bash scripts/autoinstall.sh"
fi
if [ -f AGENTS.md ]; then
  echo "  [ok] AGENTS.md ada — Hermes wajib baca ini dulu"
else
  echo "  [!!] AGENTS.md TIDAK ada — repo belum versi handoff, jalankan ulang script ini"
fi
if [ -n "${PYBIN:-}" ]; then echo "  [ok] python : $PYBIN"; else echo "  [!!] python : belum siap"; fi
printf '  versi  : %s\n' "$(cat VERSION 2>/dev/null || echo '?')"
printf '  commit : %s\n' "$(git -C "$DIR" log --oneline -1 2>/dev/null || echo '(tanpa git)')"
printf '  folder : %s\n' "$DIR"

cat <<TUTUP

  SELESAI. Buka Hermes di folder proyek lalu bilang:

     "baca AGENTS.md, lalu lanjutkan proyek Kosmate"

  Atau langsung lewat CLI:
     cd $DIR && hermes --profile web-builder

  Jalanin app-nya:
     cd $DIR && bash scripts/serve_local.sh 8080     # buka http://127.0.0.1:8080
TUTUP
