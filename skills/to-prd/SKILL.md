---
name: to-prd
disable-model-invocation: true
description: >-
  Synthesize the CURRENT conversation into a Product Requirements Document and save it to the
  project's plans location — no fresh interview, it crystallizes what's already been discussed.
  Quizzes only about which modules the change touches (a design-first nudge) before writing.
  TRIGGER when: the user says "turn this into a PRD", "write this up", "document what we decided",
  or wants a durable doc out of a discussion that's already happened.
  DO NOT TRIGGER when: requirements are still unclear and need an interview (use /analyst), or the
  user wants to break an existing plan into work items (use /to-issues).
allowed-tools: Read, Grep, Glob, Write, AskUserQuestion, Agent
effort: medium
---

# To PRD: $ARGUMENTS

Turn what you and the user have **already discussed** into a clean PRD. This is a *synthesis* skill,
not an interview — the thinking happened in the conversation (often a `/grill` or `/analyst`
session); your job is to capture it precisely. The one thing you do ask about is **which modules
the change touches**, because naming the design surface up front is what keeps a PRD from becoming
a wish-list that ignores the codebase.

`$ARGUMENTS` may point at a source (a brief/spec path, an issue file) to fold in; otherwise work
from the conversation context.

This skill carries only invariant logic. The plans location and naming convention come from
`.claude/PROJECT.md`; the domain vocabulary comes from `CONTEXT.md`.

---

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` — **Plans location** + naming convention (the PRD is a plan),
   **Architecture** (module map, for the modules-touched question), **Domain** (roles/vocabulary).
   If missing or `TEMPLATE`, fall back to the root `CLAUDE.md` (always in context) when it carries
   the plans location and architecture — note you're running without a kit profile; **STOP** →
   `/bootstrap` first only if *neither* has them.
2. If `CONTEXT.md` exists, read it and write the PRD in its **ubiquitous language**.
3. Read any source passed in `$ARGUMENTS` (brief, spec, issue) and fold it in.

---

## Phase 1 — Gather from context (no interview)

Pull the substance from the conversation: the problem, the decisions already made, the scope
agreed, constraints, and any open questions raised. Don't re-ask what's already settled — if the
conversation answered it, capture it. If the conversation is thin and the PRD would be mostly
guesswork, **stop and route to `/analyst`** (the interview skill) instead of inventing requirements.

---

## Phase 2 — The one quiz: modules touched

Before writing, ask the user which **modules / layers** this change touches (offer your best guess
from `PROJECT.md` → Architecture and the conversation, via `AskUserQuestion`). Naming the design
surface now:
- grounds the PRD in the real codebase,
- surfaces ripple effects and reuse early,
- and flags if the change is bigger than the discussion assumed.

If a touched module is unfamiliar, Grep/Glob to confirm it exists and what it does — cite `path`.

---

## Phase 3 — Write the PRD

Write to the **plans location from `PROJECT.md`** using its naming convention (e.g.
`<plans>/<YYYY-MM-DD>-<slug>-prd.md`; prefix a ticket id if the conversation had one). For a longer
PRD, delegate the drafting to the **`docs-writer`** agent, then review it. Structure:

```markdown
# <Feature> — PRD

- **Date:** <today>   ·   **Status:** Draft   ·   **Source:** <conversation | brief path>

## Problem & value
<the pain/gap, who it's for, why now — from the discussion>

## Goals / non-goals
- **Goals:** <what success looks like>
- **Non-goals:** <explicitly out of scope>

## Requirements
- Numbered user stories (US-1, US-2…) and behaviour, in the domain vocabulary.

## Modules touched
- `<module/layer per PROJECT.md>` — <what changes there> (from Phase 2)

## Constraints & assumptions
<decisions taken as given, deadlines, dependencies>

## Open questions
<unresolved forks that still affect scope or design>

## Acceptance criteria
<verifiable, each traceable to a user story (AC-n → US-n)>
```

Keep it factual and traceable — number user stories, reference them from acceptance criteria.

---

## Phase 4 — Route onward

| Next need | Route |
|-----------|-------|
| Break the PRD into independently-grabbable work items | **`/to-issues <prd-path>`** |
| Codebase-readiness / impact analysis before building | **`/prepare <prd-path>`** |
| Requirements still have real gaps | **`/analyst`** (proper interview) |

State the recommendation and the PRD path.

---

## Hard rules

- **Synthesize, don't interview.** The only question you ask is *modules touched*. Everything else
  comes from the conversation — if it isn't there, route to `/analyst`, don't invent it.
- **Ground in the codebase.** Modules-touched must reference real paths from `PROJECT.md` →
  Architecture; confirm unfamiliar ones.
- **Domain vocabulary.** Write in the `CONTEXT.md` language.
- **Facts from PROJECT.md.** Plans location and naming convention come from the profile.

## See also

- **Before:** `/grill` or `/analyst` (where the discussion happens). **`/discover`** brief as a source.
- **After:** `/to-issues` (split into work items) or `/prepare` (plan the build).
