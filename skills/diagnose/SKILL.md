---
name: diagnose
description: >-
  Root-cause debugging workflow — reproduce, isolate, root-cause, fix, verify.
  TRIGGER when: the user reports a bug, failure, crash, test failure, or unexpected/incorrect
  behavior and wants to know WHY it happens and how to fix it.
  TRIGGER ALSO on a bare failure report with no request attached — a pasted traceback, a failing
  test name, "X is broken", a screenshot of wrong output: the report IS the request.
  DO NOT TRIGGER when: the failure is live in production and harming users right now — use
  /incident first (stabilize, preserve evidence), then return here for root cause; the user
  wants to build a new feature (use /analyst); or wants a general code-quality / cleanup pass
  with no specific failure (use /code-review).
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, WebFetch
effort: high
---

# Structured Debugging

Issue: $ARGUMENTS

## Principle

Never guess. Reproduce first, then isolate, then root-cause, then fix the true cause,
then verify. Each phase must produce evidence before moving to the next. A premature fix
that masks the symptom creates new bugs.

## Phase 0 — Load profile

Before debugging, load project facts so this generic workflow becomes concrete:

- [ ] Read `.claude/PROJECT.md` — note **Architecture** (modules/layers/boundaries),
      **Commands** (test / run / logs, if present), and **Plans location** (only if the user wants
      the Diagnosis Report saved).
- [ ] Read applicable `.claude/rules/*` for stack-specific pitfalls and conventions.
- [ ] If `PROJECT.md` is missing **or still `TEMPLATE`**, fall back to the root
      `CLAUDE.md` (always in context) when it carries the architecture/commands above —
      proceed on it, noting you're running without a kit profile. Only if *neither* has
      those facts, STOP and tell the user to run `/bootstrap` first.

Use the Architecture layers and the Commands from PROJECT.md everywhere below; do not assume
hardcoded paths or commands.

---

## Phase 1 — Reproduce

Confirm you can trigger the bug before touching code:

- [ ] Read the error message / traceback / unexpected output carefully.
- [ ] Identify the exact command, request, or code path that triggers it.
- [ ] Run it using the **run/test command from PROJECT.md → Commands** to reproduce.
- [ ] If intermittent: identify the conditions (specific input, env, data, config, timing).
- [ ] Record the exact reproduction steps and observed output.

### Gather evidence BEFORE hypothesizing

Cite observed evidence for every claim; never reason from memory. Read the real thing first:

- [ ] **Read the actual output** — the error/traceback/log, not a paraphrase; capture it verbatim.
- [ ] **Recent history** — `git log --oneline -20 -- <file>` and `git blame` the suspect lines:
      was this touched recently, and by which change?
- [ ] **Adjacent code** — read the failing unit's tests and its comments/docstrings; grep the
      **Plans/backlog location** (PROJECT.md) for a prior fix of the same area.
- [ ] **Production errors** — if PROJECT.md → Integrations lists an error-tracking MCP
      (e.g. Sentry), read the live issue there instead of guessing from the trace.
- [ ] **External service** — if the failure touches a service in PROJECT.md → Integrations,
      `WebFetch` its official docs to confirm field names / types / error codes; never from memory.

DO: *"I read the log — error X at file:line; git blame shows commit Z changed it; the docs say
W — here's the fix."* DON'T: *"Based on my understanding, this might be caused by…"*

**If you cannot reproduce**, the bug may be environment- or state-specific. Check stale
caches, persisted state/DB, and stale build artifacts — see the locations named in
PROJECT.md → Architecture and the installed `.claude/rules/*`.

## Phase 2 — Isolate

Narrow from "something is wrong" to "this specific function/line is wrong":

**Isolate by variation before isolating by reading.** The traceback names a line, not the
condition. Re-run the Phase 1 reproduction with deliberate variations — one TINY (nearest
simpler input, one flag off, ten rows instead of ten thousand), one LARGE (a distant config,
an adjacent feature). Name the hypothesis a variation would delete before running it; one that
deletes nothing is not worth the round trip. A run that still fails deletes a hypothesis; a run
that stops failing names the difference. Treat every condition in the report as the reporter's
hypothesis, never as observed fact: strip one at a time — an unnecessary condition deletes a
whole module from the search. Read code only where the variations pointed. If the case cannot
be varied here (prod-only, no repro env, timing-dependent), say so and read instead — never
report a run you did not make.

- [ ] Read the full traceback — identify the failing file and line.
- [ ] Read that file; understand the function's purpose, inputs, and assumptions.
- [ ] Trace the call chain backward: who calls it? What data does it receive?
- [ ] Check inputs: are they the expected type / shape / range?
- [ ] If silent wrong output (no traceback): add targeted logging to bisect the suspect area.

**Isolate by layer.** Walk the **modules/layers defined in PROJECT.md → Architecture** and
determine which one owns the failure. For each candidate layer: verify its inputs are valid
at the boundary, then verify its outputs. The first layer whose output is wrong while its
inputs are right is the culprit. Use the layer's logs/test command from PROJECT.md to confirm.

