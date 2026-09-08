---
name: spike
disable-model-invocation: true
description: >-
  Time-boxed throwaway experiment to validate ONE risky hypothesis before
  committing to the full pipeline — write a scratch experiment, run it, record
  works / doesn't / caveats, and explicitly do NOT integrate it into production
  code. TRIGGER when the user wants a quick feasibility check ("just check if X
  works", "spike on Y", "is this even possible", "proof of concept", "validate
  this assumption"). Do NOT trigger when: the approach is already known and the
  user wants to build it → /implement; requirements are unclear → /analyst;
  a full design/impact analysis is wanted → /prepare; the question is how it
  should look or behave, or you want to compare several design options → /prototype.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion
effort: medium
---

# Spike: $ARGUMENTS

A spike is a **time-boxed, throwaway** experiment that answers one risky question
cheaply — "can X do Y?" — without the full `analyst → prepare → implement` pipeline.
The experiment is **scratch code you will delete**; its only product is a finding.

This skill carries ONLY invariant workflow logic. Run/test commands and where source
lives are read at runtime from `.claude/PROJECT.md`. The experiment lives **outside**
the project's source tree and is **never** integrated into production.

---

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md`. If it is missing, or still contains TEMPLATE /
   placeholder markers, fall back to the root `CLAUDE.md` (always in context) when it
   carries the commands/architecture/libraries below — proceed on it, noting you're
   running without a kit profile. Only if *neither* has those facts, **STOP** and tell
   the user: "Profile not configured — run `/bootstrap` to generate `.claude/PROJECT.md`,
   then re-run `/spike`."
2. If `$ARGUMENTS` is empty, ask what hypothesis to validate.

From PROJECT.md, resolve and keep handy:
- **Commands** — `run`, `test` / `test:targeted` (to execute the experiment).
- **Architecture** — where source lives, so you can scaffold the scratch experiment
  **outside** it (never under the app's source paths).
- **Key libraries** — so the scratch uses the project's real dependencies.
- **Plans location** — where the Spike Report is saved (so the finding survives the session).

If `CONTEXT.md` exists, skim it so the hypothesis is framed in the project's vocabulary.

Before framing a brand-new hypothesis, skim the **Plans location** for a prior spike report on
the same question — it may already be settled (`WORKS` / `DOESN'T`). Don't re-spike a decided
call without new evidence; if one exists, surface it instead of repeating the experiment.

---

## Phase 1 — Frame the hypothesis (and the time-box)

Pin the experiment down before writing anything:

- **Hypothesis** — one falsifiable statement: "X can do Y under condition Z."
- **Why it's risky** — what unknown this de-risks (a new library, an API limit, a
  performance ceiling, an integration shape).
- **Pass / fail signal** — the *observable* result that settles it, decided **up front**.
- **Time-box** — the rough budget ("~15 min, then stop and report"). A spike is small;
  if it's growing into a feature, stop and route to `/prepare`.
- **Hard cases** — name the two or three uses that fit *worst* and build at least one; write the
  assumed volumes and concurrency as agreed numbers. A few hard cases are no veto, an unnamed one is.

**When the hypothesis carries concurrency** — retries, webhooks, background jobs, two processes on one
row — list the timelines and the resources they share *before* writing code, then walk the ladder in
order: fewer timelines · shorter timelines · no shared resource · a safe sharing primitive · explicit
coordination. Stop at the first rung that answers the question, and say in the report which rung the
experiment stood on — a mechanism proved on one timeline proved nothing about the shape you will ship.

If the hypothesis is unclear or hides several questions, ask **one** focused question
via `AskUserQuestion` (the `/grill` one-at-a-time discipline) and narrow to a single testable claim.

---

## Phase 2 — Build the scratch experiment

Write the **smallest** experiment that produces the pass/fail signal:

- Put it in a **clearly throwaway location outside the source tree** — a scratch dir
  (e.g. `spike/` or `.spike/`) at the repo root, or the system temp dir. **Never**
  under the Architecture source paths from PROJECT.md.
