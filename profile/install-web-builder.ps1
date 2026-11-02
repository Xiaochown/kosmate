# Pasang profile 'web-builder' (SOUL + skill desain) di Hermes Windows.
# Jalankan:  powershell -ExecutionPolicy Bypass -File install-web-builder.ps1
$ErrorActionPreference = "Stop"
$Base = "https://raw.githubusercontent.com/Xiaochown/kosmate/main/profile/web-builder"
$Home_ = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA "hermes" }
$P = Join-Path $Home_ "profiles\web-builder"
$S = Join-Path $P "skills\cozy-indie-game-ui"

Write-Host "== target: $P"
New-Item -ItemType Directory -Force -Path (Join-Path $S "references") | Out-Null

$files = @(
  @{ rel = "SOUL.md"; out = (Join-Path $P "SOUL.md") },
  @{ rel = "skills/cozy-indie-game-ui/SKILL.md"; out = (Join-Path $S "SKILL.md") },
  @{ rel = "skills/cozy-indie-game-ui/references/tokens.css"; out = (Join-Path $S "references\tokens.css") },
  @{ rel = "skills/cozy-indie-game-ui/references/pwa_shell.md"; out = (Join-Path $S "references\pwa_shell.md") },
  @{ rel = "skills/cozy-indie-game-ui/references/asset_pipeline.py"; out = (Join-Path $S "references\asset_pipeline.py") }
)

$ok = 0
foreach ($f in $files) {
  try {
    Invoke-WebRequest -UseBasicParsing -Uri "$Base/$($f.rel)" -OutFile $f.out -TimeoutSec 40
    $n = (Get-Item $f.out).Length
    if ($n -lt 40) { throw "file terlalu kecil" }
    Write-Host ("  [ok] {0,-52} {1} byte" -f $f.rel, $n)
    $ok++
  } catch {
    Write-Host ("  [!!] gagal: {0}" -f $f.rel)
  }
}

Write-Host ""
if ($ok -eq 5) {
  Write-Host "  SELESAI ($ok/5 file). Profile siap dipakai."
  Write-Host ""
  Write-Host "  Jalankan:  hermes --profile web-builder"
  Write-Host "  Atau pilih profile 'web-builder' di UI desktop."
} else {
  Write-Host "  ADA YANG GAGAL ($ok/5). Cek koneksi lalu jalankan lagi."
  exit 1
}
