---
name: triage
description: >-
  Move local backlog issues through a triage state machine — read each open issue, sort it into the
  next canonical status (needs-triage → ready → blocked/done…), set its status frontmatter, and
  report the board. The triage roles/labels come from PROJECT.md. Operates on the local markdown
  issue tracker written by /to-issues.
  TRIGGER when: the user wants to triage the backlog, "what should I work on next", sort/label
  issues, groom the backlog, or move an issue to a new state.
  TRIGGER ALSO on the same request phrased as plain work, with this skill unnamed — "is this
  issue still blocked", "what's actually ready to grab", "the board is out of date" — when the
  target is the local issue tracker rather than one issue's implementation.
  DO NOT TRIGGER, above all, on close-out — "I implemented the plans, check everything is done, can
  I move the epic to done?" is /close-epic, not grooming. This skill looks FORWARD: it sorts work
  that has not happened yet. Also DO NOT TRIGGER when: the user wants to create issues from a plan
  (use /to-issues) or implement one (use /implement).
allowed-tools: Read, Glob, Grep, Bash, Edit, AskUserQuestion
effort: medium
---

# Triage: $ARGUMENTS

Walk the local backlog and move each issue to its correct **triage status**, so the board reflects
reality and "what's next" has an obvious answer. Triage is a small state machine: an issue carries
**one** status at a time and moves forward as it gets clarified, unblocked, or finished.

`$ARGUMENTS` optionally narrows scope — one issue id, or a status to sweep (e.g. `needs-triage`).
Empty = triage all open issues.

This skill carries only invariant logic. The issues directory and the **triage labels** (the
canonical status vocabulary) come from `.claude/PROJECT.md`.

**Routing check before anything else.** If the request is about work the user says they have
*already finished* ("реализовал/implemented the plans — check it's all done, can this go to
done?"), that is `/close-epic`, not triage: closing verifies what happened, triage sorts what
hasn't. This is the single most frequent misroute into this skill — 7 sessions, corpus
2026-07-31. Say which skill you are routing to and stop; do not groom the board instead.

---

## Phase 0 — Load profile & the label set

1. Read `.claude/PROJECT.md` — the **Issue tracker** convention (local; the issues directory) and
   the **triage labels**: the canonical statuses and their order (set during `/bootstrap`). If
   missing or `TEMPLATE`, fall back to the root `CLAUDE.md` (always in context) when it carries the
   issues directory and triage labels — note you're running without a kit profile; **STOP** →
   `/bootstrap` first only if *neither* has them.
   - If no triage labels are defined yet, propose a sensible default state machine and ask the user
     to confirm before using it:
     `needs-triage → ready → in-progress → done`, plus `blocked` (off to the side).
2. If `CONTEXT.md` exists, read it so you reason about issues in the project's vocabulary.

---

## Phase 1 — Read the board

Glob the issues directory and read each issue's frontmatter (`id`, `title`, `status`,
`blocked_by`). Build the current board: count by status, and resolve `blocked_by` — an issue whose
blockers are all `done` is *unblocked* and a candidate to advance.

---

## Phase 2 — Triage each issue

**Triage owns the grooming transitions** — getting an issue *ready to be worked*. It does **not**
start or finish work: `in-progress` and `done` track *work*, which the user marks as it happens;
triage only **reflects** them on the board. Advance only when the entry condition holds:

| From | To | When (triage's job) |
|------|----|----|
| `needs-triage` | `ready` | scope is clear, acceptance is verifiable, no unmet blockers |
| `needs-triage` | `blocked` | depends on an unfinished issue or an external dependency |
| `blocked` | `ready` | its `blocked_by` are now all `done` (or a blocker was removed → treat as unblocked) |

**Work states — triage reflects, doesn't drive:** `ready → in-progress` and `in-progress → done`
track *work*, not grooming — triage never starts or finishes work itself. Set `in-progress` when
an issue is picked up and `done` once its work is verified; the user marks this and triage
reconciles it onto the board (and the index) on the next pass. (`/implement` stamps the *plan*
file's status, not the issue's — so nothing else advances an issue to these states.)
**Route-out (not a status):** an issue that's too big or covers multiple capabilities goes
**back to `/to-issues`** to be split — don't force it to `ready`.

When the next status is a genuine judgement call (is this *really* ready? is it one slice or
three?), ask the user via `AskUserQuestion` — present the issue and the candidate move. Don't
silently advance an issue whose acceptance is vague; send it back to `needs-triage` or `/to-issues`
instead.

---

## Phase 3 — Apply & report

1. **Set the `status` frontmatter** on each moved issue (`Edit`, frontmatter only — never rewrite
   the body). Update the status column in the index (`<issues-dir>/00-index.md`) if it exists.
2. **Report the board:**

```
## Triage — <scope>

| Status | Count | Issues |
|--------|-------|--------|
| ready  | 3 | 0002, 0004, 0007 |
| blocked| 1 | 0005 (waits on 0004) |
| needs-triage | 2 | 0008, 0009 |

### Moved
- 0004: needs-triage → ready (scope clear, acceptance verifiable)
- 0003: blocked → ready (0001 is done)

### Recommended next
- ⭐ 0002 — <title> (ready, unblocked, highest value) → /prepare 0002 or /implement 0002
```

---

## Hard rules

- **One status at a time.** Each issue carries exactly one triage label; moving forward replaces it.
- **Don't advance on vague acceptance.** No path to "ready" for an issue whose done-condition isn't
  verifiable — send it back or split it.
- **Frontmatter only.** Triage edits the `status` field, never the issue body.
- **Labels from PROJECT.md.** Use the project's canonical statuses; don't invent ad-hoc ones.
- **Local files only.** Operates on the markdown backlog — no external tracker.

## See also

- **`/to-issues`** — creates the issues this skill sorts (and where an over-large issue gets split).
- **`/prepare` / `/implement`** — pick a `ready` issue and plan/build it; mark the issue `done`
  once the work is verified (triage reconciles it on the next pass — `/implement` only stamps the
  plan file).
- **`/epic-status`** — progress over a wave-structured *decomposition* (one epic directory);
  triage grooms single issues, epic-status reads an epic's waves.
