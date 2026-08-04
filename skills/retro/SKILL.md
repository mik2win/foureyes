---
name: retro
disable-model-invocation: true
description: >-
  Learning loop over the project's own history — mine archived plans' Deviation Reports,
  implementation logs, handoff notes, and diagnose/arch-health reports for RECURRING patterns,
  then fold each confirmed lesson back into the right artifact (rules, PROJECT.md, CONTEXT.md,
  or a skill) with user confirmation. The kit's memory: what went wrong twice should never go
  wrong a third time. TRIGGER when: an epic just closed, the user says "retro", "what keeps
  going wrong", "learn from this", "post-mortem the last few features", or after a painful
  debugging stretch. DO NOT TRIGGER when: the user wants to diagnose ONE current bug (use
  /diagnose), review current code (use /code-review), or close out an epic's bookkeeping
  (use /close-epic — then come back here).
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Agent
effort: high
---

# Retrospective: $ARGUMENTS

The kit generates evidence about itself constantly — `/implement` writes a Deviation Report
into every plan, `/diagnose` records root causes, `/handoff` snapshots decisions, `/arch-health`
ranks rot. This skill is the only consumer: it reads that exhaust, finds what **recurs**, and
folds the lesson back into the artifact that will prevent the next occurrence. One occurrence
is an accident; two is a pattern; a pattern with no rule against it is a scheduled repeat.

`$ARGUMENTS` optionally scopes the retro (an epic name, a date range like "last month", a
theme like "testing"); empty = everything since the previous retro report (or all history on
the first run).

This skill edits **kit-config artifacts only** (rules, PROJECT.md, CONTEXT.md pointers, retro
reports) — never application code, and never a skill file without explicit confirmation.

---

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` — **Plans/backlog location**, **Archive location**, **Artifact
   git policy**. If missing or `TEMPLATE`, fall back to the root `CLAUDE.md` (always in context)
   when it carries those locations — note you're running without a kit profile; **STOP**: run
   `/bootstrap` first only if *neither* has them.
2. Read `CONTEXT.md` (if present) so lessons are phrased in the project's language.
3. Find the previous retro report at the Plans location (`*-retro.md`) — its date bounds this
   run's window, and its "Lessons applied" list must not be re-proposed.

---

## Phase 1 — Harvest the evidence (read-only)

Collect from the window, citing every source file:

- **Archived plans** (Archive location + backlog): every `## Implementation Log` and
  **Deviation Report** table — what did plans get wrong about the code?
- **Plan status frontmatter** — `PARTIAL` / `BLOCKED` plans and their `notes`.
- **Handoff docs** — "Key decisions" and "Open questions" sections: what kept being decided
  mid-flight instead of at planning time?
- **Diagnose / arch-health / audit reports** at the Plans location — root causes and
  confirmed findings.
- **`git log`** over the window (Bash, read-only) — revert commits and fix-of-a-fix chains
  (`fix`, `revert`, repeated touches of one file in short succession).

For a large window, delegate the sweep to a read-only **Explore** agent per source category
and collect its citations. Do not paraphrase from memory — every harvested item carries its
source path.

---

## Phase 2 — Mine for recurrence (the evidence gate)

Group harvested items into candidate patterns. **A pattern requires ≥2 independent
occurrences, each cited** — one-off events are logged under "Observed once (watch)" and are
NOT actionable this run. Typical pattern shapes:

| Pattern shape | Example signal |
|---------------|----------------|
| Plans keep assuming code that isn't there | same "Plan said / What was done" deviation class in ≥2 plans |
| Same root-cause class recurs | two diagnose reports blaming the same boundary/idiom |
| Same rule violated repeatedly | code-review/audit findings citing one rule in ≥2 rounds |
| Same question asked every feature | recurring open question in specs/handoffs |
| Same file always in the blast radius | hot file appearing in ≥2 deviation/blocked notes |
| Profile fact repeatedly wrong | commands/paths from PROJECT.md corrected in ≥2 logs |

