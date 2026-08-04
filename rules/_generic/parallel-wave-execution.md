---
description: >-
  On-demand wave-execution contract — the invariants a session must honour while 2+ plans run
  concurrently: disjoint `Owns` within a wave, Deps-landed before a wave starts, solo tasks,
  same-dir sessions over worktrees, the `Owns`/`Reads`/`Shared edits` triad, serialization
  points, targeted-tests-only in-wave, and the classification table for a fix that lands
  outside `Owns`. This is the in-flight half; the decomposition-time templates (per-session
  brief, wave schedule, ownership matrix, RUN-ORDER) live in
  `skills/prepare/reference/parallel-wave-execution.md` and are read while decomposing, not
  while implementing. Loaded when working with plan/backlog artifacts.
paths:
  - "**/plans/**"
  - "**/backlog/**"
  - "**/_backlog/**"
  - "**/*plan*.md"
---

# Parallel-wave execution (generic)

How a session must behave when it is **one of several running concurrently** against the same
repo. Companion to the Artifact-Continuity Contract (`rules/_generic/planning-artifacts.md`) —
that file governs the plan as an artifact, this one governs the sessions executing it.

**Applies when** a plan declares `Wave` / `Owns` (i.e. it came out of a wave-structured
decomposition), or when 2+ plans are launched at once. A single-plan session may skip it.

**Not here:** the templates used to *produce* a decomposition — per-session brief, wave-schedule
and file-ownership tables, RUN-ORDER, the backlog file layout. Those live in
`skills/prepare/reference/parallel-wave-execution.md`, loaded at decomposition time.

Legend: `→` must wait (file/data dependency) · `∥` concurrent-safe (disjoint files) ·
`⚠` shared-file conflict.

## Core model — waves over a dependency DAG

- A **wave** is a set of subtasks runnable concurrently, each in its own session.
- **Disjoint-ownership invariant** — within one wave, every subtask's `Owns` file-set is pairwise
  disjoint from the others. No two concurrent sessions ever write the same file. This is the
  whole safety guarantee; everything else in this file is downstream of it.
- **Deps-landed invariant** — a subtask's `Deps` are merged into the shared branch *before* its
  wave starts. Waves are the topological layers of the dependency DAG, nothing more.
- Re-layer until both hold. A "wave" that violates disjoint ownership is not a wave — split the
  offenders across two waves, or serialize them.
- **The hard boundary is _concurrency_, not ownership.** The only thing that corrupts parallel
  work is two **concurrent** sessions writing the same file. A file owned by an already-merged
  prior wave, by a not-yet-started future wave, or by no subtask at all carries no concurrency
  risk — editing it is a *scope* question, not a *safety* one. Keep the two apart; conflating
  them is what turns "stay in your lane" into a shipped hack.

## Solo tasks (run alone)

Some subtasks cannot share a wave with anything: hot-file hubs (wiring that touches an
entrypoint plus a registry plus shared types), broad refactors whose blast radius resists clean
carving, and gated finals that run only if an upstream decision says so.

Mark them **explicitly** — own single-task wave, `(solo)` on the wave, `Solo: YES — <reason>` at
the top of the brief; every other task carries `Solo: no`. The marking is load-bearing: a
session whose brief says `Solo: YES` has no concurrent siblings and therefore gets the **widest**
out-of-`Owns` latitude (see the classification table). A solo task that forgot to say so gets
treated as a wave member and stops on fixes it was safe to make.

## Isolation — same-dir sessions, not worktrees (default)

For file-disjoint waves, run each subtask as a **separate session in the same repo directory, on
one branch**. Do **not** reach for git worktrees by default:

- Same-dir sessions share the project's skills, rules, and permission allowlist — no
  per-command approval prompts, no missing `.claude/` context. **Worktrees lose all of this**,
  which is the reason they are not the default, not a stylistic preference.
- Ownership is what keeps the shared tree safe, and ownership is already enforced by the
  disjointness invariant. Filesystem isolation buys nothing a disjoint wave does not already
  have.
- Use a worktree only when two tasks genuinely must edit the same file *and* you want
  filesystem isolation — and even then, prefer serializing them into different waves.

## File ownership — the conflict key

Every subtask declares three sets:

| Field | Meaning | Conflict? |
|-------|---------|-----------|
| `Owns` | Files it exclusively creates / edits / deletes | **Yes** — never shared within a wave |
| `Reads` | Files read for context, never modified | No — freely shared |
| `Shared edits` | Registry / config / doc files it must append to | Serialized — ≤1 editor per wave per file |

