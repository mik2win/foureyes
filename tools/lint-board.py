#!/usr/bin/env python3
"""Report-only checks over a wave-structured backlog board (`<epic>/RUN-ORDER.md`).

It answers the mechanical half of `/epic-status` deterministically, so a parallel launch never
rests on a model noticing that two rows claim the same file. Never edits anything, never blocks.

Board format: `skills/prepare/reference/parallel-wave-execution.md` § RUN-ORDER.
Stdlib only — no install step, and it runs identically on a laptop and in a hook.

  python3 tools/lint-board.py status [--epic NAME] [--oneline]
  python3 tools/lint-board.py lint   [--epic NAME] [--quiet] [--strict]
  python3 tools/lint-board.py hook   < hook.json

Locations come from `.claude/PROJECT.md` (Plans / backlog), and `--dir` overrides.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HELP = __doc__

# Directories under the backlog root that are never epics.
NON_EPIC_DIRS = {"realised", "realized", "issues", "archive", "archived", "_archive", "_tools"}

ROW_ID_RE = re.compile(r"^(?:[A-Z]{1,2}\d+(?:\.\d+)?|\d+\.\d+)[a-z]?")
PROMPT_HEADING_RE = re.compile(r"^###\s+(?:Prompt\s+)?((?:[A-Z]{1,2}\d+(?:\.\d+)?|\d+\.\d+)[a-z]?)\b")
PROMPT_TARGET_RE = re.compile(r"^/(?:implement|prepare)\s+(\S+\.md)\b")
BACKTICK_RE = re.compile(r"`([^`]+)`")
PLAN_STATUS_RE = re.compile(r"\bstatus\b\**\s*:\s*\**\s*([A-Za-z][A-Za-z-]*)", re.I)

TERMINAL_PLAN = {"DONE", "PARTIAL", "CLOSED", "SKIPPED", "FOLDED", "SUPERSEDED", "REALISED", "REALIZED"}
ACTIVE_PLAN = {"READY", "PREPARED", "PLANNED", "OPEN", "PROPOSED", "DRAFT", "IN-PROGRESS", "BLOCKED", "GATED"}


# --------------------------------------------------------------------------- paths & globs

def expand_braces(token: str) -> list[str]:
    m = re.search(r"\{([^{}]*)\}", token)
    if not m:
        return [token]
    out = []
    for part in m.group(1).split(","):
        out.extend(expand_braces(token[: m.start()] + part + token[m.end():]))
    return out


def path_like(token: str) -> bool:
    if re.search(r"[\s<>$]", token) or token.startswith("/"):
        return False
    return "/" in token or bool(re.fullmatch(r"[\w.-]+\.[a-z]{1,5}", token))


def is_glob(path: str) -> bool:
    return "*" in path


def _seg_regex(seg: str) -> str:
    """One path segment of a glob → regex source. `*` never crosses a `/`."""
    out, i = "", 0
    while i < len(seg):
        c = seg[i]
        if c == "*":
            out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        elif c == "[":
            close = seg.find("]", i + 1)
            if close == -1:
                out += re.escape(c)
            else:
                body = seg[i + 1:close]
                out += "[" + ("^" + body[1:] if body.startswith("!") else body) + "]"
                i = close
        else:
            out += re.escape(c)
        i += 1
    return out


def _glob_regex(pattern: str) -> re.Pattern:
    """Pathname-semantics glob: `**` spans directories, `*` does not."""
    if pattern.endswith("/**"):
        pattern = pattern[:-3] + "/**/*"
    segs = pattern.split("/")
    src = ""
    for i, seg in enumerate(segs):
        if seg == "**":
            src += "(?:[^/]+/)*"
        else:
            src += _seg_regex(seg) + ("/" if i < len(segs) - 1 else "")
    return re.compile("^" + src + "$")


def fnmatch_path(pattern: str, path: str) -> bool:
    return bool(_glob_regex(pattern).match(path))


def _seg_match(pattern: str, text: str) -> bool:
    return bool(re.fullmatch(_seg_regex(pattern), text))


def globs_overlap(xs: list[str], ys: list[str]) -> bool:
    """Two globs can name the same file — compared segment by segment."""
    if (xs and xs[0] == "**") or (ys and ys[0] == "**"):
        return True
    if not xs or not ys:
        return not xs and not ys
    same = xs[0] == ys[0] or _seg_match(xs[0], ys[0]) or _seg_match(ys[0], xs[0])
    return same and globs_overlap(xs[1:], ys[1:])


def overlap(a: str, b: str) -> bool:
    """Can these two `Owns` tokens ever name the same file?"""
    if a == b:
        return True
    if is_glob(a) and is_glob(b):
        return globs_overlap(a.split("/"), b.split("/"))
    for x, y in ((a, b), (b, a)):
        if is_glob(x):
            if fnmatch_path(x, y) or (y.endswith("/") and x.startswith(y)):
                return True
        elif "/" not in x:
            if os.path.basename(y) == x:
                return True
        elif x.endswith("/") and y.startswith(x):
            return True
    return False


# --------------------------------------------------------------------------- model

class Row:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    @property
    def terminal(self) -> bool:
        return self.status in ("done", "skipped")

    @property
    def session(self) -> bool:
        return not self.operator and not (self.mode is None or re.fullmatch(r"[—-]?", self.mode.strip()))


class Finding:
    def __init__(self, kind: str, message: str):
        self.kind, self.message = kind, message

    def __eq__(self, other):
        return (self.kind, self.message) == (other.kind, other.message)

    def __hash__(self):
        return hash((self.kind, self.message))


class Epic:
    def __init__(self, name, directory, board, rows, prompts, findings=None, plans=None):
        self.name, self.dir, self.board = name, directory, board
        self.rows, self.prompts, self.findings, self.plans = rows, prompts, findings or [], plans


def read_plan_status(path: Path) -> tuple[str, int] | None:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], start=2):
            if line.strip() == "---":
                break
            m = re.match(r"status:\s*[\"']?([A-Za-z][A-Za-z-]*)", line)
            if m:
                return m.group(1).upper(), i
    for i, line in enumerate(lines[:25], start=1):
        m = PLAN_STATUS_RE.search(line)
        if m:
            return m.group(1).upper(), i
    return None


# --------------------------------------------------------------------------- board parsing

class BoardParser:
    def __init__(self, epic_dir: Path):
        self.dir = epic_dir
        self.path = epic_dir / "RUN-ORDER.md"
        self.lines = self.path.read_text(encoding="utf-8", errors="ignore").splitlines()

    def parse_rows(self) -> list[Row]:
        rows, columns = [], None
        for index, line in enumerate(self.lines, start=1):
            if not line.startswith("|"):
                columns = None
                continue
            cells = self._split_cells(line)
            if all(re.fullmatch(r":?-+:?", c) for c in cells):
                continue
            if columns is None:
                columns = self._header_columns(cells)
                continue
            if not columns["board"]:
                continue
            row = self._build_row(cells, columns, index)
            if row:
                rows.append(row)
        return rows

    def parse_prompts(self) -> dict[str, dict]:
        found: dict[str, dict] = {}
        current = None
        for index, line in enumerate(self.lines, start=1):
            m = PROMPT_HEADING_RE.match(line)
            if m:
                current = m.group(1)
                found.setdefault(current, {"line": index, "targets": []})
            elif line.startswith(("## ", "### ")):
                current = None
            elif current:
                t = PROMPT_TARGET_RE.match(line)
                if t:
                    found[current]["targets"].append(t.group(1))
        return found

    @staticmethod
    def _split_cells(line: str) -> list[str]:
        body = re.sub(r"\|$", "", re.sub(r"^\|", "", line.strip()))
        return [c.strip() for c in re.split(r"(?<!\\)\|", body)]

    @staticmethod
    def _header_columns(cells: list[str]) -> dict:
        def find(pattern):
            for i, cell in enumerate(cells):
                if re.search(pattern, cell):
                    return i
            return None

        cols = {
            "id": find(r"^#$"), "status": find(r"(?i)^status$"), "owns": find(r"(?i)^owns$"),
            "deps": find(r"(?i)^depends"), "mode": find(r"(?i)^mode$"), "card": find(r"(?i)^card"),
        }
        cols["board"] = cols["id"] is not None and cols["status"] is not None
        return cols

    def _build_row(self, cells: list[str], columns: dict, line: int) -> Row | None:
        def cell(key):
            i = columns[key]
            return cells[i] if i is not None and i < len(cells) else ""

        id_cell = cell("id")
        m = ROW_ID_RE.match(id_cell)
        if not m:
            return None
        row_id = m.group(0)
        owns_cell, card_cell = cell("owns"), cell("card")
        owned, plan_refs = self._split_owns(owns_cell)
        status_text = cell("status")
        operator = row_id.startswith("C") or columns["owns"] is None or bool(re.fullmatch(r"[—-]?", owns_cell))
        wave_m = re.match(r"\d+", row_id)
        return Row(
            id=row_id, line=line, wave=wave_m.group(0) if wave_m else row_id,
            parallel="∥" in id_cell, mode=cell("mode") if columns["mode"] is not None else None,
            card_cell=card_cell, deps_raw=cell("deps"), owns=owned, plan_refs=plan_refs,
            card_refs=[] if operator else self._card_refs(card_cell),
            status=self._normalize_status(status_text), status_text=status_text, operator=operator,
        )

    @staticmethod
    def _split_owns(cell: str) -> tuple[list[tuple[str, tuple[str, ...]]], list[str]]:
        """Owns cell → (owned paths with their prose exclusions, referenced plan/card files)."""
        owned, refs = [], []
        for m in BACKTICK_RE.finditer(cell):
            token = re.sub(r"^(?:new|optional)\s+", "", m.group(1).strip())
            if not path_like(token):
                continue
            if token.endswith(".md") and re.search(r"(^|/)(plans|cards)/", token):
                refs.append(token)
                continue
            clause = re.match(r"[^,`]*", cell[m.end():]).group(0)
            excluded = tuple(re.findall(r"\b\d+\.\d+[a-z]?\b", clause)) if re.search(r"\bexcept\b", clause) else ()
            for path in expand_braces(token):
                if (path, excluded) not in owned:
                    owned.append((path, excluded))
        return owned, refs

    @staticmethod
    def _card_refs(cell: str) -> list[tuple[str, str]]:
        paths = [t for t in BACKTICK_RE.findall(cell) if t.endswith(".md")]
        if paths:
            return [("path", p) for p in paths]
        head = re.split(r"\s+—\s+", cell, maxsplit=1)[0]
        seen, out = set(), []
        for n in re.findall(r"(?<![#\d])(\d{2}[a-z]?)(?!\d)", head):
            if n not in seen:
                seen.add(n)
                out.append(("number", n))
        return out

    @staticmethod
    def _normalize_status(text: str) -> str:
        value = re.sub(r"[*`_]", "", text).strip().lower()
        if value in ("", "—", "-") or re.match(r"(open|todo|to do|planned|prepared|ready|proposed|not started)\b", value):
            return "open"
        if re.match(r"(done|✅|closed|landed|merged|complete)", value):
            return "done"
        if re.match(r"(skipped|skip|deferred|dropped|cancel|not needed|folded|superseded|won't)", value):
            return "skipped"
        if re.match(r"(blocked|❌|gated|on hold)", value):
            return "blocked"
        if re.match(r"(in[- ]progress|wip|running|started|partial)", value):
            return "in_progress"
        return "unknown"


# --------------------------------------------------------------------------- the checks

class EpicLinter:
    def __init__(self, epic: Epic, ctx: "Context"):
        self.epic, self.ctx = epic, ctx
        self.rows = epic.rows
        self.by_id = {row.id: row for row in self.rows}
        self._deps = None

    @property
    def deps(self) -> dict[str, list[str]]:
        if self._deps is None:
            self._deps = {row.id: self._resolve_deps(row) for row in self.rows}
        return self._deps

    def run(self) -> list[Finding]:
        if not self.rows:
            return [Finding("empty", f"no board rows parsed from {self.ctx.display(self.epic.board)} — nothing checked")]
        found = [*self._status(), *self._dep_findings(), *self._overlaps(),
                 *self._brief(), *self._missing(), *self._drift()]
        out = []
        for f in found:
            if f not in out:
                out.append(f)
        return out

    def _resolve_deps(self, row: Row) -> list[str]:
        raw = re.sub(r"[*`]", "", row.deps_raw)
        ids: list[str] = []
        for wave in re.findall(r"(?i)wave\s+(\d+)", raw):
            ids.extend(o.id for o in self.rows if o.wave == wave and not o.operator and o.id != row.id)
        for wave, start, end in re.findall(r"(?P<w>\d+)\.(\d+)\s*[–-]\s*(?:(?P=w)\.)?(\d+)", raw):
            ids.extend(f"{wave}.{minor}" for minor in range(int(start), int(end) + 1))
        stripped = re.sub(r"(\d+)\.(\d+)\s*[–-]\s*(?:\d+\.)?\d+", "", raw)
        ids.extend(re.findall(r"(?<![\d.])((?:[A-Z]{1,2})?\d+\.\d+[a-z]?)(?![\d.])", stripped))
        ids.extend(re.findall(r"(?<![\w.])([A-Z]{1,2}\d+)(?![\w.])", stripped))
        out = []
        for i in ids:
            if i not in out:
                out.append(i)
        return out

    def _status(self) -> list[Finding]:
        return [Finding("status", f"{row.id}: Status `{row.status_text[:60]}` is outside the vocabulary ({self._loc(row)})")
                for row in self.rows if row.status == "unknown"]

    def _dep_findings(self) -> list[Finding]:
        out = []
        for row in self.rows:
            for dep in self.deps[row.id]:
                other = self.by_id.get(dep)
                if other is None:
                    out.append(Finding("deps", f"{row.id} depends on {dep}, which is not on the board ({self._loc(row)})"))
                elif row.status == "done" and not other.terminal:
                    out.append(Finding("deps", f"{row.id} is done but its dependency {dep} is {other.status} ({self._loc(row)}, {self._loc(other)})"))
        out.extend(Finding("deps", "dependency cycle: " + " → ".join(cycle)) for cycle in self._cycles())
        return out

    def _cycles(self) -> list[list[str]]:
        found: list[list[str]] = []
        state: dict[str, str] = {}

        def visit(node: str, stack: list[str]) -> None:
            if state.get(node) == "done":
                return
            if state.get(node) == "active":
                found.append(stack[stack.index(node):] + [node])
                return
            state[node] = "active"
            for dep in self.deps.get(node, []):
                if dep in self.by_id:
                    visit(dep, stack + [node])
            state[node] = "done"

        for row in self.rows:
            visit(row.id, [])
        seen, out = set(), []
        for cycle in found:
            key = tuple(sorted(cycle))
            if key not in seen:
                seen.add(key)
                out.append(cycle)
        return out

    def _reachable(self, src: str, dst: str, seen: set[str] | None = None) -> bool:
        seen = set() if seen is None else seen
        if src in seen:
            return False
        seen.add(src)
        return any(dep == dst or self._reachable(dep, dst, seen) for dep in self.deps.get(src, []))

    def _overlaps(self) -> list[Finding]:
        live = [r for r in self.rows if not r.terminal and not r.operator and r.owns]
        out = []
        for i, a in enumerate(live):
            for b in live[i + 1:]:
                if self._reachable(a.id, b.id) or self._reachable(b.id, a.id):
                    continue
                shared = []
                for x, x_ex in a.owns:
                    for y, y_ex in b.owns:
                        if b.id in x_ex or a.id in y_ex:
                            continue
                        if overlap(x, y):
                            shared.append((x, y))
                if not shared:
                    continue
                sample = ", ".join(f"`{x}`" if x == y else f"`{x}` ~ `{y}`" for x, y in shared[:3])
                more = f" (+{len(shared) - 3} more)" if len(shared) > 3 else ""
                out.append(Finding("overlap", f"{a.id} ↔ {b.id} may run concurrently (no dependency either way) "
                                              f"and both own {sample}{more} ({self._loc(a)}, {self._loc(b)})"))
        return out

    def _brief(self) -> list[Finding]:
        if not self.epic.prompts:
            return []
        out = [Finding("brief", f"{row.id} is an unfinished session row with no prompt heading ({self._loc(row)})")
               for row in self.rows if row.session and not row.terminal and row.id not in self.epic.prompts]
        for pid in self.epic.prompts:
            if pid not in self.by_id:
                out.append(Finding("brief", f"prompt {pid} has no board row ({self.ctx.display(self.epic.board)}:{self.epic.prompts[pid]['line']})"))
        return out

    def _missing(self) -> list[Finding]:
        out = []
        for row in self.rows:
            for kind, value in row.card_refs:
                if not self._resolve_card(kind, value):
                    out.append(Finding("missing", f"{row.id}: card `{value}` resolves to no file ({self._loc(row)})"))
            for path in self._plan_paths(row):
                if not (self.ctx.root / path).exists() and not row.terminal:
                    out.append(Finding("missing", f"{row.id}: plan `{path}` does not exist ({self._loc(row)})"))
        return out

    def _drift(self) -> list[Finding]:
        out = []
        for row in self.rows:
            for path in self._plan_paths(row):
                file = self.ctx.root / path
                if not file.exists():
                    continue
                status = read_plan_status(file)
                if not status:
                    continue
                token, line = status
                if row.status == "done" and token in ACTIVE_PLAN:
                    out.append(Finding("drift", f"{row.id} is done but its plan still says {token} ({path}:{line})"))
                elif not row.terminal and token in TERMINAL_PLAN:
                    out.append(Finding("drift", f"plan says {token} ({path}:{line}) but row {row.id} is {row.status} ({self._loc(row)})"))
        return out

    def _resolve_card(self, kind: str, value: str) -> bool:
        if kind == "path":
            return (self.epic.dir / value).exists() or (self.ctx.root / value).exists()
        return bool(list(self.epic.dir.glob(f"{value}-*.md")) or list(self.epic.dir.glob(f"cards/{value}-*.md")))

    def _plan_paths(self, row: Row) -> list[str]:
        targets = self.epic.prompts.get(row.id, {}).get("targets", []) + row.plan_refs
        out = []
        for path in targets:
            path = re.sub(r"^\./", "", path)
            if re.search(r"(^|/)cards/", path):
                continue
            if path not in out:
                out.append(path)
        return out

    def _loc(self, row: Row) -> str:
        return f"{self.ctx.display(self.epic.board)}:{row.line}"


# --------------------------------------------------------------------------- locations

class Context:
    """Where the repo, the backlog and the plans live. Discovered once, printed on request."""

    def __init__(self, backlog_override: str | None = None):
        self.root = self._git_root()
        project = self._project_file()
        self.plans_dir = self._from_project(project, r"Plans location") or ".claude/plans/"
        backlog = backlog_override or os.environ.get("LINT_BOARD_DIR") \
            or self._from_project(project, r"Backlog\s*/\s*decomposition location") or "_backlog/"
        self.backlog = (self.root / backlog).resolve() if not os.path.isabs(backlog) else Path(backlog).resolve()

    @staticmethod
    def _git_root() -> Path:
        try:
            out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
            if out.returncode == 0 and out.stdout.strip():
                return Path(out.stdout.strip())
        except (OSError, subprocess.SubprocessError):
            pass
        return Path.cwd()

    def _project_file(self) -> str:
        for candidate in (self.root / ".claude" / "PROJECT.md", self.root / "PROJECT.md"):
            if candidate.exists():
                return candidate.read_text(encoding="utf-8", errors="ignore")
        return ""

    @staticmethod
    def _from_project(text: str, label: str) -> str | None:
        """`- **Backlog / decomposition location:** `_backlog/<epic>/` …` → `_backlog`.

        A value still carrying the template's `<placeholder>` is not a location; treat the
        profile as unfilled rather than inventing a path out of it.
        """
        m = re.search(rf"(?i)\*\*{label}[^:]*:\*\*\s*(.+)", text)
        if not m:
            return None
        value = m.group(1).strip()
        token = re.match(r"`([^`]+)`", value)
        value = token.group(1) if token else value.split()[0]
        value = re.sub(r"<[^>]*>", "", value).strip().rstrip("/")
        return value or None

    def display(self, path: Path) -> str:
        path = Path(path).resolve()
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)


def load_epic(directory: Path, ctx: Context) -> Epic | None:
    name = directory.name
    if (directory / "RUN-ORDER.md").exists():
        parser = BoardParser(directory)
        epic = Epic(name, directory, parser.path, parser.parse_rows(), parser.parse_prompts())
        epic.findings = EpicLinter(epic, ctx).run()
        return epic
    if (directory / "00-overview.md").exists():
        plans = sorted(f for f in directory.iterdir()
                       if f.is_file() and re.fullmatch(r"(?!00-)\d{2}[a-z]?-.+\.md", f.name))
        return Epic(name, directory, directory / "00-overview.md", [], {}, [],
                    [(f, read_plan_status(f)) for f in plans])
    return None


def epics(ctx: Context, only: str | None = None) -> list[Epic]:
    if not ctx.backlog.is_dir():
        return []
    out = []
    for directory in sorted(p for p in ctx.backlog.iterdir() if p.is_dir()):
        if directory.name.startswith(".") or directory.name in NON_EPIC_DIRS:
            continue
        if only and directory.name != only:
            continue
        epic = load_epic(directory, ctx)
        if epic:
            out.append(epic)
    return out


# --------------------------------------------------------------------------- reporting

def gate_note(row: Row) -> str:
    rest = re.sub(r"[*`]", "", row.deps_raw)
    rest = re.sub(r"(?:[Ww]ave\s+\d+|(?:[A-Z]{1,2})?\d+\.\d+[a-z]?|(?<![\w.])[A-Z]{1,2}\d+(?![\w.])|[–+,&—-]|\band\b)", " ", rest)
    rest = re.sub(r"\s+", " ", rest).strip()
    return f" (gated: {rest})" if rest else ""


def status_line(epic: Epic, ctx: Context) -> str:
    if epic.plans is not None:
        tokens = [status[0] if status else None for _, status in epic.plans]
        done = sum(1 for t in tokens if t in TERMINAL_PLAN)
        unread = [f.name for f, status in epic.plans if status is None]
        line = f"{epic.name}: {done}/{len(epic.plans)} subtasks terminal (overview epic — deps/Owns not machine-read)"
        return line + (f" · no status line: {', '.join(unread)}" if unread else "")

    rows = [r for r in epic.rows if not r.operator]
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    linter = EpicLinter(epic, ctx)
    by_id = {r.id: r for r in epic.rows}
    ready = [r for r in rows if r.status == "open"
             and all(by_id.get(dep) is not None and by_id[dep].terminal for dep in linter.deps[r.id])]
    operator_open = [r for r in epic.rows if r.operator and not r.terminal]
    parts = [f"{counts.get('done', 0) + counts.get('skipped', 0)}/{len(rows)} done"]
    if counts.get("in_progress"):
        parts.append(f"{counts['in_progress']} in progress")
    if counts.get("blocked"):
        parts.append(f"{counts['blocked']} blocked")
    if ready:
        parts.append("can start: " + ", ".join(r.id + gate_note(r) for r in ready))
    if operator_open:
        parts.append("operator open: " + ", ".join(r.id for r in operator_open))
    if epic.findings:
        parts.append(f"⚠ {len(epic.findings)} lint")
    return f"{epic.name}: {' · '.join(parts)}"


def lint_report(epic: Epic, ctx: Context) -> list[str]:
    if epic.plans is not None:
        return [status_line(epic, ctx)]
    header = f"{epic.name} ({ctx.display(epic.board)}: {len(epic.rows)} rows, {len(epic.prompts)} prompts)"
    if not epic.findings:
        return [header, "  ✓ clean"]
    return [header] + [f"  ✗ {f.kind.ljust(7)} {f.message}" for f in epic.findings]


def finished(epic: Epic) -> bool:
    if epic.plans is not None:
        return all((status[0] if status else None) in TERMINAL_PLAN for _, status in epic.plans)
    return all(r.terminal for r in epic.rows) and not epic.findings


def epics_for_file(file_path: str, ctx: Context) -> list[Epic]:
    """Which epics an edited file could have invalidated — the board's own tree, or a plan it cites."""
    try:
        relative = Path(file_path).resolve().relative_to(ctx.root)
    except (ValueError, OSError):
        return []
    rel = str(relative)
    backlog_rel = ctx.display(ctx.backlog)
    if rel.startswith(backlog_rel + "/"):
        parts = rel.split("/")
        return epics(ctx, only=parts[1]) if len(parts) > 1 else []
    if not rel.startswith(ctx.plans_dir.rstrip("/") + "/"):
        return []
    return [e for e in epics(ctx)
            if e.board.read_text(encoding="utf-8", errors="ignore").find(rel) != -1]


