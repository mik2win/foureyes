# Parallel-Wave Decomposition & Execution

Companion to `/prepare` Phase 6 — loaded only when a task is **Complex** (Phase 3 tier).
Simple/Medium tasks never read this file. All commands, paths, and layer names come from
`PROJECT.md` — never hardcode them.

**Applies to:**
- `/prepare` Phase 6 decomposition — the saved plan must be wave-structured.
- Any time 2+ plans run concurrently via `/implement` — each session honors its ownership brief.

Legend: `→` must wait (file/data dependency) · `∥` concurrent-safe (disjoint files) · `⚠` shared-file conflict.

## Core model — waves over a dependency DAG

- A **wave** is a set of subtasks runnable concurrently, each in its own implementation session.
- **Disjoint-ownership invariant**: within one wave, every subtask's `Owns` file-set is pairwise
  disjoint from the others. No two concurrent sessions ever write the same file — this is the whole
  safety guarantee.
- **The hard boundary is _concurrency_, not ownership.** The only thing that corrupts parallel work
  is two **concurrent** sessions writing the same file. Files owned by an already-merged prior wave,
  a not-yet-started future wave, or no subtask at all carry no concurrency risk — editing them is a
  *scope* question, not a *safety* one (see "When a fix lands outside `Owns`").
- **Deps-landed invariant**: a subtask's `Deps` must be merged before its wave starts. Waves are the
  topological layers of the dependency DAG. Re-layer until both invariants hold.

## Solo tasks (run alone)

Some subtasks cannot share a wave and must run **solo** — one session, no concurrent siblings:
- **Hot-file hubs** — wiring/integration edits touching an entrypoint + a registry + shared types.
- **Broad refactors** — blast radius spans many modules; ownership can't be carved cleanly.
- **Gated finals** — run only if an upstream gate/decision says so.

Mark them explicitly: give the task its own single-task wave, annotate that wave `(solo)`, and set
`Solo: YES — <reason>` at the top of its brief. Every other task defaults to `Solo: no`.

## Sizing per subtask

Defined once in `/prepare` Phase 6.1 — independently committable, reviewable in one sitting,
disjoint `Owns`, and projected under ~200k of session context. Not restated here.

## File ownership — the conflict key

| Field | Meaning | Conflict? |
|-------|---------|-----------|
| `Owns` | Files it exclusively creates/edits | **Yes** — never shared within a wave |
| `Reads` | Files read for context, never modified | No — freely shared |
| `Shared edits` | Registry/config/doc files it must append to | Serialized — ≤1 editor per wave per file |

Tasks may share `Reads`; they may **never** share `Owns`.

## Shared / hot files (serialization points)

Files many subtasks naturally want at once — route them carefully:
- **Wiring / registries** — the app entrypoint/CLI, a plugin or route registry, DI wiring.
- **Cross-cutting types / config** — shared type modules, a central config object.
- **Docs** — `CONTEXT.md`, `.claude/rules/*`, the task's own `00-overview.md`.

**Rule**: at most **one** task per wave may edit a given shared file. If several need it, serialize
them into different waves, or route all edits into a single dedicated "wiring/integration" subtask
that runs in its own wave after the feature tasks land.

## Isolation — same-dir parallel sessions (default)

For file-disjoint waves, run each subtask as a **separate session in the same repo directory on one
branch**. Do **not** use git worktrees by default: same-dir sessions share skills, rules, and the
permission allowlist — worktrees lose all of that. Use worktrees only when two tasks genuinely must
edit the same file and you want filesystem isolation (prefer serializing into different waves).

## Tests during a wave

- **In-wave**: each session runs **only** the targeted tests for its `Owns` modules
  (`PROJECT.md` → Commands `test:targeted`). Do **not** run the full suite mid-wave — N parallel
  full suites race on artifacts and drown the signal.
- **After the wave merges**: run the full `test` command from `PROJECT.md` **once** as the
  integration/regression pass.

## When a necessary fix lands outside `Owns`

An audit finding, a failing test, or a missed dependency may demand a change to a file **not in your
`Owns`**. A blanket "never touch anything else" forces a hack; classify the file first — only
**concurrent** collisions are a hard stop (the user reviews every diff before committing, so a
minimal, recorded fix to a non-concurrent file is safe):

