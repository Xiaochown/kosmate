"""join-project: pakai uv pip untuk dependency + retry unduhan file profile."""
import pathlib

p = pathlib.Path("/root/kosmate/profile/join-project.sh")
s = p.read_text()

# 1) dependency: pakai uv pip kalau venv dibuat uv (venv uv tidak punya pip)
s = s.replace('''pasang_dep() {
  "$1" -m pip install -q --upgrade pip 2>/dev/null
  "$1" -m pip install -q -r requirements.txt 2>/dev/null
  "$1" -c "import starlette, uvicorn, httpx" 2>/dev/null
}''', '''pasang_dep() {
  local py="$1"
  if "$py" -m pip --version >/dev/null 2>&1; then
    "$py" -m pip install -q --upgrade pip 2>/dev/null
    "$py" -m pip install -q -r requirements.txt 2>/dev/null
  else
    local uv="$(cari_uv || true)"
    [ -n "$uv" ] && UV_LINK_MODE=copy "$uv" pip install -q --python "$py" -r requirements.txt 2>/dev/null
  fi
  "$py" -c "import starlette, uvicorn, httpx" 2>/dev/null
}''')

# 2) unduhan: 3x percobaan (raw.githubusercontent kadang telat untuk file baru)
s = s.replace('''n=0''', '''coba_ambil() {
  local out="$1" url="$2" i=1
  while [ "$i" -le 3 ]; do
    if ambil "$out" "$url" 2>/dev/null; then return 0; fi
    sleep 2
    i=$((i+1))
  done
  return 1
}

n=0''')
s = s.replace('  if ambil "$out" "$RAW/$rel" 2>/dev/null; then n=$((n+1)); fi',
              '  if coba_ambil "$out" "$RAW/$rel"; then n=$((n+1)); else echo "  [!!] gagal: $rel"; fi')

p.write_text(s)
print("uv pip:", "uv\" pip install -q --python" in s)
print("retry :", "coba_ambil" in s)
