#!/usr/bin/env python3
"""
reverse-skill self-test: validate all SKILL.md files.

Inspired by dsh-reverse-skill _selftest.mjs — checks:
  - correct skill count
  - unique names
  - non-empty content per skill
  - parseable YAML front-matter (name + description)
  - BOM / CRLF tolerance
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# plugins/ and lib/ are stale plugin-packaging copies — exclude from count
EXCLUDE_DIRS = {"plugins", "lib", ".git", "node_modules", "__pycache__"}
EXPECTED = 88  # active skills (89 total minus plugins/ copy)

errors = []
warnings = []
info = {"with_bom": 0, "with_crlf": 0, "no_frontmatter": 0}


def parse_fm(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Tolerant of BOM and CRLF."""
    raw = text
    if raw.startswith("\ufeff"):
        info["with_bom"] += 1
        raw = raw[1:]
    if "\r\n" in raw:
        info["with_crlf"] += 1
    raw = raw.replace("\r\n", "\n")
    if not raw.startswith("---"):
        info["no_frontmatter"] += 1
        return {}, raw
    end = raw.find("\n---", 3)
    if end == -1:
        return {}, raw
    fm_text = raw[3:end]
    body = raw[end + 4:].lstrip("\n")
    fm = {}
    for line in fm_text.splitlines():
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            fm[key] = val
    return fm, body


def find_skill_files() -> list[Path]:
    """Recursively collect every SKILL.md, excluding stale copy dirs."""
    files = []
    for p in ROOT.rglob("SKILL.md"):
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        files.append(p)
    return files


def main():
    print(f"=== reverse-skill self-test ===")
    print(f"root: {ROOT}")

    skill_files = find_skill_files()
    print(f"\n[1] skill count: {len(skill_files)}")
    if len(skill_files) != EXPECTED:
        errors.append(
            f"expected {EXPECTED} SKILL.md, found {len(skill_files)}"
        )

    names = {}
    empty = []
    missing_name = []
    missing_desc = []

    for path in skill_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        fm, body = parse_fm(text)

        if "name" not in fm:
            missing_name.append(str(rel))
        else:
            name = fm["name"]
            if name in names:
                errors.append(
                    f"duplicate name '{name}': {names[name]} & {rel}"
                )
            else:
                names[name] = str(rel)

        if "description" not in fm:
            missing_desc.append(str(rel))

        if len(body.strip()) == 0:
            empty.append(str(rel))

    print(f"\n[2] unique names: {len(names)}")
    if len(names) != len(skill_files) - len(missing_name):
        dupes = len(skill_files) - len(missing_name) - len(names)
        errors.append(f"{dupes} duplicate name(s)")

    print(f"\n[3] empty body: {len(empty)}")
    for e in empty:
        errors.append(f"empty body: {e}")

    print(f"\n[4] missing name: {len(missing_name)}")
    for e in missing_name:
        errors.append(f"missing name: {e}")

    print(f"\n[5] missing description: {len(missing_desc)}")
    for e in missing_desc:
        warnings.append(f"missing description: {e}")

    print(f"\n[6] encoding: {info['with_bom']} with BOM, "
          f"{info['with_crlf']} with CRLF")

    # bonus: warn about stale copies in plugins/
    stale = list((ROOT / "plugins").rglob("SKILL.md")) if (ROOT / "plugins").exists() else []
    if stale:
        warnings.append(
            f"{len(stale)} stale SKILL.md in plugins/ (exclude from test, "
            f"consider removing)"
        )

    print(f"\n{'=' * 40}")
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  ⚠ {w}")
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\nFAILED ✗")
        sys.exit(1)
    else:
        print(f"ALL PASSED ✓  ({EXPECTED} skills valid)")
        sys.exit(0)


if __name__ == "__main__":
    main()
