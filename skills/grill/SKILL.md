---
name: grill
description: >-
  Relentless one-question-at-a-time interview that stress-tests a plan or design until every
  branch of the decision tree is resolved and you and the user share one understanding. The
  reusable alignment primitive the pipeline leans on (analyst wraps it, arch-health runs it,
  prepare/spike apply it) and a standalone way to interrogate any plan before building.
  TRIGGER when: the user wants to pressure-test a plan/design, says "grill me" / "interview me"
  / "poke holes in this" / "what am I missing", OR another skill needs the interview loop.
  DO NOT TRIGGER when: the user wants a written spec (use /analyst), a full impact analysis
  (use /prepare), to ALSO capture the terms/decisions as you align (use /grill-with-docs),
  or simply asked a question to be answered (just answer it).
allowed-tools: Read, Grep, Glob, Bash, WebSearch, Write, AskUserQuestion, Agent
effort: high
---

# Grill

Interview the user **relentlessly** about every aspect of this plan or design until you reach a
shared understanding. Walk down each branch of the decision tree, resolving dependencies between
decisions one at a time. The whole point is to close the **alignment gap** — "no-one knows
exactly what they want" — *before* code gets written, when changing course is still cheap.

This is the invariant interview discipline used across the kit: `/analyst` wraps it to write a spec,
`/arch-health` runs it to walk a chosen opportunity, and `/prepare` / `/spike` apply the same
one-question discipline when confirming assumptions or framing a hypothesis. You can also run it
standalone (`/grill <thing to grill>`) to stress-test any plan — including a non-code one. The
subject to grill is `$ARGUMENTS`, the current conversation, or whatever the calling skill hands you.

---

## Phase 0 — Ground (light, optional)

Grill runs with or without a project profile — don't block on it (lean on the root `CLAUDE.md` if
it carries the facts).

- If `.claude/PROJECT.md` exists, read its **Domain** (vocabulary, roles), **Architecture**, and
  **Plans location** (where a standalone run saves its alignment summary) so your questions use the
  project's real terms and reference real modules — never invent jargon.
- If `CONTEXT.md` (the project glossary, maintained by `/domain-model`) exists, read it too and
  phrase questions in its **ubiquitous language**. When the user reaches for a term that conflicts
  with the glossary, that conflict is itself a question to grill.
- Skim the project's recorded decisions and prior work for the topic being grilled — ADRs
  (`docs/adr/`), the `CONTEXT.md` glossary, and existing plans/backlog at the **Plans location**.
  A settled verdict or an existing implementation is itself something to pin down: don't
  re-litigate a resolved decision without new evidence — surface it and ask whether anything
  has changed.
- If neither exists (e.g. grilling a non-code plan, or a repo before `/bootstrap`), proceed
  anyway on the plain subject.

---

## The loop

**One question at a time.** Ask a single question, wait for the answer, then ask the next.
Dumping many questions at once is bewildering and lets vague answers slide — never do it.

For each question:

1. **State the question** plainly, in the project's vocabulary.
2. **Give your recommended answer** and a one-line reason. A grilling is not a blank
   interrogation — you bring a point of view the user can confirm, sharpen, or reject.
3. **Wait** for the response. Let it reshape the tree — a new answer may open or close later
   branches. Adapt; don't read from a fixed script.

Use `AskUserQuestion` when the answer is a genuine choice among a few concrete options; use plain
text for open-ended questions. Never batch unrelated questions into one prompt.

### Explore instead of asking

**If a question can be answered by looking at the codebase, look — don't ask.** Grep/Glob/Read
the repo (or a read-only shell check, or delegate a wide sweep to the **Explore** agent) and
confirm what you found instead of making the user tell you something the code already states. For a genuinely open external
question (a library's limits, an API's shape), a quick `WebSearch` beats guessing. Only ask the
user what only the user can answer: intent, priorities, trade-offs, and acceptance.

---

## What to grill

Walk the decision tree breadth-first, resolving dependencies before dependents. **Within a
tier, ask first the question whose answer would most reshape the plan** — highest uncertainty ×
blast-radius. Ten easy questions that change nothing are worth less than the one that redraws
the tree; if you already know which answer you'd bet on and being wrong wouldn't change the
design, that question goes last or not at all.

