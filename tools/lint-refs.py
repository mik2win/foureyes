#!/usr/bin/env python3
"""Dead-reference gate for a project's committed agent instructions.

Every repo path that `CLAUDE.md` or a file under `.claude/` cites — in backticks or as a
markdown link — must exist. An agent sent to a "reference implementation" that was renamed
away follows a dead end, and nothing else in the repo fails when that rots.

  python3 tools/lint-refs.py                 # exit 1 on dead references
  python3 tools/lint-refs.py --baseline-mode # rewrite the baseline from current findings

Skipped: kit-owned files (`.claude/.kit-manifest.json` — their example paths are
stack-agnostic illustrations and `/update-kit` owns them); paths carrying a placeholder or a
glob (`<x>`, `*`, `{a,b}`, `NN`, `YYYY`); and gitignored local trees (the plans and backlog
locations from `PROJECT.md`, agent memory, worktrees) that never exist on a fresh clone.

A path cited on purpose although it does not exist — a rule saying "there is no `app/forms/`
layer", a hypothetical "e.g." — is recorded once in `.lint-refs-baseline` as `<file>|<path>`.
A baseline entry that no longer matches a finding is reported, so the file only ever shrinks.

Stdlib only. It is the project-side counterpart of `tools/validate-kit.py`, which checks the
same class of reference over the kit's own layout and over kit-owned files.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"[*{}<>$|\s]|\.\.\.|…|\bNN\b|YYYY|\bXXX\b")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
SCHEME_RE = re.compile(r"^[a-z]+://")

SCAN_GLOBS = [
    "CLAUDE.md", ".claude/PROJECT.md", ".claude/GUIDE.md", ".claude/CONTEXT.md",
    ".claude/rules/**/*.md", ".claude/references/**/*.md", ".claude/agents/*.md",
    ".claude/skills/**/*.md", ".claude/commands/*.md", ".claude/output-styles/*.md",
]
# Trees that exist on a laptop and never on a fresh clone. The plans and backlog locations
# are read from PROJECT.md and added to these.
LOCAL_ONLY = [".claude/agent-memory/", ".claude/worktrees/", ".claude/plans/"]


def git_root() -> Path:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return Path.cwd()


ROOT = git_root()
BASELINE_FILE = ROOT / ".lint-refs-baseline"


def read_project() -> str:
    for candidate in (ROOT / ".claude" / "PROJECT.md", ROOT / "PROJECT.md"):
        if candidate.exists():
            return candidate.read_text(encoding="utf-8", errors="ignore")
    return ""


def path_roots() -> list[str]:
    """First path segments worth resolving: the repo's own top-level directories, plus `.claude`.

    Deliberately the tree and not a hardcoded stack list, so the tool needs no per-project
    configuration. The trade-off it buys: a citation whose entire top-level root was deleted is
    not checked, because nothing is left to anchor it. This tool is for the common rot — a file
    renamed or moved inside a tree that still exists. Bare fragments that merely look like paths
    ("put it in `hooks/`") are not roots, and that is why they are not flagged.
    """
    roots = {p.name for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")}
    roots.add(".claude")
    return sorted(r for r in roots if r and r not in ("node_modules", "vendor"))


def local_only(project: str) -> list[str]:
    out = list(LOCAL_ONLY)
    for label in (r"Plans location", r"Backlog\s*/\s*decomposition location", r"Archive on done"):
        m = re.search(rf"(?i)\*\*{label}[^:]*:\*\*\s*(.+)", project)
        if not m:
            continue
        token = re.match(r"`([^`]+)`", m.group(1).strip())
        value = re.sub(r"<[^>]*>", "", token.group(1) if token else m.group(1).split()[0]).strip()
        if value and value not in ("n/a", "local"):
            out.append(value.rstrip("/") + "/")
    return out


def kit_owned() -> set[str]:
    manifest = ROOT / ".claude" / ".kit-manifest.json"
    if not manifest.exists():
        return set()
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except ValueError:
        return set()
    return {f".claude/{key}" for key in data.get("files", {})}


def scanned_files() -> list[str]:
    kit, seen = kit_owned(), []
    for pattern in SCAN_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            rel = str(path.relative_to(ROOT))
            if rel not in seen and rel not in kit and path.is_file():
                seen.append(rel)
    return sorted(seen)


def normalize(token: str) -> str:
    token = token.strip()
    token = re.sub(r"^\./", "", token)
    token = re.sub(r"#L?\d.*$", "", token)      # a line anchor in a link
    token = re.sub(r"::[\w:.#?!]+$", "", token)  # path.py::symbol
    token = re.sub(r":\d+(?:-\d+)?$", "", token)  # path.py:214, path.py:10-20
    return re.sub(r"[.,;:)]+$", "", token)


def is_candidate(path: str, roots: list[str], skip: list[str]) -> bool:
    if not path or PLACEHOLDER_RE.search(path) or SCHEME_RE.match(path):
        return False
    if any(path.startswith(prefix) for prefix in skip):
        return False
    return any(path.startswith(root + "/") for root in roots)


def exists(path: str, source: str) -> bool:
    return (ROOT / path).exists() or ((ROOT / source).parent / path).exists()


def main(argv: list[str]) -> int:
    if "--help" in argv or "-h" in argv:
        print(__doc__)
        return 0
    if not (ROOT / ".claude").is_dir():
        print("lint-refs: no .claude/ directory — nothing to check "
              "(in the kit's own repo, tools/validate-kit.py covers this)")
        return 0

    project = read_project()
    roots, skip = path_roots(), local_only(project)
    files = scanned_files()

    dead: list[tuple[str, str]] = []   # (key, message)
    checked = 0
    for source in files:
        in_fence = False
        for number, line in enumerate((ROOT / source).read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            tokens = BACKTICK_RE.findall(line) + LINK_RE.findall(line)
            seen_here: list[str] = []
            for token in tokens:
                path = normalize(token)
                if path in seen_here or not is_candidate(path, roots, skip):
                    continue
                seen_here.append(path)
                checked += 1
                if not exists(path, source):
                    dead.append((f"{source}|{path}", f"{source}:{number}: `{path}` does not exist"))

    keys = sorted({key for key, _ in dead})
    if "--baseline-mode" in argv:
        BASELINE_FILE.write_text("\n".join(keys) + ("\n" if keys else ""), encoding="utf-8")
        print(f"lint-refs: baseline written to {BASELINE_FILE.name} ({len(keys)} entries)")
        return 0

    baseline: set[str] = set()
    if BASELINE_FILE.exists():
        baseline = {l.strip() for l in BASELINE_FILE.read_text(encoding="utf-8").splitlines() if l.strip()}

    for key in sorted(baseline - set(keys)):
        print(f"lint-refs: stale baseline entry `{key}` — the reference is gone or now resolves; delete the line")

    new_dead = [msg for key, msg in dead if key not in baseline]
    if not new_dead:
        suppressed = len([k for k in keys if k in baseline])
        extra = f", {suppressed} baselined" if suppressed else ""
        print(f"lint-refs: OK ({checked} path references in {len(files)} files{extra})")
        return 0

    print(f"lint-refs: {len(new_dead)} dead reference(s) of {checked} checked in {len(files)} files")
    for msg in new_dead:
        print(msg)
    print()
    print("Point each reference at the file that now holds the code, or drop it if nothing does.")
    print(f"A path cited on purpose (a rule naming a layer that must not exist) goes into {BASELINE_FILE.name}.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
