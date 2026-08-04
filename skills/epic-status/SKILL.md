---
name: epic-status
description: >-
  Read-only progress dashboard over a wave-structured decomposition (one epic =
  one <backlog>/<task-name>/ directory from /prepare Phase 6): which subtasks are
  done/in-progress/blocked, which wave is current, the next safe wave to launch
  (all Deps merged, Owns pairwise disjoint), what can launch in parallel right now, and
  whether running parallel sessions collide on ownership. Where a parent RUN-ORDER exists
  it is read as the execution truth and reported against plan frontmatter as drift.
  Reports and recommends — never edits, commits, or launches.
  TRIGGER when: "where is this epic", "what's the next wave", "can I start these in
  parallel", "epic status", or before launching concurrent /implement sessions.
  TRIGGER ALSO on the same question phrased as plain work, with this skill unnamed — "how far
  along is <backlog>/<name>", "what's left in this epic", "which of these are safe to run at
  once", "did wave N land", "is this finished", "check if the epic is done? <backlog>/<name>".
  Those last two are cheap status questions and land HERE, not in /close-epic: answering them is
  a read of what is on disk, not an end-to-end verification contract. Only escalate to
  /close-epic when the ask is to verify and archive ("run the verification steps from the
  overview", "can this be archived").
  DO NOT TRIGGER when: grooming single issues (use /triage), creating the
  decomposition (use /prepare), or snapshotting one session's live state (use /handoff).
allowed-tools: Read, Grep, Glob, Bash
effort: medium
---

# Epic Status: $ARGUMENTS

A **strictly read-only** dashboard over one epic — a `<backlog>/<task-name>/` directory produced by
`/prepare` Phase 6 (see `skills/prepare/reference/parallel-wave-execution.md` for the wave model this
skill reads). It answers: where does the epic stand, which wave is current, what is the **next safe
wave**, and do any running sessions **collide on ownership**. It changes nothing: statuses are
stamped by `/implement` and reconciled by the user; this skill only reports and recommends.

This skill carries only invariant logic. The backlog location and commands come from
`.claude/PROJECT.md`. `Bash` is for read-only inspection (`git log`, `git status`, `ls`) — never
mutation.

## Phase 0 — Load profile & resolve the epic

1. Read `.claude/PROJECT.md`. If missing or `profile_status: TEMPLATE`, fall back to the root
   `CLAUDE.md` (always in context) when it carries the backlog location and commands — note you're
   running without a kit profile — and only **STOP** → run `/bootstrap` first if *neither* has them.
   Resolve **Plans / backlog location** (and the **Archive on done** location, if any).
2. `$ARGUMENTS` names the epic — a directory under the backlog location, or its name. If empty,
   glob the backlog location for directories containing a `00-overview.md`, list them, and **ask**
   which epic to report on. Do not guess.
3. **Parent RUN-ORDER — look, never require.** Walk up from the epic directory toward the program
   directory for a `RUN-ORDER.md` (the artifact is described in
   `skills/prepare/reference/parallel-wave-execution.md`). **Found** → it is the execution truth for
   ordering and parallel-safety; Phase 2 reconciles it against plan frontmatter. **Not found** →
   report exactly as before and say nothing about it. Absence is the normal case for a standalone
   epic, not a gap — and this skill never creates one.

## Phase 1 — Gather evidence (read everything, assume nothing)

Status comes **only from what is on disk** — never from memory of past sessions. Checklist:

- [ ] `00-overview.md` — summary, subtask table, dependency graph, **wave schedule**, and
      **file-ownership matrix** (Owns / Reads / Shared edits per task).
- [ ] Every `NN-<subtask>.md` — the header line (`Wave` · `Owns` · `Reads` · `Deps` ·
      `Shared edits` · `Solo`), the `status` frontmatter if `/implement` stamped one
      (`DONE | PARTIAL | BLOCKED`, `completed_at`, `notes`), and any appended
      `## Implementation Log` sections.
- [ ] The archive location — a subtask file moved there counts as done.
- [ ] `implementation-prompts.md` — the per-session `/implement` briefs, grouped by wave.
- [ ] The parent `RUN-ORDER.md`, **if Phase 0 found one** — this epic's row(s): Mode, Model, `∥`
      marks, `Owns`, the Status cell, any inline cross-row collision note, and the Follow-ups
      section. Status cells carry what the plans do not: commit SHAs, E2E counts, measured deltas,
      re-pricings, and what spun out.
- [ ] `git status --short` and `git log --oneline -15 -- <owned files>` — uncommitted or recent
      activity on a subtask's `Owns` files signals an in-progress or freshly merged session.

Derive each subtask's status from this evidence, cited as `path:line`:

| Evidence | Status |
|----------|--------|
| Frontmatter `status: DONE` / `PARTIAL`, or file archived | **done** (PARTIAL: note the deviations) |
| Frontmatter `status: BLOCKED` | **blocked** — quote the `notes` |
| Implementation Log present but no final status, or uncommitted working-tree changes on its `Owns` files | **in-progress** |
| None of the above | **not started** |

If the evidence conflicts (e.g. log says done, no status stamped), report the drift verbatim and
propose the exact fix — **do not apply it**.

## Phase 2 — Wave math

1. **Current wave** — the earliest wave in the schedule with any subtask not yet done.
2. **Deps landed?** — per pending subtask, every `Deps` entry must be done **and merged**
   (committed — verify via `git log`; uncommitted done-work does not count as landed).
3. **Next safe wave** — the earliest wave whose subtasks are all not-started, all Deps landed, and —
   **re-verified from the `Owns` declarations, not trusted from the schedule** — pairwise-disjoint
   on `Owns` with ≤1 editor per `Shared edits` file. Honor `(solo)` waves: a solo subtask runs
   alone, never alongside siblings.
4. **Collision check** — for everything currently **in-progress** (plus anything you're about to
   recommend): verify all `Owns` sets are pairwise disjoint and no shared file has two editors. Two
   in-progress subtasks sharing an `Owns` file is a **COLLISION — flag it loudly**, name both
   subtasks and the file, and recommend pausing one. Never recommend a launch into a collision.
5. **RUN-ORDER reconciliation** (only when Phase 0 found one). The RUN-ORDER is the execution truth;
   plan frontmatter is what the sessions actually stamped. Report the **drift between them**, each
   side cited:
   - a row marked done whose plan carries no terminal status, or the reverse;
   - a row whose Mode/Model/wave position the plans contradict;
   - a Follow-ups row with no card file behind it, or a card with no row.

   Propose the exact edit for each drift item — **never apply it**, and never write into
   `RUN-ORDER.md`: it is a serialization point with exactly one writer.
6. **What can launch in parallel right now.** Answer from the RUN-ORDER's `∥` marks **and** the
   `Owns` sets when a RUN-ORDER exists — not from the dependency DAG alone; the `∥` marks encode
   cross-card facts the DAG cannot see, and inline notes ("F2.7 and F2.8 both edit `<file>` — run
   them in order") override a `∥` mark. Re-verify disjointness yourself before recommending;
   a `∥` mark that the current `Owns` sets contradict is drift, and drift loses to evidence.

## Phase 3 — Report (fixed contract)

```
## Epic: <task-name> — <N> subtasks · <done> done · <in-progress> in-progress · <blocked> blocked · <left> not started

| Wave | Subtask | Status | Owns | Deps met? |
|------|---------|--------|------|-----------|
| W1   | 01 — <name> | done (00-overview.md:12, 01-<name>.md:3) | <files> | — |
| W2   | 03 — <name> | in-progress (git: uncommitted) | <files> | yes (01 merged) |

### Current wave: W<k> — <what's still open in it>
### Collision check: OK — in-progress Owns pairwise disjoint
   (or) ⚠️ **COLLISION**: 03 and 04 both own `<file>` (03-<name>.md:2 · 04-<name>.md:2) — pause one.
### Next safe wave: W<k+1> — SAFE / NOT SAFE (<unmet dep / collision / blocked upstream>)
Launch when ready (briefs in implementation-prompts.md, "Wave W<k+1>" section):
- Session 05: /implement <backlog>/<task>/05-<name>.md   (solo: no · owns <files>)
### Blockers / drift
- 06 BLOCKED — <notes> (06-<name>.md:4)
- Drift: 02 has an Implementation Log but no status stamp — suggest `status: DONE` (user applies).
```

**Only when a parent RUN-ORDER exists**, add these two sections — omit them entirely otherwise
(no "no RUN-ORDER found" line):

```
### RUN-ORDER: <path> — rows for this epic
| # | Row | Mode | Model | ∥ | RUN-ORDER says | Plans say |
|---|-----|------|-------|---|----------------|-----------|
| 2.3 | 05-<name> | I | default | ∥ | done (RUN-ORDER.md:41) | no status stamp (05-<name>.md:2) — **drift** |
### Parallel-safe right now: 05 ∥ 07  (∥ marks + Owns re-verified disjoint)
   (or) 05 only — 07's ∥ mark contradicts its Owns (`<file>` shared with 05); RUN-ORDER row is stale.
```

Every claim in the report must be citable to a file and line (or a git command's output).

## Hard rules

- **Strictly read-only.** Never edit a `status` field, never write or archive files, never run
  `git add`/`commit`, never launch sessions. You *recommend*; the user launches and `/triage`/
  `/implement` own the state changes. **A RUN-ORDER is never written or created here** — drift is
  reported with the exact proposed edit; the operator applies it.
- **Evidence only.** Every status comes from frontmatter, logs, `00-overview.md`, or git output on
  disk — never from conversational memory. Unknown is reported as unknown.
- **Collisions are loud.** A shared `Owns` file between in-progress subtasks is a headline finding,
  not a footnote — and disqualifies any wave recommendation that worsens it.
- **Re-verify, don't trust.** The next-wave verdict is recomputed from the `Owns`/`Deps`
  declarations, not read off the wave schedule table — or off a RUN-ORDER `∥` mark, which is a
  claim about ownership, not proof of it.
- **Facts from PROJECT.md.** Backlog and archive locations come from the profile — never hardcoded.

## See also

- **`/prepare`** — creates the wave-structured decomposition this skill reads (and its
  `reference/parallel-wave-execution.md`, the canonical layout).
- **`/implement`** — runs one subtask session; stamps `status` and appends the Implementation Log.
- **`/triage`** — grooming of single backlog issues (not epics).
- **`/handoff`** — snapshot of one session's live state (not the whole epic).
- **`/close-epic`** — the terminal counterpart. Escalate here only when the ask is to *verify and
  archive*; "is the epic done?" is answered by this skill.
