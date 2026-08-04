#!/usr/bin/env python3
"""Structural validation for the FourEyes kit.

Everything here is a property the kit already relies on being true. Nothing is style.
Stdlib only — no pip install on the runner, and it runs identically on a laptop.

  python3 tools/validate-kit.py          # check, exit 1 on any error
  python3 tools/validate-kit.py --stats  # also print the listing-budget table
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The harness truncates `description` + `when_to_use` at this many characters in the
# skill listing. A skill that overruns it silently loses its trailing keywords — the
# very ones Claude matches a prompt against. Source: code.claude.com/docs/en/skills.
LISTING_CAP = 1536

errors: list[str] = []
warnings: list[str] = []


def err(path: Path, msg: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {msg}")


def warn(path: Path, msg: str) -> None:
    warnings.append(f"{path.relative_to(ROOT)}: {msg}")


def parse_frontmatter(text: str) -> dict | None:
    """Minimal YAML-frontmatter reader for the flat `key: value` shape the kit uses.

    Handles folded/literal block scalars (`>`, `>-`, `|`) because every skill
    description is written as one. Returns None when there is no frontmatter at all.
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    body = text[4:end].split("\n")

    data: dict[str, str] = {}
    key = None
    block: list[str] = []
    for line in body:
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if m and not line.startswith((" ", "\t")):
            if key is not None:
                data[key] = " ".join(s.strip() for s in block).strip()
            key, first = m.group(1), m.group(2).strip()
            block = [] if first in (">", ">-", "|", "|-", "") else [first]
        elif key is not None:
            block.append(line)
    if key is not None:
        data[key] = " ".join(s.strip() for s in block).strip()
    return data


def check_frontmatter_syntax() -> None:
    """Every frontmatter block must survive a real YAML parser.

    The reader above is deliberately forgiving; the harness's is not. The failure that
    actually happens: a plain (unquoted) scalar containing `": "` — `memory: project`,
    `concurrently: disjoint` — which YAML reads as a nested mapping key and rejects. The
    file then loads with no `paths:`, silently. Backticks mean nothing to a parser.

    PyYAML is used when importable; the hazard lint below is stdlib and always runs, so
    a laptop without PyYAML still catches the class.
    """
    try:
        import yaml  # noqa: PLC0415 — optional; the lint below is the stdlib fallback
    except ImportError:
        yaml = None

    targets = sorted(ROOT.glob("skills/*/SKILL.md")) + sorted(ROOT.glob("agents/*.md")) \
        + sorted(ROOT.glob("rules/**/*.md"))
    for path in targets:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            continue
        end = text.find("\n---", 3)
        if end == -1:
            err(path, "frontmatter opened but never closed")
            continue
        block = text[4:end]

        if yaml is not None:
            try:
                yaml.safe_load(block)
            except Exception as exc:  # noqa: BLE001 — any parser complaint is fatal
                err(path, f"frontmatter is not valid YAML: {str(exc).splitlines()[0]}")
                continue

        for i, line in enumerate(block.splitlines(), 2):
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):[ \t]+(\S.*)$", line)
            if not m:
                continue
            value = m.group(2).rstrip()
            if value[0] in "\"'>|[{#&*!%@`":  # quoted, block, flow, or already-indicated
                continue
            if ": " in value or value.endswith(":") or " #" in value:
                err(path, f"line {i}: plain scalar for `{m.group(1)}` carries a YAML "
                          f"indicator — fold it into a `>-` block")


def check_frontmatter_files() -> list[tuple[Path, dict]]:
    """skills/*/SKILL.md and agents/*.md must carry a name + description."""
    found = []
    for path in sorted(ROOT.glob("skills/*/SKILL.md")):
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            err(path, "no YAML frontmatter")
            continue
        expected = path.parent.name
        if fm.get("name") != expected:
            err(path, f"frontmatter name {fm.get('name')!r} != directory {expected!r}")
        if not fm.get("description"):
            err(path, "empty or missing description")
        found.append((path, fm))

    for path in sorted(ROOT.glob("agents/*.md")):
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm is None:
            err(path, "no YAML frontmatter")
            continue
        if fm.get("name") != path.stem:
            err(path, f"frontmatter name {fm.get('name')!r} != filename {path.stem!r}")
        if not fm.get("description"):
            err(path, "empty or missing description")
        if not fm.get("tools"):
            warn(path, "no explicit `tools:` — the agent inherits everything")
    return found


