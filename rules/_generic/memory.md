---
description: >-
  On-demand memory reference — the kit's statement of the auto-memory contract (one fact per
  file, indexed, update-don't-duplicate, delete-when-wrong) and the inventory of agents that
  carry `memory: project`. The main session's contract is carried by the harness when
  auto-memory is on; each memory-bearing agent carries its own stance inline. Loaded when
  authoring agents or working with memory.
paths:
  - ".claude/agents/**"
---

# Memory discipline — reference (generic)

When auto-memory is on, the **harness already injects the contract** (the `MEMORY.md` index +
one-fact-per-file topic files, with the `user` / `feedback` / `project` / `reference` types)
into the main session every turn — so it is no longer restated always-on here. This file is the
kit's canonical statement of that contract (for reference, and for when auto-memory is off) plus
the roster of agents that persist across sessions.

## The contract

- **One fact per file**, with frontmatter: a kebab-case `name`, a one-line `description` (used
  to decide relevance at recall time), and `metadata.type` — `user` (who the user is),
  `feedback` (guidance on how to work — corrections and confirmed approaches, with *why* and
  *how to apply*), `project` (ongoing work/goals/constraints not derivable from code or git;
  convert relative dates to absolute), or `reference` (external URLs/dashboards/tickets).
- **Index every memory** with one line in `MEMORY.md` (`- [Title](file.md) — hook`); the index
  loads each session, never memory *content*. Link related memories with `[[name]]`.
- **Update, don't duplicate; delete when wrong.** Amend an existing file rather than adding a
  second that will drift; a memory contradicted by current reality is deleted the moment the
  contradiction is observed.
- **Never store what the repo already records** (code structure, past fixes, git history,
  anything in `CLAUDE.md` / `PROJECT.md` / `CONTEXT.md` / ADRs / archived plans), nor what only
  matters to the current conversation.
- **Recalled ≠ true now.** A recalled memory reflects when it was written — verify a named file,
  flag, or command still exists before acting (`core.md` → recalled is inferred).

## Gates on what gets written

The contract above says what a memory looks like; these three say whether it should exist at
all. Each entry is individually defensible and the aggregate is unbounded — and an agent's
store is written by an executor the user never watches deliberate.

- **The write bar.** Record only a pattern seen **at least twice, in different sessions**, that
  would not be re-derived from the code in a minute. A one-off observation about the file you
  just audited belongs in the audit report, not in memory. A first sighting that you expect to
  recur may be filed as an explicit `(1×)` candidate — and is **deleted at the next prune if it
  never did**. The counter below is what makes that promise enforceable; without it the bar is
  unmeasurable and every entry looks equally earned.
- **Announce writes.** An agent that wrote to memory says so in its report — the filename and
  one line of why — so the user can object *before* the entry is committed rather than after.
- **Prune on read.** When loading `MEMORY.md`, treat an entry whose cited referent no longer
  exists as stale: drop it and say so. Memory that outlives its referent is worse than no memory —
  it is a confident wrong fact from a trusted source.
  Cite the referent as `file.py::symbol`, not `file.py:214` (see `code.md` § Greppability): a
  memory is durable text, and a line number gives a **false** staleness signal every time an edit
  above it shifts the file, while a vanished *symbol* is a true one. Prune on the symbol; a moved
  line proves nothing either way.

## Shape of a store that stays useful past a hundred entries

The contract above keeps each entry honest; these four keep the *store* readable. They come from one project's agent memory measured at 287 entries, where the practice existed and was never written down — so it never travelled, and three lessons at ≥12× occurrences had still not become a rule.

- **Three fixed sections in `MEMORY.md`, in this order:** `## Recurring — check first` · `## Sanctioned — do not re-flag` · `## Method lessons`. The first is what a new run reads before starting; the second is what stops it re-reporting a blessed pattern for the fourth time; the third is about how the *work* goes wrong, not the code. A flat index of 200 lines gets skimmed, and skimming defeats the purpose of having it.
- **An occurrence counter in the index line, and one dated line per occurrence in the file:** `- [rule rewrite leaves a twin docstring](rule-rewrite-twin-docstring.md) (43×) — grep the rule as prose, not the symbol`. The count is the only thing that turns a pile of equally-worded entries into a priority order, and it is what `/retro` promotes on.
- **A size cap per entry:** the rule, **Why**, **How to apply**, and the **last ~3 occurrences** with dates and citations. Older occurrences fold into the counter — they have already made their point, and an entry that grows without bound is one nobody finishes reading.
- **Prune against the counter, not only against the referent.** At prune time a `(1×)` candidate older than a couple of months is deleted; a `(≥3×)` entry that has not been promoted to a rule, agent line or skill step is a **`/retro` input**, not a memory to keep re-reading. Memory is the waiting room, not the destination.

## Agents that carry `memory: project`

`code-reviewer`, `security-reviewer`, `docs-writer`, `finding-verifier`, `quality-auditor`. Each
follows this contract and carries its own stance **inline in its agent file** — e.g.
`finding-verifier` remembers REFUTED/STALE findings (never CONFIRMED); `quality-auditor` remembers
recurring debt patterns and once-flagged-but-sanctioned patterns (never per-file verdicts). An
agent memory nobody prunes is where false facts become permanent — the delete-when-wrong rule
binds agents most.