Tasks may share `Reads`. They may **never** share `Owns`.

## Serialization points (shared / hot files)

Files many subtasks naturally want at once:

- **Wiring / registries** — the composition root, the app entrypoint, a plugin or route
  registry, DI wiring.
- **Cross-cutting types / config** — shared type modules, a central config file or object.
- **Docs and contracts** — `PROJECT.md`, `CONTEXT.md`, `.claude/rules/*`, and the task's own
  `<backlog>/` files.

**Rule:** at most **one** task per wave may edit a given shared file. If several need it,
serialize them into different waves, **or** route every edit into a single dedicated
"wiring / integration" subtask that runs in its own wave after the feature tasks land.

A file whose edits are structurally disjoint (separate keyed blocks in one config, appended
entries that never interleave) may be declared a tolerated exception in the plan — name it and
say why, or the default rule stands.

## Tests during a wave

- **In-wave** — run **only** the targeted tests for your `Owns` modules (`PROJECT.md` →
  Commands, `test:targeted`). Do **not** run the full suite mid-wave: N parallel full suites
  race on shared artifacts, are slow, and drown the signal you are actually looking for.
- **After the wave merges** — run the full `test` command **once** as the integration and
  regression pass. That single run, not the in-wave ones, is what clears the wave.

## When a necessary fix lands outside `Owns`

An audit finding, a failing test, or a missed dependency may demand a change to a file **not in
your `Owns`**. A blanket "never touch anything else" is wrong — it forces you to either violate
ownership or ship the hack. Classify the file first; only **concurrent** collisions are a hard
stop. Everything else is logged scope, and the user reviews every uncommitted diff before it is
committed, so a minimal, recorded fix to a non-concurrent file is safe.

Classify using your brief (`Solo`, `Siblings this wave`) plus the overview's ownership matrix and
wave schedule:

| Class | The file is… | Action |
|-------|--------------|--------|
| **Shared-edit (mine)** | in **my own** `Shared edits` | Append-only edit as declared; log it. |
| **Concurrent-sibling** | in the `Owns` / `Shared edits` of a session running **now** in my wave | **HARD STOP — never edit.** Record under *Cross-Session Findings*; the sibling or a follow-up fixes it. This is the disjoint-ownership invariant. |
| **Serialization-point** | a hot / shared file (composition root, registry, shared types or central config, `PROJECT.md`, `CONTEXT.md`, `.claude/rules/*`, the task's own `<backlog>/` docs) — **even if currently unowned** | **STOP & flag.** Another wave or session may touch it; route the change into a dedicated wiring subtask. |
| **Sequenced** | owned by a **prior, already-merged** subtask, or a **later, not-yet-started** one | Default **flag** for the owning subtask. Edit **only** if it is a true blocker for your task **and** the fix is small and clearly belongs there → log it as a scope deviation and note the overlap so the user can sequence it. |
| **Unowned** | claimed by **no** subtask in the schedule, and not a serialization point | **Minimal fix allowed.** Scope it to the actual defect, log it, report it. |

**Solo / single-session wave** — the Concurrent-sibling row is vacuous, so you get the widest
latitude: apply the Sequenced / Unowned / Serialization-point rows directly. You are the only
writer, so audit- and test-driven fixes are safe. Still **flag** future-wave and
serialization-point files rather than editing them, and **log every** out-of-`Owns` edit.

Every flagged-but-unfixed item and every applied out-of-`Owns` fix must surface in the session's
final report under *Cross-Session / Out-of-Scope Findings*. Silent scope creep defeats the point
of the classification — the table exists to make the deviation visible, not to license it.

## Committing a wave

Do **not** emit a commit command mid-wave. The coordinator combines the wave once its sessions
land, and the user runs it; a per-session commit in a shared tree is what picks up a concurrent
sibling's uncommitted changes. Note `Part of Wave W — combine with siblings; do not commit
standalone` in the session report instead. `git add` / `git commit` are user-only in either
case, and staging is always by explicit path — never `-A`, `.`, or a bare directory.

## DON'T

- Put two subtasks that share an `Owns` file in the same wave.
- Edit a concurrent sibling's file or a serialization-point file — STOP & flag instead. (Other
  out-of-`Owns` fixes follow the classification table, not a blanket ban.)
- Run the full test suite from inside a concurrent wave session.
- Default to worktrees — they lose shared skills, rules and permissions.
- Let an out-of-`Owns` fix land without a line in the final report.