- **Problem & value** — what pain/gap, for whom, what happens if we *don't* build it.
- **Scope** — the smallest useful slice; what is explicitly out; what is deferred.
- **Decisions & their dependencies** — each real fork in the design, in dependency order (a
  choice that constrains later choices comes first).
- **Assumptions** — surface every "we're taking X as given" and test it: against the user, or
  against the code (cite `path:line` when you verify one).
- **Edge cases & failure modes** — empty/boundary inputs, concurrency, partial failure,
  idempotency — the cases a happy-path plan silently skips.
- **Acceptance** — how we'll know it works; the observable definition of done.
- **Unquantified words** — every "fast", "reliable", "handy", "large", "soon" hides a decision
  nobody has made. Ask for the number and its unit, or record it as an open question: left
  vague, it gets decided silently by whoever writes the code, and no one can say later that
  it came out wrong.

Challenge over-scope, contradictions, and anything simpler-than-proposed. A good grilling pushes
back; it doesn't just transcribe.

---

## Convergence

Keep going until the decision tree is **resolved** — every branch has an answer or an explicit
"deferred, and here's why it's safe to defer". Then stop; don't manufacture questions past
alignment. If the user stalls on a fork, record it as an open question and move on rather than
blocking the whole session.

**Steelman before you close.** As the final exchange, state the strongest honest case *against*
the now-agreed plan in 2–3 sentences — the argument a sharp skeptic would make — and ask the
user to defuse or accept it. If it collapses, the alignment is real; if it survives, it enters
the summary as a named risk. Agreement that was never pushed on isn't alignment, it's momentum.

---

## Output

A short **alignment summary** the caller (or the user) can act on:

```
## Alignment — <subject>

### Resolved
- <decision> → <answer> (<why>)

### Assumptions confirmed
- <assumption> — <user-confirmed | verified at path:line>

### Open questions (deferred)
- <unresolved fork> — <why deferred / what it blocks>
```

**When invoked by another skill**, this summary is your return value — hand it back (don't write a
file); the caller folds it into its own spec/plan/report.

**When run standalone, persist it so nothing is lost.** `Write` the alignment summary where it
survives the session:
- **grilling an existing plan/epic** → write the **resolved decisions back into the plan file(s)**
  themselves (not only into the summary), per the Artifact-Continuity Contract
  (`rules/_generic/planning-artifacts.md`): the next session reads the plan, not this chat. Then
  **sweep** sibling plans + the overview for anything a decision invalidated. Append the summary to
  the plan you were grilling; otherwise
- write `<plans>/<YYYY-MM-DD>-<slug>-alignment.md` at the **Plans location** from `PROJECT.md`
  (its git policy follows `PROJECT.md` → Artifact git policy);
- if there's no profile yet (pre-`/bootstrap`), save `ALIGNMENT-<slug>.md` at the repo root and say so.

Then suggest the next step — usually `/to-prd` to expand the saved alignment into a PRD (no
re-interview), or `/prepare` to plan it; `/analyst` only if it needs a fuller spec from scratch, or
straight to building if the scope is already trivial.

---

## Hard rules

- **One question at a time.** Wait for each answer before the next. Never batch.
- **Recommend, don't just ask.** Every question carries your suggested answer + reason.
- **Look before you ask.** Anything the codebase or docs can answer, you answer — don't outsource
  it to the user.
- **Speak the project's language.** Use the Domain/`CONTEXT.md` vocabulary when present.
- **Don't write code or full specs.** Grill's only output file is the short **alignment summary**
  (standalone, so nothing is lost) — the spec/plan/PRD belong to `/analyst`, `/prepare`, `/to-prd`.
  When invoked by another skill, write nothing; return the summary to the caller.

## See also

- **`/analyst`** — wraps this loop to produce a full requirements **spec**.
- **`/prepare`** — wraps it to confirm assumptions during **impact analysis**.
- **`/domain-model`** — when a grilled term needs to enter the **glossary** or a decision needs an
  **ADR**, hand off there.
- **`/grill-with-docs`** — same interview loop, but captures crystallizing terms/decisions into
  `CONTEXT.md` + ADRs *as you go*; reach for it when the alignment is worth recording, not just
  reaching.
