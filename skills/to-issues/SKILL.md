---
name: to-issues
disable-model-invocation: true
description: >-
  Break a plan, spec, or PRD into independently-grabbable issues using TRACER-BULLET vertical
  slices — each slice cuts end-to-end through every layer (schema→logic→API→UI→tests), is demoable
  on its own, and declares what blocks it. Writes the issues as local markdown files in the
  project's backlog (the local issue tracker), in dependency order.
  TRIGGER when: the user wants to split a plan/PRD/spec into work items, "make issues/tickets out
  of this", "break this down into slices", or set up grabbable units for later implementation.
  DO NOT TRIGGER, above all, on close-out — "I implemented the plans, check everything is done, can
  I move the epic to done?" is /close-epic, not breakdown. This skill looks FORWARD: it creates work
  that has not happened yet. Also DO NOT TRIGGER when: the user wants the parallel-safe execution
  decomposition with file-ownership waves (use /prepare), or wants to build one known change now
  (use /implement).
allowed-tools: Read, Grep, Glob, Bash, Write, AskUserQuestion, Agent
effort: high
---

# To Issues: $ARGUMENTS

Break a plan into **independently-grabbable issues** using **vertical slices** (tracer bullets).
Each issue is a thin slice that cuts through *all* integration layers end-to-end — a narrow but
COMPLETE path someone can pick up, build, and demo on its own. This is the product-level breakdown
that turns a PRD into a backlog of real work items.

`$ARGUMENTS` is the plan/PRD/spec to break down (a file path, or the current conversation).

This skill carries only invariant logic. The backlog location, the local issue-tracker convention,
and triage labels come from `.claude/PROJECT.md`; domain vocabulary comes from `CONTEXT.md`.

**Routing check before anything else.** If the request is about work the user says they have
*already finished* ("реализовал/implemented the plans — check it's all done, can this go to
done?"), that is `/close-epic`, not breakdown. Close-out phrased as work is the single most
frequent misroute into the grooming skills — 7 sessions, corpus 2026-07-31. Say which skill you
are routing to and stop; do not slice a finished epic into fresh issues.

---

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` — the **Issue tracker** (local) and **Issues directory** (where issue
   files live, e.g. `<backlog>/issues/`), plus **Triage labels** and **Architecture**. If missing or
   `TEMPLATE`, fall back to the root `CLAUDE.md` (always in context) when it carries the issues
   directory and architecture — note you're running without a kit profile; **STOP** → `/bootstrap`
   first only if *neither* has them.
2. If `CONTEXT.md` exists, read it — issue titles and bodies use the project's domain vocabulary
   and respect any ADRs in the area touched.
3. Read the source in `$ARGUMENTS` (plan/PRD/spec) in full, including its user stories.

---

## Phase 1 — Explore for prefactors (optional)

If you haven't already, explore the affected code (Grep/Glob, or the **Explore** agent for a wide
repo) to understand the current state. Look for a **prefactor** that would make the slices easier —
*"make the change easy, then make the easy change."* A prefactor becomes the first slice (it blocks
the rest), not a hidden assumption inside another slice.

---

## Phase 2 — Draft the vertical slices

Cut the plan into **tracer-bullet** issues:

<vertical-slice-rules>
- Each slice delivers a narrow but **COMPLETE** path through every layer it needs (schema, domain
  logic, API, UI, tests) — NOT a horizontal slice of one layer ("all the models", "all the UI").
- A completed slice is **demoable or verifiable on its own** — it adds one real, usable increment.
- Any **prefactor** is its own first slice and blocks the slices that depend on it.
- Slices are **independently grabbable**: minimal coupling, explicit `blocked_by` where order matters.
</vertical-slice-rules>

Horizontal slicing is the anti-pattern: splitting by layer produces issues that can't be demoed
until the last one lands and that all break together. Slice by *capability*, not by *layer*.

---

## Phase 3 — Quiz the user

Present the proposed breakdown as a numbered list. Per slice show: **Title**, **Blocked by** (which
slices must finish first), and **User stories covered** (US-n from the source, if any). Ask:

- Does the **granularity** feel right (too coarse / too fine)?
- Are the **dependency** relationships correct?
- Should any slices be **merged or split**?

Iterate (via `AskUserQuestion` for concrete forks) until the user approves the breakdown. Don't
write files before approval.

---

## Phase 4 — Write the issues (local files)

**Create the issues directory if it doesn't exist** (to-issues owns it). Then write one markdown
file per approved slice to the **issues directory from `PROJECT.md`** (the local issue tracker), in
**dependency order** (blockers first) so `blocked_by` can reference real slice ids. Naming:
`<issues-dir>/NNNN-<slug>.md` (zero-padded sequence). Body:

```markdown
---
id: NNNN
title: <short capability name>
status: needs-triage   # the entry state — /triage moves it to ready; never stamp ready here
blocked_by: [<ids, or empty>]
user_stories: [US-1, US-3]
---

## Capability
<the narrow end-to-end increment this slice delivers — demoable on its own>

## Layers touched
<schema / domain / API / UI / tests — the complete path this slice cuts, with real paths from
PROJECT.md → Architecture>

## Acceptance
- [ ] <verifiable check that proves the slice works end-to-end>

## Notes
<prefactor needed? patterns to follow? pitfalls? — cite path:line>
```

Then write/update the index at `<issues-dir>/00-index.md` (this exact name, so `/triage` can find
it): the slice list with titles, `status`, `blocked_by`, and the dependency order, so the backlog
is scannable.

---

## Output

```
## Issues — <source>

| # | Title | Blocked by | Stories | File |
|---|-------|-----------|---------|------|
| 0001 | <slice> | — | US-1 | <path> |

**Order**: 0001 → 0002, 0003 → 0004
**Wrote**: <N issue files + index> to <issues dir>
**Next**: /triage (sort the backlog) · /prepare <issue> (plan a slice) · /implement <issue>
```

---

## Hard rules

- **Vertical, not horizontal.** Every slice is an end-to-end demoable increment. Reject any "all
  the X layer" issue.
- **Independently grabbable.** Explicit `blocked_by`; minimal coupling; prefactor first.
- **Local files only.** Issues are markdown in the backlog location — no external tracker calls.
- **Approve before writing.** Phase 3 sign-off precedes any file write.
- **Facts from PROJECT.md.** Issues dir, triage labels, architecture, and naming come from the
  profile; vocabulary from `CONTEXT.md`.

## See also

- **Before:** `/to-prd` or `/analyst` (the source plan/PRD). 
- **`/prepare`** — for an approved slice that's complex, produces the parallel-safe **execution**
  decomposition (file-ownership waves). `to-issues` = product slices; `/prepare` = how to build one.
- **After:** `/triage` (sort/label the backlog) · `/implement` (build a slice).
