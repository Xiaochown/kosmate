"""Perbaiki join-project.sh: deteksi uv, fallback venv, status jujur."""
import pathlib

p = pathlib.Path("/root/kosmate/profile/join-project.sh")
s = p.read_text()

# --- ganti blok dependency ---
lama_awal = s.index('echo "== 2/4 dependency python"')
lama_akhir = s.index('echo "== 3/4 pasang profile web-builder"')
baru = '''echo "== 2/4 dependency python"
cd "$DIR" || { echo "  [!!] folder tidak bisa dibuka"; exit 1; }

cari_uv() {
  for k in "$(command -v uv 2>/dev/null)" "$HOME/.local/bin/uv" "$HOME/.hermes/bin/uv" \\
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
    UV_LINK_MODE=copy "$UV" venv .venv -q 2>/dev/null && PYBIN="$DIR/.venv/bin/python" \\
      && echo "  [ok] venv dibuat (uv)"
  fi
  if [ -z "$PYBIN" ] && python3 -m venv .venv 2>/dev/null && [ -x .venv/bin/python ]; then
    PYBIN="$DIR/.venv/bin/python"; echo "  [ok] venv dibuat (python3 -m venv)"
  fi
fi

pasang_dep() {
  "$1" -m pip install -q --upgrade pip 2>/dev/null
  "$1" -m pip install -q -r requirements.txt 2>/dev/null
  "$1" -c "import starlette, uvicorn, httpx" 2>/dev/null
}

if [ -n "$PYBIN" ] && pasang_dep "$PYBIN"; then
  echo "  [ok] dependency siap di venv"
else
  # jalan terakhir: pakai python sistem + --user (venv sering gagal di Termux)
  echo "  [..] venv tidak bisa dipakai, coba python sistem"
  if python3 -c "import starlette, uvicorn, httpx" 2>/dev/null; then
    PYBIN="$(command -v python3)"; echo "  [ok] pakai python sistem (dependency sudah ada)"
  elif python3 -m pip install -q --user -r requirements.txt 2>/dev/null \\
       && python3 -c "import starlette, uvicorn, httpx" 2>/dev/null; then
    PYBIN="$(command -v python3)"; echo "  [ok] dependency dipasang ke python sistem"
  else
    echo "  [!!] dependency BELUM terpasang. Coba manual:"
    echo "       pkg install python        # Termux"
    echo "       python3 -m pip install -r requirements.txt"
    PYBIN=""
  fi
fi
printf '%s\\n' "$PYBIN" > .kosmate-runtime 2>/dev/null || true

'''
s = s[:lama_awal] + baru + s[lama_akhir:]

# --- status jujur ---
lama_status = s.index('echo "== 4/4 status"')
akhir_status = s.index('cat <<TUTUP')
status = '''echo "== 4/4 status"
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
printf '  versi  : %s\\n' "$(cat VERSION 2>/dev/null || echo '?')"
printf '  commit : %s\\n' "$(git -C "$DIR" log --oneline -1 2>/dev/null || echo '(tanpa git)')"
printf '  folder : %s\\n' "$DIR"

'''
s = s[:lama_status] + status + s[akhir_status:]
p.write_text(s)
print("cari_uv:", "cari_uv" in s, "| status jujur:", "[ok] AGENTS.md ada" in s)