# --------------------------------------------------------------------------- CLI

def main(argv: list[str]) -> int:
    args = list(argv)
    command = "status"
    if args and not args[0].startswith("-"):
        command = args.pop(0)
    if command in ("help", "-h", "--help") or "--help" in args or "-h" in args:
        print(HELP)
        return 0

    def flag(name: str) -> bool:
        if name in args:
            args.remove(name)
            return True
        return False

    oneline, quiet, strict = flag("--oneline"), flag("--quiet"), flag("--strict")
    only = directory = None
    for name, setter in (("--epic", "epic"), ("--dir", "dir")):
        if name in args:
            i = args.index(name)
            value = args[i + 1] if i + 1 < len(args) else None
            del args[i:i + 2]
            if setter == "epic":
                only = value
            else:
                directory = value

    ctx = Context(directory)

    if command == "status":
        found = epics(ctx, only)
        if oneline:
            found = [e for e in found if not finished(e)]
        if not found and not oneline:
            print(f"No epics under {ctx.display(ctx.backlog)}/")
        for epic in found:
            print(status_line(epic, ctx))
        return 0

    if command == "lint":
        found = epics(ctx, only)
        if not found and not quiet:
            print(f"No epics under {ctx.display(ctx.backlog)}/")
        for epic in found:
            if quiet and not epic.findings:
                continue
            print("\n".join(lint_report(epic, ctx)))
        return 1 if strict and any(e.findings for e in found) else 0

    if command == "hook":
        try:
            payload = json.loads(sys.stdin.read())
            file_path = str(payload.get("tool_input", {}).get("file_path") or "")
        except (ValueError, AttributeError):
            return 0
        if not file_path:
            return 0
        report: list[str] = []
        for epic in epics_for_file(file_path, ctx):
            if epic.findings:
                report.extend(lint_report(epic, ctx))
        if not report:
            return 0
        context = ("lint-board after this edit (report-only — fix only what your row owns, flag the rest):\n"
                   + "\n".join(report))
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}))
        return 0

    print(HELP, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