**Classify each candidate against `docs/agent-failure-modes.md`** — the catalog of systematic
agent failure modes. A pattern that matches a mode (premature closure, silent scope narrowing,
confabulated specifics, thrash, …) inherits that mode's documented countermeasure as the
default proposal; cite the mode number in the lesson. A recurring pattern that matches *no*
mode and no kit countermeasure is doubly valuable — flag it as a candidate addition to the
catalog itself.

Then run each candidate through the **`finding-verifier`** agent (batches of 3–4; default
REFUTED on ambiguity) — a "recurring pattern" built on coincidence wastes a rule slot forever.
Only CONFIRMED patterns proceed.

---

## Phase 3 — Route each lesson to the artifact that prevents the repeat

The fix goes where the *next* session will actually meet it:

| Lesson type | Target artifact |
|-------------|-----------------|
| Wrong/stale project fact (command, path, layer) | `PROJECT.md` — correct the fact |
| Recurring code antipattern in one stack | the matching `.claude/rules/*` stack rule (append a lean imperative line) |
| Recurring cross-stack antipattern | `rules/_generic/*` (only if truly generic — prefer stack rules) |
| Terminology confusion / naming drift | hand to `/domain-model` (CONTEXT.md / ADR) |
| Pipeline-stage weakness (plans keep missing X) | the producing skill's checklist — propose via `/writing-skills` conventions |
| Hot-file / blast-radius knowledge | the plan-decomposition guidance in PROJECT.md notes or the epic overview template |
| Decision that keeps being re-litigated | an ADR via `/domain-model` |

One lesson → one target. A lesson that "belongs everywhere" belongs in the most specific
place it will be read.

---

## Phase 4 — Propose, confirm, apply

Present the confirmed lessons as a table: **pattern (with its ≥2 citations) → proposed edit →
target file**. Then confirm via `AskUserQuestion` — batch related lessons, but never bundle a
skill-file edit with rule/profile edits in one question. Apply **only** confirmed edits:

- `PROJECT.md` / rules — apply directly with `Edit` (lean, imperative, in the target file's
  existing voice; a rule line the next session must obey, not an essay).
- Skill files — apply only on explicit confirmation, following `/writing-skills` conventions.
- CONTEXT.md / ADRs — route to `/domain-model`; don't write them here.

Rejected lessons are recorded in the report with the user's reason — a rejection is itself
knowledge (don't re-propose it next retro).

## Phase 5 — Write the retro report

`Write` `<plans>/<YYYY-MM-DD>-retro.md` (its git policy per PROJECT.md):

```markdown
# Retro — <window/scope>

## Lessons applied
- <pattern> (evidence: path, path) → <edit made> in `<file>`

## Rejected (do not re-propose)
- <pattern> — <user's reason>

## Observed once (watch)
- <event> (evidence: path) — becomes actionable if it recurs

## Health notes
- <plans DONE/PARTIAL/BLOCKED counts, deviation rate trend vs previous retro if available>
```

---

## Hard rules

- **≥2 cited occurrences or it's not a pattern.** Singles go to "Observed once" — never into
  a rule.
- **Verify before proposing.** Every pattern passes `finding-verifier`; ambiguity = REFUTED.
- **User confirms every edit.** No rule, profile, or skill change lands without confirmation;
  skill edits need their own explicit yes.
- **Never edit application code.** Code fixes route to `/refactor` / `/prepare` — this skill
  changes what the kit *knows*, not what the app *does*.
- **Respect settled decisions.** A pattern already covered by an ADR or a previous retro's
  rejection is surfaced as "settled — reopen?" — never silently re-applied.
- **Facts from PROJECT.md.** Locations and policies come from the profile — never hardcoded.

## Cross-reference

- **Upstream evidence:** `/implement` (Deviation Reports), `/diagnose`, `/handoff`,
  `/arch-health`, `/close-epic` (run it first to settle the epic; then retro it).
- **Lesson sinks:** `/domain-model` (terms/ADRs), `/writing-skills` (skill edits),
  `PROJECT.md` and `.claude/rules/*` (direct edits here).
