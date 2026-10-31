#!/usr/bin/env bash
# Kosmate :: perbaikan suara sekali jalan
#   1) ambil kode terbaru (zip, data/ & .env aman)
#   2) pastikan FISH_API_KEY valid (tanya sekali, input tersembunyi)
#   3) set voice Miyaa
#   4) restart server + cetak status
set -u
cd "$(dirname "$0")" 2>/dev/null || cd "$HOME/kosmate" || exit 1
[ -f install.sh ] || { echo "  [!!] install.sh tidak ada di folder ini"; exit 1; }

ok(){ printf '  [ok] %s\n' "$*"; }
warn(){ printf '  [!!] %s\n' "$*"; }
step(){ printf '\n== %s ==\n' "$*"; }

# ---------- 1. kode terbaru ----------
step "1/4 ambil kode terbaru"
ORIG="$(pwd)"
TMPD="$(mktemp -d 2>/dev/null || echo "$ORIG/.tmp-fix")"
mkdir -p "$TMPD"
python - "$TMPD/install.sh" <<'PY' 2>/dev/null || cp install.sh "$TMPD/install.sh"
import sys, urllib.request
url = "https://raw.githubusercontent.com/Xiaochown/kosmate/main/install.sh"
data = urllib.request.urlopen(url, timeout=60).read()
open(sys.argv[1], "wb").write(data)
PY
if KOSMATE_FORCE_ZIP=1 KOSMATE_DIR="$ORIG" bash "$TMPD/install.sh" --no-install >/dev/null 2>&1; then
  ok "kode diperbarui"
else
  warn "gagal unduh kode baru — lanjut pakai kode yang ada"
fi
rm -rf "$TMPD"
[ -f .env ] || cp .env.example .env

# ---------- 2. dependency ----------
step "2/4 cek dependency"
if bash scripts/install.sh >/dev/null 2>&1; then ok "dependency siap"; else warn "install.sh melaporkan masalah (server mungkin tetap jalan)"; fi

# ---------- 3. key Fish ----------
step "3/4 Fish Audio key"
CUR="$(grep -E '^FISH_API_KEY=' .env 2>/dev/null | head -1 | cut -d= -f2- | tr -d '[:space:]')"
if [ -n "${KOSMATE_FISH_KEY:-}" ]; then
  NEW="$KOSMATE_FISH_KEY"
elif [ "${#CUR}" -ge 20 ] && [ "${CUR#FIS...}" = "$CUR" ]; then
  NEW=""
  ok "key sudah ada (${#CUR} karakter) — tidak ditanya lagi"
else
  echo "  tempel Fish Audio API key, lalu Enter (input gak kelihatan):"
  printf '  key: '
  read -rs NEW < /dev/tty || read -rs NEW || true
  echo
  NEW="$(printf '%s' "${NEW:-}" | tr -d '[:space:]')"
fi

if [ -n "${NEW:-}" ]; then
  if [ "${#NEW}" -lt 20 ]; then
    warn "key kepotong (${#NEW} karakter) — nanti isi manual: bash scripts/set_key.sh"
  else
    python - "$NEW" <<'PY'
import pathlib, sys
key = sys.argv[1]
p = pathlib.Path(".env")
lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
out, done = [], False
for line in lines:
    s = line.strip()
    if s.startswith("FISH_API_KEY="):
        out.append(f"FISH_API_KEY={key}"); done = True
    elif s.startswith("FISH_API_KEY") and "=" not in s:
        continue
    else:
        out.append(line)
if not done:
    out.append(f"FISH_API_KEY={key}")
p.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"  [ok] FISH_API_KEY tersimpan ({len(key)} karakter)")
PY
  fi
fi

# ---------- 4. voice + restart ----------
step "4/4 set voice Miyaa & restart"
mkdir -p data
printf '{\n  "key": "miyaa"\n}\n' > data/voice.json
ok "voice: Miyaa (perempuan, 0.80x) — bisa diganti di ⚙ → Suara"
bash scripts/restart.sh
RC=$?

printf '\n=== SELESAI ===\n'
if [ "$RC" = "0" ]; then
  printf '  buka: http://127.0.0.1:8080\n'
  printf '  lalu: ⚙ → Suara  (Miyaa / Kang Dedi / Prabowo)\n'
  printf '  tes  : ⚙ → Diagnostik → "tes suara"\n'
else
  printf '  server belum hidup — kirim 20 baris log di atas ke gw\n'
fi
exit "$RC"