| Class | The file is… | Action |
|-------|--------------|--------|
| **Shared-edit (mine)** | in **my own** `Shared edits` | Append-only edit as declared; log it. |
| **Concurrent-sibling** | in the `Owns`/`Shared edits` of a session running **now** in my wave | **HARD STOP — never edit.** Record under Cross-Session Findings; a sibling/follow-up fixes it. |
| **Serialization-point** | a hot/shared file (entrypoint, registry, shared types/config, `CONTEXT.md`, `.claude/rules/*`) — even if currently unowned | **STOP & flag.** Another wave may touch it; route into a dedicated wiring subtask. |
| **Sequenced** | owned by a prior (merged) or later (not-started) subtask | Default **flag** for the owner. Edit only if a true blocker AND the fix is small and clearly belongs here → log as a scope deviation noting the overlap. |
| **Unowned** | claimed by no subtask, and not a serialization-point | **Minimal fix allowed** — scoped to the defect, logged, reported. |

**Solo / single-session wave**: the Concurrent-sibling row is vacuous → **widest latitude** (apply
Sequenced / Unowned / Serialization-point rows directly); still flag future-wave & serialization-
point files, and log every out-of-`Owns` edit. Every flagged item and applied fix must surface in
the session's final report — silent scope creep defeats the point.

## RUN-ORDER — the execution spine above the plans (conditional)

A **RUN-ORDER** is a *program*-level artifact: one row per plan or card, carrying execution order,
parallel-safety, and what the work discovered. It sits **above** `00-overview.md` — an overview
indexes one epic's subtasks; a RUN-ORDER sequences several epics or cards and stays alive while
they run, absorbing what implementation finds.

**Conditional, never mandatory.** Where one exists it is the execution truth and every skill defers
to it. Where none exists, no skill creates one as a side effect and none complains about its
absence — a standalone epic without one is the normal case, not a gap. Detection is mechanical:
walk up from the plan path toward the program directory looking for `RUN-ORDER.md`; found → read it
and honor this plan's row; not found → proceed exactly as without it, and say nothing about it.

**It earns its keep at 4+ plans, or when one card-set spans several epics.** A two-subtask
single-wave epic gets an overview and nothing more.

**Authorship belongs to the program tier**, not to `/prepare`. `/prepare` and `/implement` *read*
it and *propose* rows; the operator (or the program pass) writes them. A wave session never edits
it mid-wave — it is a serialization point with exactly one writer at a time.

```markdown
# RUN-ORDER — <program name>

Legend: **P** = run `/prepare` first · **I** = the card is the spec, implement straight ·
`∥` = file-disjoint with its wave siblings, safe to launch as parallel sessions.

## Wave 1 — <what this wave establishes>

| # | Card / plan | Mode | Model | Owns | Status |
|---|-------------|------|-------|------|--------|
| 1.1 ∥ | `<backlog>/<card>/plan.md` — <one line> | I | default | `<files>` | |
| 1.2 | `<backlog>/<epic>/00-overview.md` — <one line> | P → I | strongest | `<files>` | |

## Follow-ups — wave N (from the <cards> close-out, <date>)

| # | Card | Mode | Why here |
|---|------|------|----------|
| F2.1 | <card> | P → I | <what was discovered, and why it sits at this position> |
```

Per-row fields:

- **Mode** — `P` (needs a `/prepare` pass first) or `I` (the card already *is* the spec).
- **Model** — the hint from Phase 6.2's rule, recorded so a parallel launcher doesn't re-derive it.
- **`∥`** — the row's `Owns` set is disjoint from its wave siblings'. Same disjointness test as the
  wave-safety check below, one tier up. Collisions a `∥` mark can't express are written inline
  ("F2.7 and F2.8 both edit `<file>` — run them in order, or merge them").
- **Status** — filled as rows land: commit SHA, E2E counts, measured deltas, re-pricings, and
  **what spun out**. This is the only place an epic's real cost stays visible, and it is what
  `/retro` and `/revisit` read.

A **Follow-ups** section is not a parking lot. A row carries a **position** and a one-line
**"why here"**, or it does not get filed — otherwise "file a card" becomes a way to defer real work
indefinitely.

## E2E-verify block (written into `00-overview.md` at prepare time)

Governed by `/prepare` Phase 6.4; executed by `/close-epic`, which appends
`## E2E results — <date>` beneath it.

```markdown
## E2E verify — <epic>   (written at prepare time; executed at close)

Surfaces touched: <the surfaces from PROJECT.md → Architecture this epic actually changes>
Drive method:     <per surface, the command from PROJECT.md → Commands — browser drive, live-server
                   request, remote probe, CLI invocation, direct store query>
Baseline:         <the pre-change measurement this epic must beat: the value, the command that took
                   it, the machine, the date>

| # | Check | How to drive | Expected | Blocking? |
|---|-------|--------------|----------|-----------|
| 1 | <a claim this epic makes, stated observably> | <exact command / driver> | <value or state> | yes |
| 2 | <a denominator that must reconcile> | <exact command> | <== exactly> | yes |
| 3 | <a nice-to-have> | | | no |
```

