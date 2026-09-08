---
name: onboard
disable-model-invocation: true
description: >-
  Fast comprehension of an unfamiliar codebase — surface scan, run-it-first, one traced
  end-to-end flow, git-history archaeology (churn hotspots, bus factor, the oldest untouched
  code), seams & boundaries, load-bearing weirdness list — into a written orientation map.
  TRIGGER when: joining/inheriting an unfamiliar repo, "разберись в этом проекте", "how does
  this codebase work", "map this project", before the first real task in a codebase nobody
  has profiled yet.
  DO NOT TRIGGER when: researching one feature/capability in a known repo (use /discover),
  hunting architectural rot in a familiar one (use /arch-health), or the user wants
  PROJECT.md written (that's /bootstrap — this skill *feeds* it).
allowed-tools: Read, Grep, Glob, Bash, WebFetch, AskUserQuestion, Write, Agent
effort: high
---

# Codebase Onboarding: $ARGUMENTS

## Principle

Understanding is built from **behavior first, then structure, then history** — run it
before reading it, trace one real flow before mapping all of them, and let `git log` tell
you what the files can't: where the work happens, who knows it, and what everyone is
afraid to touch. The output is a written map, because comprehension that stays in one
session's head is re-paid by every next session.

Read-only on app code. The only file you create is the orientation report.

## Phase 0 — Context (works pre-bootstrap by design), and which mode you are in

Read `README`/`CONTRIBUTING`/docs index if present — as *claims to verify*, not facts: docs
drift, code doesn't. Then pick the mode from whether the repo carries an active profile:

**Cold mode — no `.claude/PROJECT.md`.** The default, and what this skill was built for: run
the full suite of phases below and build the map from zero. Don't stop for the missing profile.

**Verification mode — an active `PROJECT.md` (plus `CONTEXT.md`, project rules, docs index).**
The repo is already profiled, so **start from what exists, verify it against code, and report
drift** rather than rediscovering from scratch: read the profile's architecture/module map and
commands first, then run the phases as *checks* on those claims — does the entry point still
live where the map says, does the stated test command still pass, does the traced flow still go
through the layers the profile names. Every phase still runs; what changes is that each one
starts from a claim instead of a blank page, and disagreement between doc and code is itself a
finding. Do not edit the profile — this skill is read-only; drift goes into the report so the
user (or `/bootstrap`) folds it back.

## Phase 1 — Surface scan (minutes)

- Manifest + lockfile → language, framework, the real dependency list (the framework in
  the lockfile beats the one in the README).
- CI config (`.github/workflows`, etc.) → how it's actually built/tested/deployed — CI is
  the only documentation forced to stay true.
- Top-level layout + entry points: `main`/`app`/`cli`/`server`/routes/jobs — what *kinds*
  of process exist (web, worker, cron, CLI)?
- Config surface: env keys, settings schemas, feature flags → the system's external knobs.

## Phase 2 — Run it before reading it

If a run/test command is discoverable (CI, README, manifest scripts) and safe (no prod
credentials, no external writes), run the test suite and/or start the app and hit one
endpoint/command. Observed behavior anchors everything you read next — and a suite that
doesn't pass on a clean checkout is finding #1. If nothing runs safely, say so in the
report (it's an onboarding cost every newcomer will pay).

## Phase 3 — Trace one real flow, end to end

Pick the most representative user-facing operation (from routes/CLI verbs) and trace it:
entry → validation → domain logic → persistence → response/effects, citing `path:line`
at each hop. One deep vertical teaches the architecture's *dialect* — layering, error
style, DI wiring, naming — better than ten shallow horizontals. Where the repo is large,
fan out **Explore** agents in parallel with distinct lenses (by-entry-points, by-tests,
by-config), but trace the spine yourself: the spine is judgment, not sweep. Reconcile the
trace against the Phase 2 run and mark each hop **observed** or **inferred**: reading
misses the frames a framework injects — middleware, inherited callbacks, ORM hooks.

**Read the tests as documentation**: test names are the behavior vocabulary; fixtures
show the domain objects' real shapes; what has *no* tests is the first danger-zone entry.

**When re-reading a method stops paying, frame it**: on paper, name each field it touches
as a parameter, each mutation as a return value. A field overwritten before any read was
never an input; a parameter you cannot name is a glossary candidate, not an "unclear" note.

## Phase 4 — History archaeology (the part files can't tell you)

```bash
git log --format="%an" | sort | uniq -c | sort -rn | head   # who holds the knowledge (bus factor)
git log --since="6 months ago" --diff-filter=M --name-only --format= | sort | uniq -c | sort -rn | head -20   # churn hotspots
git log --format="%ad" --date=short -1 -- <dir>             # per-area last-touched
```

- **Churn hotspots** = where the business actually lives (and where bugs cluster —
  churn × complexity is the best bug predictor available without running anything).
  Drop generated files, lockfiles and locale dumps, then say WHY each survivor churns —
  feature work, repeated fixing, or a mass edit that orients nobody.
- **Recent activity** = the current front: what the team is building now.
- **The untouched old code** = either finished-and-stable or feared — `git log --grep`
  for revert/hotfix language around it tells you which.
- Skim merged PR/commit messages for the last month — vocabulary, active concerns, and
  how much process the team really uses.

## Phase 5 — Seams, boundaries, weirdness

- Module map: the 5–10 real components and the dependency direction between them (delegate
  breadth to `arch-tracer`-style tracing where wiring is opaque).
- External surface: integrations, queues, storages — everything that leaves the process.
- **Load-bearing weirdness list**: everything that surprised you — the odd lock order, the
  duplicated constant, the hand-rolled thing a library usually does. Each entry is
  *"surprising, reason unknown — check `git log -L` before touching"* (`core.md`:
  surprise is evidence of a constraint you can't see; never normalize on first contact).

## Phase 6 — The orientation report

Write to the plans location if PROJECT.md defines one, else offer `./ONBOARDING.md`
(confirm before creating). In verification mode the report's most valuable section is the drift
list — that is what the user folds back into the profile and rules. Structure:

```markdown
# <Repo> — orientation map (<date>)

## What this is · How to run/test (verified: <what you actually ran>)
## Architecture in 5 lines (+ the traced flow, path:line per hop)
## Drift vs docs (verification mode only — each claim in PROJECT.md / CONTEXT.md / project
##   rules that the code contradicts: the claim, the `path:line` that disproves it, and which
##   of the two is now right. Omit this section entirely in cold mode.)
## Hotspots (churn, filtered — with why each churns) · Current front · Bus factor
## Danger zones (untested / feared-old / weird-with-unknown-reason)
## External surface (integrations, storages, queues)
## Glossary candidates (domain terms → /domain-model)
## Open questions (what only the team can answer)
## Suggested next: /bootstrap (profile), /domain-model (glossary), /arch-health (debt scan)
```

Every claim observed (`path:line`, command output) or marked inferred. If `/bootstrap`
runs next, this report is its input — offer to chain it.

## Hard rules

- **Run before you read; trace before you map; verify docs against code** — README claims
  are tier-Guessed until observed.
- **Read-only on app code**; never "fix" anything mid-onboarding — weirdness goes on the
  list, not into a diff.
- **Depth over coverage**: one flow traced to the bottom beats every directory skimmed.
  Say what you did NOT explore — a map that hides its edges misleads (`core.md`).

## See also

- `/bootstrap` — turn the map into PROJECT.md; `/discover` — one capability, known repo;
  `/arch-health` — debt scan once oriented; `/domain-model` — capture the glossary.