- Use the project's **real key libraries** (from PROJECT.md) so the result is honest.
- Hardcode, stub, and shortcut freely — this is throwaway. No tests, no abstractions,
  no error handling beyond what the signal needs.

---

## Phase 3 — Run & observe

1. Execute via the **run/test command from PROJECT.md → Commands** (or a direct
   one-off invocation of the scratch file).
2. Capture the actual output / error / measurement — the raw evidence.
3. If the signal is ambiguous, tighten the experiment and re-run — do not guess.

---

## Phase 4 — Record findings

State the outcome plainly against the Phase 1 signal:

- **Verdict** — `WORKS` / `DOESN'T` / `PARTIAL`.
- **Evidence** — the command run + the observed output/measurement.
- **Caveats** — what the spike did NOT prove, conditions assumed, scale not tested.
- **Confidence** — how much weight the result can bear.

**Persist the report (so the finding isn't lost).** `Write` the Spike Report (the Output Format
below) to the **Plans location** from `PROJECT.md`, e.g. `<plans>/<YYYY-MM-DD>-<slug>-spike.md`. The
*scratch code* is thrown away (Phase 5); the *report* is the durable product and survives the
session. Whether it's committed or kept local follows `PROJECT.md` → Artifact git policy.

---

## Phase 5 — Decide, route & clean up

1. **Route** based on the verdict:
   - WORKS / PARTIAL → `/prepare` (design it for real) or `/implement` if scope is
     already trivial; `/analyst` first if requirements are still fuzzy.
   - DOESN'T → report the dead end and the next hypothesis to try.
2. **Fold the verdict back into the plan (when this spike validated an existing plan/epic).**
   Per the Artifact-Continuity Contract (`rules/_generic/planning-artifacts.md`), the report
   alone is stranded — the implementing session reads the plan, not the report. So: write the
   verdict into the affected plan (an assumption-to-validate becomes resolved fact, or the plan
   is revised if it DOESN'T), **cross-link** the report from the plan header, add it to the
   overview's "Reviews & decisions — READ FIRST" index, and **sweep** sibling plans the verdict
   touches. A standalone spike with no plan skips this.
3. **Clean up the scratch.** Delete the experiment, or — if the user wants to keep it
   for reference — move it to the scratch dir and clearly mark it throwaway/gitignored.
   **Never** integrate scratch code into production; the real version is written fresh
   through the pipeline.

---

## Output Format

```
## Spike Report

**Hypothesis**: <falsifiable claim>
**Time-box**: <budget> — <kept / overran>
**Setup**: <what the scratch experiment did, where it lived>
**Verdict**: WORKS | DOESN'T | PARTIAL
**Evidence**: <command + observed output/measurement>
**Hard case**: <which one was built and what it cost — or why none was>
**Caveats**: <what it did NOT prove>
**Recommendation**: <route: /prepare | /implement | /analyst | abandon> — <why>
**Report saved**: <plans path — the durable finding>
**Cleanup**: <scratch code deleted | moved to scratch and marked throwaway>
```

## Hard rules

- **Throwaway only.** Scratch code is never integrated into production — the real
  implementation is built fresh through `analyst → prepare → implement`.
- **Outside the source tree.** The experiment lives in a scratch/temp location, never
  under the Architecture source paths from PROJECT.md.
- **Time-boxed.** If the spike outgrows its budget or needs production changes to
  validate, STOP and route to `/prepare` — that's a planning task, not a spike.
- **One hard case built.** A spike that exercised only the convenient path measured convenience.
- **Facts from PROJECT.md.** Run/test commands and source layout come from the profile.

## Cross-reference

- **Sibling:** `/prototype` — when the question isn't a single yes/no risk but *how it should
  look or behave*; it explores a design space with several options. Spike answers ONE binary
  question; prototype compares many.
- **Before:** `/discover` (prior-art) may surface the risk this spike validates.
- **After:** `/prepare` (design for real) or `/implement` (if trivial).
