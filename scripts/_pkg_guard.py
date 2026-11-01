import pathlib

p = pathlib.Path("/root/kosmate/scripts/install.sh")
s = p.read_text()

# pkg install uv (fallback) -> hormati KOSMATE_SKIP_PKG
s = s.replace(
    '    pkg install -y uv >/dev/null 2>&1 || true',
    '    [ "${KOSMATE_SKIP_PKG:-0}" = "1" ] || pkg install -y uv >/dev/null 2>&1 || true',
)

# pkg install compiler (fallback kalau ada paket gagal build) -> hormati flag
s = s.replace(
    '  pkg install -y clang python-dev libffi openssl rust >/dev/null 2>&1 || true',
    '  [ "${KOSMATE_SKIP_PKG:-0}" = "1" ] || pkg install -y clang python-dev libffi openssl rust >/dev/null 2>&1 || true',
)

# python-pip fallback
s = s.replace(
    '    pkg install -y python-pip >/dev/null 2>&1 || true',
    '    [ "${KOSMATE_SKIP_PKG:-0}" = "1" ] || pkg install -y python-pip >/dev/null 2>&1 || true',
)

p.write_text(s)
print("sisa pkg install tanpa guard:", s.count("pkg install") - s.count('KOSMATE_SKIP_PKG"] = "1" ] || pkg install'))
for i, ln in enumerate(s.splitlines(), 1):
    if "pkg install" in ln:
        print(f"  {i}: {ln.strip()[:96]}")