## Backlog file layout (paths relative to `PROJECT.md` → Plans / backlog)

```
<backlog>/<task-name>/
├── 00-overview.md            # summary, dependency graph, wave schedule, ownership matrix
├── 01-<subtask>.md           # atomic task
├── 02-<subtask>.md           # depends on 01
├── ...
└── implementation-prompts.md # ready-to-use per-session /implement briefs, by wave
```

**`00-overview.md`**: 1–2 paragraph summary; subtask table (#, name, est. size, deps, test type);
dependency graph (ASCII); the **wave schedule** and **file-ownership matrix** tables below; and the
**E2E-verify block** above. It is written **only** when there are ≥2 subtask files to index — a
single-session plan is saved as `plan.md` (or `NN-<slug>.md` from a card), never under this name
(`/prepare` Phase 6.3).

**`NN-<subtask>.md`**:
```
# NN — <Title>
Wave: W1 | Owns: <files> | Reads: <files> | Deps: NN-x or None | Shared edits: <files or none> | Solo: no

## Problem        — what this subtask addresses
## Changes        — [ ] `path`: SPECIFIC change (function/line range + exact modification)
## Notes          — patterns to follow, pitfalls
## Quality        — checklist drawn from the applicable installed rules (Phase 5.3)
## Verification   — exact command from PROJECT.md → Commands, or manual steps
```

## Templates

**Per-session brief** (in `implementation-prompts.md`, one per session, grouped under its wave):
```
### Wave W1 · Session 01 — <title>
/implement <backlog>/<task>/01-<name>.md

Solo:                  no   (or: YES — run alone; reason: <why>)
OWN (edit only these): <files>
READ-ONLY (context):   <files>
DO NOT TOUCH:          <file> [02 · concurrent] · <file> [05 · future] · <file> [01 · merged]
Out-of-OWN fix?        concurrent-sibling or hot/shared file → STOP + flag (Cross-Session Findings);
                       sequenced/unowned (esp. if solo) → minimal fix + log. See this file.
Siblings this wave:    02 (owns <file>) · 04 (owns <config>)
Tests:                 <test:targeted from PROJECT.md — only this>
Commit:                none mid-wave — the coordinator combines the wave (`/implement` rule);
                       the user commits after the wave merges.
```
Annotate every `DO NOT TOUCH` file `[<NN> · concurrent|future|merged]` so the session knows which
are hard (concurrent) vs sequenced (flag-or-blocker-only).

**Wave schedule** (in `00-overview.md`):
```
| Wave | Run concurrently | Each waits for | Shared-file owner |
|------|------------------|----------------|-------------------|
| W1   | 01 ∥ 02 ∥ 04      | —              | 04 → <config file> |
| W2   | 05 ∥ 03           | 05→01 · 03→02  | —                 |
| W3 (solo) | 06 — run alone | 06→05         | 06 = wiring hub: <entrypoint> + registry |
```

**File-ownership matrix** (in `00-overview.md`):
```
| Task | Owns | Reads | Shared edits |
|------|------|-------|--------------|
| 01 | <files> | <files> | — |
| 04 | (config block) | — | <config file> |
```

**Recommended model / effort** — annotate every wave and session heading with a
`rec: <model>/<effort>` suffix. Advisory only: the operator picks the actual model at launch.
Score **complexity** on this table, then apply the **risk overlay** from `/prepare` Phase 6.2 —
a subtask that is irreversible, touches a server-side or live path, writes schema or persisted
state, or carries a wide blast radius gets the strongest model *even when the change looks
mechanical*. Model names come from what is actually available at launch time; the tiers are what
matter:

```
| Tier · effort            | Fits |
|--------------------------|------|
| strongest · high/xhigh   | Novel deep-module design; solo/hub integration waves; cross-cutting
|                          | rewrites; contract-defining work later waves code against; ambiguous specs |
| default · medium/high    | Careful surgery in existing central files; moderately complex
|                          | features with a detailed spec |
| cheapest · low/medium    | Mechanical / mirror / pattern-copy tasks; small additive endpoints;
|                          | styling; fully-specified small modules |
```

**`00-overview.md` skeleton** (the wave-schedule and ownership-matrix cells use the tables
above; the E2E-verify block is the one earlier in this file):
```markdown
# <Task name> — Overview

**Created**: <date> | **Subtasks**: N | **Status**: ready for implementation
**Context budget**: each subtask projected under ~200k of session context

## Summary
<1–2 paragraphs>

## Reviews & decisions — READ FIRST
<!-- Artifact-Continuity Contract (rules/_generic/planning-artifacts.md): index every
     spike/grill/review/audit report bearing on this epic, so /implement opens them before
     touching code. One row per report; keep current as findings fold back into subtasks. -->
| Report | Verdict (1 line) | Affects subtask(s) |
|--------|------------------|--------------------|
| _(none yet)_ | | |

## Subtask overview
| # | Subtask | Est. context | Deps | Tests |
|---|---------|--------------|------|-------|

## Dependency graph
<ASCII — notation below>

## Wave schedule
<table above; each row carries its model hint>

## File-ownership matrix
<table above>

## E2E verify — <epic>
<the block earlier in this file: surfaces, drive method, baseline, check table>

## Start implementation
See `implementation-prompts.md` for ready-to-use session prompts.
```

**`implementation-prompts.md` skeleton** — always written when there are ≥2 subtasks. Organize
**by wave**; each entry is the per-session brief above, with the test-approach suffix appended:
```markdown
# Implementation prompts — <task name>

**Workflow:** `/implement <plan>` → `/test-spec <module>` (pure logic only)

## Execution order
<sequential / parallel diagram — notation below>

## Wave W1
<one per-session brief per subtask>

## Wave W2
...

## Quick validation
<post-implementation smoke checks>
```

Test-approach suffix per subtask, by what the code *is*:

| Code type | Test approach | Prompt suffix |
|-----------|---------------|---------------|
| Pure logic (calculators, detectors, filters, mappers) | Unit tests | `Tests: /test-spec <module> — <what to test>` |
| Integration (wiring, handlers, persistence) | Manual | `No unit tests — integration. Manual: <steps>` |
| Config / schema change | Manual | `No unit tests. Manual: <how to observe the new state>` |

**Parallel-execution notation** — one legend used by every diagram and table here:
```
Sequential:   01 → 02 → 03
Parallel:     01 → [02 ∥ 03] → 04            ∥ = file-disjoint, safe to run at once
Fork-join:    01 ─┬─> 02 ─┬─> 04
                  └─> 03 ─┘
Solo wave:    🧱 06                           🧱 = runs alone, no concurrent siblings
Conflict:     ⚠ 07 & 08 both edit <file>      ⚠ = shared-file collision, must be serialized
```
A `⚠` in a saved decomposition is a bug, not an annotation — it means the wave-safety check
below has not been satisfied yet.

## Wave-safety check (MANDATORY before saving)

Verify that within **each** wave all `Owns` sets are pairwise disjoint and every shared file has ≤1
editor. If not, re-layer the waves. Only then offer to save.

If re-layering cannot terminate — some subtask never becomes eligible because its `Deps` chain
leads back to itself — the graph has a **cycle**. Stop and put it to the user; never break an edge
heuristically to make the layers come out. `Deps` are authored, so a cycle is a decomposition bug
with a real answer (usually two subtasks that should be one, or a dependency pointing the wrong
way), and guessing which edge to cut silently ships the wrong split.

## Save & commit flow

1. Present the decomposition and ask **`Save to <backlog>/<task-name>/?`** — **confirm before
   creating any files**.
2. On confirmation, write `00-overview.md`, one `NN-<subtask>.md` per subtask, and
   `implementation-prompts.md`. Full sessions (not subagents/worktrees) load the project's complete
   `.claude/` — keep that in mind for briefs meant for parallel runs.
3. If plan files were written AND plans are a **committed** category (`PROJECT.md` → Artifact git
   policy), **offer** a copy-paste `git add <explicit paths> && git commit` block for those files —
   **suggest-only TEXT the user runs**; never execute; explicit paths only (never `-A` / `.` /
   `<dir>`). If plans are local/gitignored, skip.

## Tracking progress

Between waves, `/epic-status <backlog>/<task-name>` reads the overview + subtask statuses and
reports: what's done, the next safe wave (all `Deps` merged, `Owns` pairwise disjoint), and any
ownership collision among in-progress sessions.

## /implement — parallel-session awareness

When a plan declares `Wave` / `Owns`: read `Owns`/`Reads`/`Shared edits` first and restrict edits to
`Owns` + append-only `Shared edits`; classify any needed out-of-`Owns` change via the table above
(concurrent-sibling / serialization-point → STOP & flag); run targeted tests only; do **not**
emit a commit command mid-wave — the coordinator combines the wave; note "Part of Wave W —
combine with siblings; do not commit standalone" in the session report.

## DON'T
- Put two subtasks that share an `Owns` file in the same wave.
- Edit a concurrent sibling's file or a serialization-point file — STOP & flag instead.
- Run `git add` / `git commit` yourself, or stage with `-A` / `.` / `<dir>`.
- Run the full test suite from inside a concurrent wave session.
- Default to worktrees — use same-dir sessions.
