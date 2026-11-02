import pathlib

p = pathlib.Path("/root/kosmate/profile/install-web-builder.sh")
s = p.read_text()
if "kosmate-project" not in s:
    s = s.replace(
        '  "skills/cozy-indie-game-ui/SKILL.md|$S/SKILL.md" \\',
        '  "skills/kosmate-project/SKILL.md|$P/skills/kosmate-project/SKILL.md" \\\n'
        '  "skills/cozy-indie-game-ui/SKILL.md|$S/SKILL.md" \\',
    )
    s = s.replace('if [ "$ok" -eq 5 ]; then', 'if [ "$ok" -eq 6 ]; then')
    s = s.replace('($ok/5 file)', '($ok/6 file)').replace('($ok/5)', '($ok/6)')
    s = s.replace('mkdir -p "$S/references"', 'mkdir -p "$S/references" "$P/skills/kosmate-project"')
    p.write_text(s)
print("kosmate-project di installer:", "kosmate-project" in p.read_text())
