---
name: domain-model
disable-model-invocation: true
description: >-
  Build and sharpen the project's LIVING domain model — a ubiquitous-language glossary
  (CONTEXT.md) plus architectural decision records (docs/adr/). Actively challenge fuzzy terms,
  stress-test relationships with edge-case scenarios, cross-check against code, and write the
  glossary and decisions down the moment they crystallize. A shared language makes the agent
  terse, names code consistently, and is easier to navigate next session.
  TRIGGER when: the user wants to pin down terminology / a ubiquitous language, record an
  architectural decision, resolve a naming conflict, OR another skill (analyst, grill, tdd) needs
  the domain model actively maintained — not merely read.
  DO NOT TRIGGER when: a skill only needs to *read* the glossary for vocabulary (that's a one-line
  habit any skill does, not this skill) — this skill is for *changing* the model.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Agent
effort: high
---

# Domain Modeling

Actively build and sharpen the project's domain model as you design. This is the **active**
discipline — challenging terms, inventing edge-case scenarios, and writing the glossary and
decisions down the *moment* they crystallize. (Merely *reading* `CONTEXT.md` for vocabulary is a
one-line habit any skill does — that is not this skill. This skill is for when you are *changing*
the model.)

Why it matters: at the start of a project the developer and the domain experts speak different
languages, and the agent is dropped in to guess the jargon — so it uses 20 words where 1 would do.
A shared language fixes that. The same precise term flows into conversation, variable names, file
names, and tests; the codebase gets easier to navigate; the agent spends fewer tokens thinking.

---

## Phase 0 — Load profile & locate the model

1. Read `.claude/PROJECT.md` → **Domain** (the seed vocabulary and roles) and **Architecture** (so
   terms map to real modules). If `PROJECT.md` is missing or still `TEMPLATE`, you can still run
   (lean on the root `CLAUDE.md` if it carries the facts) — but tell the user `/bootstrap` will wire
   the glossary location into the profile.
2. Locate the model files (lazily created — see below):
   - **`CONTEXT.md`** — the glossary, at the repo root (or the path named in `PROJECT.md` →
     Domain). If a **`CONTEXT-MAP.md`** exists at the root, the repo has multiple bounded
     contexts; the map points to where each `CONTEXT.md` lives.
   - **`docs/adr/NNNN-<slug>.md`** — architectural decision records (or the ADR location named in
     `PROJECT.md`).

## File structure

Most repos have a single context:

```
/
├── CONTEXT.md                 ← the ubiquitous-language glossary
├── docs/adr/
│   ├── 0001-event-sourced-orders.md
│   └── 0002-postgres-for-write-model.md
└── src/
```

Multi-context repos add a root `CONTEXT-MAP.md` and put a `CONTEXT.md` (and optional
context-specific `docs/adr/`) inside each context directory. **Default to a single `CONTEXT.md`** —
introduce the map only when contexts genuinely diverge.

**Create files lazily.** Don't scaffold empty docs. Create `CONTEXT.md` when the *first* term is
resolved; create `docs/adr/` when the *first* decision needs recording.

---

## During the session

Run these continuously while designing — this is a background discipline, not a phase you finish.

### Challenge against the glossary
When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out
immediately. *"Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"*

### Sharpen fuzzy language
When the user uses a vague or overloaded term, propose a precise canonical one. *"You're saying
'account' — do you mean the Customer or the User? Those are different things."* Pick one term per
concept and an `_Avoid_` list of the synonyms it replaces.

### Discuss concrete scenarios
When a relationship is being discussed, stress-test it with a specific scenario that probes the
boundary. *"A lesson moves to a different section mid-course — does its materialized path change?"*
Edge cases are where fuzzy models break; force precision there.

### Cross-reference with code
When the user states how something works, check whether the code agrees (Grep/Glob/Read). If you
find a contradiction, surface it: *"Your code cancels entire Orders, but you just said partial
cancellation is possible — which is right?"*

### Write it down inline
The moment a term or decision crystallizes, **write it** — don't defer to an "update docs" step
that never happens:
- New/changed term → update `CONTEXT.md` per [CONTEXT-FORMAT.md](CONTEXT-FORMAT.md).
- A decision with trade-offs that future readers will question → write an ADR per
  [ADR-FORMAT.md](ADR-FORMAT.md). For drafting a longer ADR, delegate to the **`docs-writer`**
  agent, then review it yourself before it lands — the agent never commits; if ADRs are the
  committed category (profile → Artifact git policy), hand the user the commit command to run.

---

## Output

After the session, report:

- **Glossary changes** — terms added/changed/retired in `CONTEXT.md` (with the `_Avoid_` synonyms).
- **ADRs written** — `docs/adr/NNNN-<slug>.md` paths and their one-line decisions.
- **Open ambiguities** — terms still unresolved, flagged for the user (mirror the "Flagged
  ambiguities" section in `CONTEXT.md`).

---

## Hard rules

- **Write inline, not later.** Capture each term/decision the moment it's settled; an unrecorded
  model decays back into jargon.
- **One term per concept.** Canonical term + `_Avoid_` synonyms. Consistency is the whole payoff.
- **Lazy files.** No empty `CONTEXT.md`/`docs/adr/` — create on first real content.
- **Don't touch app code.** This skill writes `CONTEXT.md` and ADRs only; renaming code to match
  the glossary is `/refactor`'s job.
- **Ground in code.** A glossary term that contradicts the codebase is a bug in one of them —
  surface it, don't paper over it.

## See also

- **`/grill` & `/grill-with-docs`** — a grilling session *is* where most terms crystallize; run
  this skill alongside it to capture them. (`/analyst` also feeds terms here.)
- **`/codebase-design`** — its glossary (Module/Seam/Adapter…) is the *design* vocabulary; this is
  the *domain* vocabulary. Both keep the language tight.
- [CONTEXT-FORMAT.md](CONTEXT-FORMAT.md) · [ADR-FORMAT.md](ADR-FORMAT.md) — the two formats.
