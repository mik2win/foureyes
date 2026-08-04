---
name: discover
disable-model-invocation: true
description: >-
  Feature research & ideation — frame a request, find prior art and reuse
  candidates in the repo (and optionally the web), then write a short feature
  brief and route onward. Read-only on app code; no spec, no plan, no
  implementation. TRIGGER when the user wants to research a feature, find prior
  art, check "what already exists for X", scope a fuzzy idea, or hunt for reuse
  before committing to a design ("research this", "what's already there", "how
  do we usually do X", "is there anything we can reuse"). Do NOT trigger when
  there is already a clear spec or scope → go to /prepare; or the request is a
  bug/failure → use /diagnose.
allowed-tools: Read, Grep, Glob, Bash, WebFetch, AskUserQuestion, Write, Agent, Skill
effort: high
---

# Feature Discovery: $ARGUMENTS

The research step at the very front of the pipeline. You **frame** a request and
surface **what already exists** before anyone writes a spec or a plan — so reuse
opportunities and house patterns are found early, not after the fact.

This skill carries ONLY invariant workflow logic. Every project-specific fact
(plans location, architecture/module map, integrations) is read at runtime from
`.claude/PROJECT.md`. You are **strictly read-only on app code** — you research
and write a brief; you do not edit source, write a spec, or build a plan.

Pipeline position: `/discover` (research) → `/analyst` (spec) → `/prepare`
(plan) → `/implement` (code).

---

## Phase 0 — Load profile

Before anything else, load context (this mirrors `skills/implement/SKILL.md`):

1. Read `.claude/PROJECT.md`. If it is missing, or still contains TEMPLATE /
   placeholder markers, fall back to the root `CLAUDE.md` (always in context) when it
   carries the stack/architecture/integrations below — proceed on it, noting you're
   running without a kit profile. Only if *neither* has those facts, **STOP** and tell
   the user: "Profile not configured — run `/bootstrap` to generate `.claude/PROJECT.md`,
   then re-run `/discover`."
2. If `$ARGUMENTS` is empty, ask the user what feature or question to research.
3. Read applicable `.claude/rules/*` (conventions, patterns) that bear on the area, and
   `CONTEXT.md` (the domain glossary) if present — frame the request in its vocabulary.

From PROJECT.md, resolve and keep handy these keys (names are profile-defined):
- **Plans/backlog location** — where the feature brief is written.
- **Architecture** — layers, module map, where code lives.
- **Integrations** — external APIs and where their docs are.
- **Domain** — vocabulary and roles, to frame the request in the project's terms.

Then, before searching, skim the **Plans/backlog location** for an existing brief or spec on
this topic. If it has already been researched, say so and build on the prior brief rather than
re-researching a settled question without new evidence.

---

## Phase 1 — Frame the request

Turn `$ARGUMENTS` into a crisp framing — do not start searching until this is clear:

- **Problem statement** — the concrete pain or gap, in the project's domain vocabulary.
- **Who / why** — who benefits (user / operator / developer / system) and why now.
- **What "found" looks like** — what a good discovery answers (reuse? prior art? feasibility?).

If the framing is ambiguous and it changes where you'd look, ask **one** focused
question via `AskUserQuestion`. Otherwise restate your framing in 2–3 sentences and proceed.

---

## Phase 2 — Prior-art in the repo (the core pass)

Find what already exists, guided by `PROJECT.md` → Architecture (its layer/module map):

1. **Glob/Grep** for existing implementations of the same or a similar capability —
   feature keywords, domain nouns, entity names, route/command names.
2. **Reuse candidates** — for each shared/utility/helper layer and common component
   named in PROJECT.md → Architecture, check whether the needed thing already exists.
3. **Closest existing pattern** — the nearest feature to replicate, so a later design
   matches house style.
4. **For a large or unfamiliar repo**, delegate the sweep to a read-only **Explore**
   agent ("very thorough"); summarize what it reports — do not dump file lists.
5. **Prior/removed attempts** — `git log --grep=<keyword>` and `git log -- <path>` (Bash) to
   surface earlier or reverted work on this capability, so you don't re-tread abandoned ground.

### Search multi-modal — one angle always misses

Each search angle is blind to what the others surface. For anything beyond a trivial lookup,
run several of these deliberately (not just keyword grep):

| Angle | How | Finds what keyword grep misses |
|-------|-----|-------------------------------|
| By name | Glob/Grep symbols, file names | conventionally-named implementations |
| By content | domain nouns/verbs, error/log strings, UI copy | code named differently than the concept |
| By caller | who imports/registers/routes it; DI wiring, route tables | capabilities reachable only via wiring |
| By test | test names & fixtures | behavior the impl's naming hides — tests name capabilities |
| By config | feature flags, env keys, settings schemas | half-shipped or toggled-off prior art |
| By history | `git log --grep`, `git log -- <path>` | removed/reverted attempts and their reasons |

**Negative results are findings.** When an angle comes up empty, record it — *"searched
<how/terms> — absent"*. Evidence of absence (you looked, it's not there) is what justifies
building new; absence of evidence (you didn't look) is how duplicates get written. These lines
go into the brief so the next session doesn't re-run the same dead-end searches.

**Cite a repo path (`path:line`) for every reuse candidate and prior-art claim.**
A claim with no path is a guess — drop it or verify it. Mark the tier of every claim:
**observed** (opened the file, cite `path:line`) vs **inferred** (concluded from naming/structure
— say so, and from what).

---

## Phase 3 — External prior-art (optional)

Only when the question is genuinely open and repo evidence is insufficient:

1. If the feature touches a service in PROJECT.md → Integrations, **WebFetch** that
   service's official doc URL (from the Integrations entry or the matching rule) to
   confirm capabilities, endpoints, and constraints — verify, don't trust memory.
2. For a genuinely open research question (unknown approach, trade-offs not answerable
   from the repo), chain the global **`deep-research`** skill via `Skill` and fold its
   cited findings into the brief.
3. If the question is really *"which library/gem/service should we adopt (or build)"* —
   a selection among external candidates, not prior-art — route to **`/select-tech`**
   instead of answering it here: it owns the hard filters, the hard-case probe, and the
   adapter-seam contract. Note the handoff in the brief.

Skip this phase entirely when the repo already answers the question.

---

## Phase 3.5 — Completeness check (before writing)

One deliberate pass before the brief: **which search angle did I not run, and could it change
the answer?** If a cheap angle (tests, config/flags, history) is unrun and could overturn a
"nothing exists" conclusion, run it now; otherwise name the gap honestly in the brief's Open
questions. A brief that silently covered only one angle reads as "covered everything" — that's
how duplicate implementations happen.

---

## Phase 4 — Write the feature brief

Use `Write` to create a **short** brief at the **Plans location from PROJECT.md**, using
its naming convention with a `-brief` suffix (e.g. `<plans>/<YYYY-MM-DD>-<slug>-brief.md`).
`Write` only **creates** this new brief — this skill carries no `Edit`, so it never
modifies existing source or specs (read-only on app code stands). Structure:

```markdown
# <Feature> — Discovery brief

- **Date:** <today>   ·   **Status:** Discovery

## Problem
<the framing from Phase 1: pain/gap, who, why>

## What already exists (repo)
- `path:line` — <existing implementation / similar feature, what it does>

## Reuse candidates
- `path:line` — <reusable function/module/component> — <how it would be reused>

## Searched but absent
- <what was searched, which angles/terms> — not found (justifies building new; saves re-search)

## External prior-art
<integration docs / deep-research findings, with sources — or "n/a">

## Open questions
- <unresolved decision that affects scope or design>

## Risks
- <risk> — <why it matters>

## Suggested route
<`/analyst` to write a spec | `/prepare` if scope is already clear> — <one-line reason>
```

Keep it short and factual. Every reuse/prior-art line carries a `path:line` (repo)
or a source URL (external).

---

## Phase 4.5 — Skeptic gate (optional, before the brief is queued)

When the brief will be **filed into the backlog rather than implemented next** — a speculative
idea, a bet on future demand, anything carrying a value claim rather than a defect — offer to
run the **`idea-skeptic`** agent on it before it is queued. It attacks the idea on four lenses:
economics at this project's real scale, supply (is there enough data/traffic/users to reach the
bar at all), claim honesty against `PROJECT.md`, and measurability of the bar and its
kill-condition on data the project owns today. Verdict: SURVIVES / KILLED /
SURVIVES-WITH-AMENDMENTS, and **amendments are binding** — write each one into the brief before
filing, or don't file it.

Skip the gate when the brief only reports what already exists in the repo (a reuse survey has no
value claim to attack), or when the work goes straight to `/prepare` and the real gate is
`plan-challenger` one stage later. Re-litigating a decision the project already made is not this
agent's lens — that is `finding-verifier` against the decision log.

---

## Phase 5 — Route onward

Recommend the next step and offer to chain it:

| Situation | Route |
|-----------|-------|
| Requirements still fuzzy; needs WHAT/WHY worked out | **`/analyst <brief-path>`** (write the spec) |
| Scope is clear and reuse is identified; ready for HOW analysis | **`/prepare <brief-path>`** |
| Hypothesis still risky / unproven | **`/spike`** (time-boxed validation) first |

State the recommendation with a one-line reason. If the user agrees, chain the skill
via `Skill`; otherwise hand off the brief path and stop.

---

## Hard rules

- **Read-only on app code.** No source edits, no spec, no plan, no implementation —
  the only file you create is the brief (`Write`, no `Edit`), at the Plans location.
- **Facts from PROJECT.md.** Plans location, architecture/module map, integrations,
  and domain vocabulary all come from the profile — never hardcode them.
- **Cite a repo path for every reuse candidate** and every prior-art claim; an
  uncited claim is a guess.
- **Stay short.** A brief, not a spec — framing, what exists, reuse, open questions,
  risks, and a route. The spec is `/analyst`'s job.

## Cross-reference

- **Next:** `/analyst` (spec) or `/prepare` (plan), per Phase 5.
- **Sidecar:** `/spike` to validate a risky hypothesis before committing.
- **External research:** the global `deep-research` skill (chained in Phase 3).
