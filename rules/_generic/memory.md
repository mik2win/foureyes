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
  just audited belongs in the audit report, not in memory.
- **Announce writes.** An agent that wrote to memory says so in its report — the filename and
  one line of why — so the user can object *before* the entry is committed rather than after.
- **Prune on read.** When loading `MEMORY.md`, treat entries whose cited `path:line` no longer
  exists as stale: drop them and say so. Memory that outlives its referent is worse than no
  memory — it is a confident wrong fact from a trusted source.

## Agents that carry `memory: project`

`code-reviewer`, `security-reviewer`, `docs-writer`, `finding-verifier`, `quality-auditor`. Each
follows this contract and carries its own stance **inline in its agent file** — e.g.
`finding-verifier` remembers REFUTED/STALE findings (never CONFIRMED); `quality-auditor` remembers
recurring debt patterns and once-flagged-but-sanctioned patterns (never per-file verdicts). An
agent memory nobody prunes is where false facts become permanent — the delete-when-wrong rule
binds agents most.
