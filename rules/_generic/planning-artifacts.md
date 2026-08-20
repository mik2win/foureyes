---
description: On-demand Artifact-Continuity Contract — the plan file is the single source of truth; persist decisions, sweep siblings, cross-link reports, validate load-bearing claims, stage gates. Loaded when working with plans/specs/backlog artifacts (the planning skills read it explicitly on entry).
paths:
  - "**/plans/**"
  - "**/backlog/**"
  - "**/_backlog/**"
  - "**/*plan*.md"
  - "**/*spec*.md"
---

# Planning artifacts (generic)

The **Artifact-Continuity Contract**: the planning artifact (plan / spec / backlog doc) is
the single source of truth for the work. Every skill and agent that touches a plan honours
it, so context does not leak between pipeline stages or between sessions. This is the
"Finding Contract" idea applied to plans — one shared invariant, no exceptions.

## Plans are the source of truth — the conversation is not

- A fresh session (or a teammate) reads **only the plan file** — not this conversation. A
  decision that lives only in chat is lost the moment the context resets.
- Anything the next stage or the next session must know goes **into the plan**, not into a
  reply that scrolls away.
- Match the length of a written artifact to what the task needs: cover the substance; no
  filler sections, no redundant summaries, no boilerplate.

## Persist every decision the turn it's made

- The instant a decision is settled — a user choice, a resolved ambiguity, a trade-off,
  scope moved in/out — write it into the affected plan **that same turn**, before moving on.
- **Test scope is a decision.** When test scope is agreed, promote it from a "suggested" note
  to a **required step** with explicit **acceptance criteria** in the plan — not an aside.

## Sweep siblings after any decision or review round

- A decision rarely touches one plan. After it lands, **sweep every sibling plan and the epic
  overview** (ADR / risk register / decision table) for staleness and update what the decision
  invalidated.
- **Verify before claiming "all updated"** — re-open each affected file and confirm; do not
  assert a sweep you did not actually perform.

## Cross-link reports — don't strand them

- A spike / review / grill report written to its own file is invisible to the implementing
  session. From **each affected plan's header**, cross-link every report that bears on it
  (relative path + one-line verdict).
- The epic / overview doc carries a **"Reviews & decisions — READ FIRST"** index listing those
  reports, so the next session opens them before touching code.

## Load-bearing behaviour is an assumption, not a fact

- A framework / library **behaviour** claim the plan leans on (an API's shape, a limit, an
  ordering, a side effect) is an **ASSUMPTION-TO-VALIDATE**, never baked in as fact. Mark it,
  and route it to `/spike` for runtime validation before the plan depends on it.

## Stage gates — hand forward only checked artifacts

Each pipeline stage consumes the previous stage's artifact and **trusts it because it was
checked, not because it exists**. The producing skill satisfies its exit gate before routing
onward; the consuming skill re-checks the gate **on entry** and, when it fails, names the
missing items and routes back to the producer (or fixes the artifact with the user first) —
it never silently compensates downstream, where the gap costs more.

| Artifact (producer) | Exit gate — all must hold before the next stage builds on it |
|---------------------|--------------------------------------------------------------|
| Brief (`/discover`) | route recommended · every claim cited (`path:line`) or marked inferred · "searched but absent" recorded · no open question that blocks spec-writing |
| Spec (`/analyst`) | ACs falsifiable ("do X, observe Y") with concrete examples · unhappy paths per US or explicit n/a · assumptions & open questions listed |
| Plan (`/prepare`) | every step answers WHERE + WHAT + HOW + VERIFY · US→step *and* AC→step mapping complete · material assumptions confirmed / repo-verified / routed to `/spike` · waves pass the safety check |
| Implementation (`/implement`) | tests green · behavior driven & observed (or skip reason named) · deviation report + log written into the plan · status frontmatter set |

A gate item that is genuinely inapplicable is **stated** n/a with a reason — never silently
skipped. A returned artifact is not a failure; papering over a weak input is.

The same holds for a whole stage: **a declared skip satisfies the gate, a silent one fails it.**
Skipping an artifact is legal when the downstream artifact names it — what was skipped, why, and
what stands in its place ("no spec: two-line change, the ticket text is the requirement"). An
artifact nobody mentioned is an unchecked input, not an absent need, and the consuming skill
treats it as a failed gate.

## Phase ordering — correctness before structure

When a plan mixes correctness fixes with refactoring, the correctness fixes form the **first,
independent phase** — shippable alone even if every later phase is cancelled. Each structural
phase then carries its own reversibility note. Structure moved before the bug is fixed moves
the bug with it.

## Persistence & new seams

- **Flag git-ignored artifacts.** If a plan/report lands under a git-ignored (local-only)
  path, warn that it won't persist across machines or reach teammates — per the project's
  Artifact git policy (`PROJECT.md`).
- **New seam → design first.** When the work introduces a new module / seam / abstraction,
  run `/codebase-design` **before** planning it — a new abstraction must be justified as a
  deeper module (small interface, more behaviour hidden), not merely more files.
