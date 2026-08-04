---
name: grill-with-docs
disable-model-invocation: true
description: >-
  A relentless grilling session that ALSO builds the project's shared language as you go — runs the
  /grill interview while /domain-model captures crystallizing terms into CONTEXT.md and decisions
  into ADRs, inline. You leave aligned AND with the glossary/decisions written down, so the next
  session is terser and the codebase gets named consistently.
  TRIGGER when: the user wants to stress-test a design AND pin down its terminology/decisions —
  "grill me and document it", "grill with docs", aligning on something worth recording.
  DO NOT TRIGGER when: a quick plain stress-test is enough (use /grill), or it's pure glossary/ADR
  work with no plan to interrogate (use /domain-model).
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Agent
effort: high
---

# Grill With Docs: $ARGUMENTS

Run a **`/grill`** session and a **`/domain-model`** session at the same time. The grilling drives
alignment; the domain-modeling captures the language and decisions the grilling surfaces — written
down the *moment* they crystallize, not in a "document it later" step that never happens.

This is arguably the highest-leverage technique in the kit: a single interview that aligns you with
the agent **and** builds a shared vocabulary. The payoff compounds — variables, functions, and
files get named from the same language; the codebase becomes easier to navigate; the agent spends
fewer tokens because one precise term replaces a paragraph of explanation.

`$ARGUMENTS` is the plan or design to grill. If empty, ask what to grill, then stop.

---

## How it runs

This skill **composes the two primitives** — it adds no new interview or glossary mechanics of its
own. Drive both in lockstep:

1. **Ground** — load `.claude/PROJECT.md` (Domain, Architecture) and `CONTEXT.md` + `docs/adr/` if
   present, per each primitive's Phase 0. The glossary you read is also the one you'll extend.
   **Profile optional.** Like both primitives, this runs with or without a profile: if
   `.claude/PROJECT.md` is missing or still `TEMPLATE`, proceed on the plain subject (lean on the
   root `CLAUDE.md` if it carries the facts) and tell the user `/bootstrap` will wire the
   `CONTEXT.md` / `docs/adr/` locations into it.
2. **Grill** — run the **`/grill`** loop on `$ARGUMENTS`: one question at a time, each with your
   recommended answer, exploring the codebase instead of asking when it can. Walk the decision tree
   to resolution.
3. **Capture as you go** — apply the **`/domain-model`** discipline *continuously while grilling*:
   - A fuzzy or overloaded term surfaces → sharpen it and **write it to `CONTEXT.md`** (canonical
     term + `_Avoid_` synonyms) right then.
   - A term the user uses conflicts with the glossary → that conflict is itself a grilling question;
     resolve it and update the glossary.
   - A decision with real trade-offs gets settled → **write an ADR** (`docs/adr/NNNN-<slug>.md`),
     delegating the draft to the `docs-writer` agent if it's long.
   - The grill targets an **existing plan/epic** → also write the resolved decision **back into
     the affected plan file(s)** (not only the ADR/summary) and **sweep** siblings + the overview,
     per the Artifact-Continuity Contract (`rules/_generic/planning-artifacts.md`) — the next
     session reads the plan.
   Create `CONTEXT.md` / `docs/adr/` lazily — on the first real term/decision, not before.

The two run as one conversation: grill a branch → if it crystallized a term or decision, record it
→ continue grilling. Don't batch the writing to the end.

---

## Output

```
## Grill With Docs — <subject>

### Alignment (from /grill)
- Resolved: <decision> → <answer>
- Open (deferred): <fork> — <why>

### Language captured (from /domain-model)
- CONTEXT.md: <terms added/changed, with the _Avoid_ synonyms>
- ADRs: <docs/adr/NNNN-<slug>.md — one-line decision>

### Next
<route: /to-prd (write it up) | /prepare (plan it) | /implement (if trivial)>
```

---

## Hard rules

- **Compose, don't reinvent.** The interview is `/grill`; the glossary/ADR mechanics are
  `/domain-model`. This skill only runs them together — see those two for the details.
- **Write inline.** Capture each term/decision the instant it's settled, mid-grill.
- **Lazy files.** No empty `CONTEXT.md`/`docs/adr/` — create on first real content.
- **One question at a time** (the `/grill` rule still holds).

## See also

- **`/grill`** — the interview loop alone, when you don't need the docs.
- **`/domain-model`** — the glossary/ADR discipline alone, when there's no plan to grill.
- **After:** `/to-prd` (synthesize the aligned discussion) or `/prepare` (plan it).