def check_listing_budget(skills: list[tuple[Path, dict]], stats: bool) -> None:
    """Only model-invocable skills claim listing budget; each is capped per-skill."""
    invocable = [
        (p, fm) for p, fm in skills
        if str(fm.get("disable-model-invocation", "")).lower() != "true"
    ]
    rows = []
    for path, fm in invocable:
        size = len(fm.get("description", "")) + len(fm.get("when_to_use", ""))
        rows.append((size, path.parent.name))
        if size > LISTING_CAP:
            err(path, f"description is {size} chars, over the {LISTING_CAP} listing cap "
                      f"— the harness will truncate it and strip its trailing keywords")
        elif size > LISTING_CAP * 0.9:
            warn(path, f"description is {size} chars, within 10% of the {LISTING_CAP} cap")

    if stats:
        total = sum(s for s, _ in rows)
        print(f"\nListing budget — {len(invocable)} model-invocable of {len(skills)} skills, "
              f"{total} chars total")
        for size, name in sorted(rows, reverse=True):
            bar = "#" * max(1, round(size / LISTING_CAP * 40))
            print(f"  {size:5d}/{LISTING_CAP}  {bar:<40}  {name}")


FENCE = re.compile(r"^```.*?^```", re.S | re.M)
INLINE_CODE = re.compile(r"`([^`\n]+)`")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+\.md)(?:#[^)]*)?\)")

# Directories the kit itself owns. A backticked path starting with one of these names a
# kit file and must resolve from the kit root — the same string in a skill is what a
# session will hand to Read. Two deliberate exclusions:
#   · a `.claude/`-prefixed path describes the *installed* layout in someone else's
#     project, which does not exist here and is not ours to check;
#   · `docs/` counts only in its flat form — `docs/adr/…` is the project's ADR
#     directory, which the kit does not ship.
KIT_DIRS = ("rules/", "skills/", "agents/", "hooks/", "_kit/", "schemas/")

KIT_PATH = re.compile(
    r"^((?:" + "|".join(map(re.escape, KIT_DIRS)) + r")\S*\.md|docs/[^/`]+\.md)$"
)


def _placeholder(target: str) -> bool:
    return any(c in target for c in "<>$*")


def check_links() -> None:
    """Two classes of reference, both of which have gone stale in this kit before.

    1. Markdown links — resolved from the linking file's own directory.
    2. Backticked kit paths — resolved from the kit root. This is the class that bites:
       a skill telling a session to `Read` a path is a link the reader follows, but no
       markdown tooling has ever checked it.
    """
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in (".git", "_backlog"):
            continue
        raw = path.read_text(encoding="utf-8")
        prose = INLINE_CODE.sub(" ", FENCE.sub("", raw))

        for target in MD_LINK.findall(prose):
            if target.startswith(("http://", "https://", ".claude/")) or _placeholder(target):
                continue
            if not (path.parent / target).exists():
                err(path, f"dead link -> {target}")

        for span in INLINE_CODE.findall(FENCE.sub("", raw)):
            span = span.strip()
            if _placeholder(span) or not KIT_PATH.match(span):
                continue
            if not (ROOT / span.removeprefix(".claude/")).exists():
                err(path, f"dead kit path in backticks -> {span}")


def check_hooks() -> None:
    """Hooks must parse and be executable — a non-executable hook fails silently."""
    for path in sorted(ROOT.glob("hooks/*.sh")):
        if subprocess.run(["bash", "-n", str(path)], capture_output=True).returncode != 0:
            err(path, "bash syntax error")
        if not path.stat().st_mode & 0o111:
            err(path, "not executable — the harness will not run it")


def check_json() -> None:
    for path in sorted(ROOT.rglob("*.json")):
        if ".git" in path.parts or "_backlog" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err(path, f"invalid JSON: {e}")


def check_no_local_paths() -> None:
    """A machine-local absolute path in a shipped file is a leak and breaks on clone."""
    pattern = re.compile(r"/Users/[a-z0-9_-]+/", re.I)
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if not path.is_file() or rel.parts[0] in (".git", "_backlog", "tools"):
            continue
        if path.suffix not in (".md", ".json", ".sh", ".yaml", ".yml"):
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if pattern.search(line):
                err(path, f"line {i}: machine-local absolute path")


def main() -> int:
    stats = "--stats" in sys.argv
    check_frontmatter_syntax()
    skills = check_frontmatter_files()
    check_listing_budget(skills, stats)
    check_links()
    check_hooks()
    check_json()
    check_no_local_paths()

    for w in warnings:
        print(f"warn  {w}")
    for e in errors:
        print(f"ERROR {e}")

    print(f"\n{len(skills)} skills · {len(list(ROOT.glob('agents/*.md')))} agents · "
          f"{len(list(ROOT.glob('hooks/*.sh')))} hooks checked — "
          f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