**Isolate by dimension when the failure is partial** — 3 of 40 jobs, 2 of 60 tenants, this box and
not that one. Confirm the change is real, diff every dimension you can name (OS, version, shard,
seed, tenant, route, release) between the failing set and the passing baseline, rank by
difference, filter to the top and repeat. It stays correlation until a mechanism explains it.

## Phase 3 — Root-Cause

Now that you know WHERE, understand WHY:

- [ ] Read the suspect code — what assumption does it make?
- [ ] Is that assumption valid for all inputs, or only the common case?
- [ ] Check recent changes: `git log --oneline -20 -- <file>` — recently modified?
- [ ] Is this a regression (worked before) or always-broken (path never exercised)?
- [ ] State the root cause — the fundamental reason, not the surface symptom.

### Common root causes (generic)

- **Off-by-one / indexing** — boundary index, look-ahead, fencepost errors.
- **Null / None propagation** — a missing value cascades into downstream computations.
- **Race / ordering** — concurrent access, unordered effects, missing await/lock.
- **Boundary / warmup** — not enough data/state before the operation is valid.
- **Stale cache** — cached value no longer matches current inputs.
- **Config mismatch** — code and config (or two configs) disagree.
- **Type mismatch** — wrong type/coercion (e.g. float where int expected).
- **Manual step** — the trail ends at a person's action: the cause is the information that was
  missing, late or unusable, or the tool that made a routine action this destructive.

Plus the stack-specific pitfalls documented in the installed `.claude/rules/*` — consult them.

## Phase 4 — Fix (minimal)

Apply the minimal, correct fix at the true cause:

- [ ] Fix the root cause, not the symptom — no symptom masking.
- [ ] Carry "delete code" as a hypothesis before adding any: a defect that looks like a missing
      special case is often a symptom of an implementation that is too complicated.
- [ ] Change as few lines as possible — surgical.
- [ ] If a refactor is needed to fix cleanly, do it as a separate, prior step.
- [ ] Does the fix handle all edge cases, or just the reported one?
- [ ] Name the defect class from the Phase 3 list (boundary/warmup, stale cache, race,
      type mismatch) — a sibling spelled differently is invisible to a text search.
- [ ] Could the same bug exist elsewhere? `grep` for the pattern and for other sites of that class.
- [ ] Add a regression test that fails before the fix and passes after — use `/test`.

## Phase 5 — Verify

Confirm the fix works and nothing else broke:

- [ ] Re-run the exact reproduction from Phase 1 — symptom must be gone.
- [ ] Run the **test command from PROJECT.md → Commands** — all tests pass.
- [ ] Run lint/typecheck if PROJECT.md defines them — no new errors.
- [ ] If a hot path: confirm no performance regression.
- [ ] Confirm the new regression test passes.

## Output Format

```
## Diagnosis Report

**Symptom**: [what the user reported — expected vs actual]
**Hypothesis**: [initial theory before evidence]
**Evidence**: [reproduction command + output, traceback, logs, variation → result → hypothesis deleted]
**Root Cause**: [fundamental reason — file:line, 1–2 sentences]
**Fix**: [what changed and why — minimal, at the true cause]
**Verification**: [reproduction re-run + test results]
**Related Risk**: [defect class; could this exist elsewhere? grep results]
```

The durable products of a diagnosis are the **fix + the regression test**. If the user wants a
**record** of the investigation (a tricky/recurring bug, a shared post-mortem), `Write` this report
to the **Plans location** from `PROJECT.md` (e.g. `<plans>/<YYYY-MM-DD>-<slug>-diagnosis.md`) — offer
it; don't write it unasked. Its git policy follows `PROJECT.md` → Artifact git policy.

## Persist to the artifact

*(Mandatory when `$ARGUMENTS` or the session brief names a plan, card or spec file.)* Follow [`../implement/reference/work-log.md`](../implement/reference/work-log.md). Keep a ledger on disk from the first phase and record deviations the moment they are decided. Before the final reply, append `## Diagnose Log — <date> — <verdict>` to that file; its `### Result` is the Diagnosis Report above; this replaces the offer-only note when the session was handed a planning artifact. Anything you could not observe yourself goes under `Re-check later`, with its command and today's baseline: a post-deploy log grep, a soak count, a UI gesture. The chat output is a copy of the log, never the only record. No planning artifact → skip this section.

## Commit (suggest-only)

*(Only if the fix changed tracked files.)* Offer a copy-paste `git add <explicit paths>` +
`git commit` block for exactly the files you changed, **plus the plan/card file the log was appended to**, — follow the **Commit Message** pattern
in `/implement`: explicit paths only (never `-A` / `.`), text the user pastes (**never run it**).

## See also

- `/incident` — the live-production inversion of this skill: mitigate first, root-cause after.
- `/test` — write the regression test that locks in the fix.
- `/tdd` — reproduce the bug with a failing test first, then drive the fix green (red → green).
- `/code-review` — quality pass on the fix and surrounding code.
