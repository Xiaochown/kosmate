#!/usr/bin/env bash
# Pasang profile 'web-builder' (SOUL + skill desain) ke Hermes di device ini.
# Tidak menyentuh profile lain. Pakai python3 buat unduh (curl Termux sering rusak).
set -u

BASE="https://raw.githubusercontent.com/Xiaochown/kosmate/main/profile/web-builder"
H="${HERMES_HOME:-$HOME/.hermes}"
P="$H/profiles/web-builder"
S="$P/skills/cozy-indie-game-ui"

echo "== target: $P"
mkdir -p "$S/references" || { echo "gagal bikin folder"; exit 1; }

ambil() {
  python3 - "$1" "$2" <<'PY'
import sys, urllib.request
tujuan, url = sys.argv[1], sys.argv[2]
with urllib.request.urlopen(url, timeout=40) as r:
    data = r.read()
if len(data) < 40:
    raise SystemExit("isi file terlalu kecil: " + url)
open(tujuan, "wb").write(data)
PY
}

ok=0
for pair in \
  "SOUL.md|$P/SOUL.md" \
  "skills/cozy-indie-game-ui/SKILL.md|$S/SKILL.md" \
  "skills/cozy-indie-game-ui/references/tokens.css|$S/references/tokens.css" \
  "skills/cozy-indie-game-ui/references/pwa_shell.md|$S/references/pwa_shell.md" \
  "skills/cozy-indie-game-ui/references/asset_pipeline.py|$S/references/asset_pipeline.py"
do
  rel="${pair%%|*}"; out="${pair##*|}"
  if ambil "$out" "$BASE/$rel" 2>/dev/null; then
    printf '  [ok] %-52s %s byte\n' "$rel" "$(wc -c < "$out" | tr -d ' ')"
    ok=$((ok+1))
  else
    printf '  [!!] gagal: %s\n' "$rel"
  fi
done

echo
if [ "$ok" -eq 5 ]; then
  echo "  SELESAI ($ok/5 file). Profile siap dipakai."
  echo
  echo "  Langkah berikutnya di device ini:"
  echo "    hermes --profile web-builder          # langsung jalan pakai profile ini"
  echo "    hermes profile list                   # cek profile terdaftar"
  echo
  echo "  Di UI desktop: pilih profile 'web-builder' saat start sesi."
else
  echo "  ADA YANG GAGAL ($ok/5). Cek koneksi lalu jalankan lagi."
  exit 1
fi
