---
name: which-skill
description: >-
  Router over the feature-flow kit — given a situation in plain words, recommend which kit
  skill (or short chain of skills) fits, and why. The map of the kit and the
  discover→analyst→prepare→implement flow, so you don't have to remember 20+ skills.
  TRIGGER when: the user asks "which skill should I use for…", "what's the right flow for…",
  "where do I start", "is there a skill for X", or describes a situation without naming a skill.
  TRIGGER ALSO (silent match) when the user states a concrete task and names no skill: a
  task-shaped request is not evidence that no skill fits, so check the catalog before running
  bare. Answer in one line and hand off — see "Silent match" below.
  DO NOT TRIGGER when: the user already named the skill they want (just run it).
allowed-tools: Read, Glob, Grep, AskUserQuestion
effort: low
---

# Which Skill?

Point the user at the right skill for their situation. Read what they're trying to do, match it to
the catalog below, and recommend the skill — or a short chain — with a one-line reason. When the
situation is genuinely ambiguous between two skills, ask one focused `AskUserQuestion` to
disambiguate; otherwise just recommend and offer to start it. If `/which-skill` is invoked with
no situation described, first ask the user what they're trying to do, then route.

## Silent match — when nobody asked for a router

You also fire on plain task requests that name no skill. That path must stay nearly free, or it
taxes every prompt:

- **One obvious match** → one line (`This is /close-epic — <reason>. Run it?`), then run it if the
  user agrees or the task is clearly the skill's own job. No catalog, no map, no phase list.
- **Two candidates** → one `AskUserQuestion`, two options.
- **Project skill** → a skill listed in `PROJECT.md` → `## Project skills` counts as a match too
  (see *Project layer* below).
- **No clear match** → say nothing about routing and do the work bare. A silent miss costs
  nothing; a paragraph about skills the user didn't ask for costs a turn.

Never make the user re-state the task after routing — carry it into the skill you name.

> **Maintenance:** every user-facing workflow skill should appear both here and in the kit repo's
> `guide/*/reference.md` "What's in it" table — keep the two in sync when a skill is added or removed. (This catalog
> deliberately omits `/which-skill` itself and the on-demand stack pack-reference skills like
> `/ruby-idioms`, so the two lists aren't byte-identical.) If unsure the list is current, `Glob`
> `skills/*/SKILL.md` and reconcile. Adding a skill the *model* may reach unprompted (no
> `disable-model-invocation`) also spends the shared skill-listing budget — check it against the
> caps in `skills/writing-skills/SKILL.md` § Platform caps on authoring before dropping the flag.

---

## First, the tier — how big is the thing they're holding?

Before picking a skill, size the input. Three tiers, three entry points; the routing mistake
this table prevents is pointing `/prepare` at a whole surface.

| Tier | The user is holding | Route to | Output |
|---|---|---|---|
| **1 · Program** | a whole *surface* to audit or map — "review every screen", "audit this area", output is plausibly 10+ separate pieces of work | **`/prompt-master`** (program pass) | ranked `00-report.md` + `evidence/` + `cards/NN-<slug>.md` + `RUN-ORDER.md`, stopping before any implementation |
| **2 · Epic** | one card, or one coherent change | **`/prepare`** | `00-overview.md` + `NN-<subtask>.md` in file-disjoint waves |
| **3 · Session** | one prepared subtask | **`/implement`** | code + implementation log + deviation report |

Tier 1 hands off to tier 2 one card at a time (`/prepare <program>/cards/NN-<slug>.md`).
A tier-1 pass never writes plans, and `/prepare` never authors a program.

## The pipeline (the spine)

```
/discover → /analyst → /prepare → /implement
research    spec        plan        build
```

- **`/idea`** — the plain-language front door *over* the spine, for a non-technical user (or
  anyone who just wants to describe an outcome): elicits the wish in outcome scenarios,
  shows 2–3 solution shapes with felt trade-offs, then drives the whole pipeline itself —
  owning every technical decision and reporting back in behavior terms.

- **`/discover`** — research prior-art & reuse before committing; scope a fuzzy idea. Read-only;
  writes a brief.
- **`/analyst`** — turn a raw idea into a spec via a structured interview (wraps `/grill`). Answers
  WHAT and WHY.
- **`/prepare`** — pre-implementation analysis: design alternatives, impact, SOLID/DRY,
  decomposition into parallel-safe execution waves. Answers WHETHER-READY and HOW.
- **`/implement`** — execute a prepared plan with deviation tracking, an architecture audit, and
  tests; every finding it hits is routed down one of four branches (fix · file a card · STOP and
  ask · hand to the sibling that owns the file), and the behavior check drives *this* slice only.
  May delegate a slice to `/tdd`.
- **`/scaffold`** — add a new module/component/command *modelled on an existing one*: exemplar
  first, placement from the profile, then every registration point wired and **proved by a
  command**. Use it when the artifact has to be registered somewhere to exist at all; a plan-sized
  change is still `/prepare`, a known edit is still `/implement`.

## Alignment & design (primitives the pipeline reuses)

- **`/grill`** — relentless one-question-at-a-time interview to pressure-test *any* plan before
  building. Standalone or invoked by analyst/prepare/spike/arch-health.
- **`/grill-with-docs`** — a grilling session that *also* builds the shared language: runs `/grill`
  while `/domain-model` records terms + ADRs inline. The high-leverage "align and document" combo.
- **`/domain-model`** — build the living glossary (`CONTEXT.md`) + ADRs; pin down terminology,
  record a decision. Run it alongside grilling to capture terms.
- **`/codebase-design`** — deep-module design vocabulary (small interface, big implementation,
  seams). Reach for it when designing or improving a module's interface.

## Explore a design before committing

- **`/spike`** — validate ONE risky hypothesis, yes/no, time-boxed, throwaway. *"Can X even do Y?"*
- **`/select-tech`** — choose a library/gem/framework/service (or decide to build it): hard
  filters → issue-tracker + hard-case probe on 2–3 finalists → scored matrix, ONE
  recommendation, adapter-seam integration contract. *"What should we use for X?"*
- **`/prototype`** — EXPLORE a design space: a runnable logic prototype, or several UI variations to
  compare. *"How should this look/behave?"* Many options, not one answer.

## Build & verify

- **`/onboard`** — fast comprehension of an *unfamiliar* codebase: run-it-first, one traced
  end-to-end flow, git-history archaeology (churn hotspots, bus factor, feared-old code),
  load-bearing-weirdness list → a written orientation map. Feeds `/bootstrap`.
- **`/api-design`** — design a public contract (endpoint/webhook/CLI/library API) before
  building: consumers & compatibility promise, resource model in domain language, the
  contract checklist (errors, pagination, idempotency, versioning), worked examples incl.
  errors, consumer's-eyes review. Internal seams stay with `/codebase-design`.
- **`/threat-model`** — design-time STRIDE-lite over a spec/plan that adds external surface:
  entry points × trust boundaries × forgotten actors (unauthenticated, wrong-tenant), abuse
  cases; every threat lands as an AC, plan step, or user-signed accepted risk. Post-build
  audits stay with `/audit-security`.
- **`/perf`** — measurement-first optimization: budget & metric → reproducible baseline →
  profile finds the real hotspot → biggest lever first, one change per re-measure → stop at
  the budget. Never optimizes unmeasured code.
- **`/tdd`** — drive new code test-first, red-green-refactor, vertical slices.
- **`/test`** — author tests for existing code, or audit/refactor a test suite.
- **`/test-spec`** — spec-first tests derived from a plan/spec *without reading the code*, so the
  spec is the source of truth (a failing test means the code is wrong). Sits between `/tdd` (no
  written spec) and `/test` (reads the module).
- **`/diagnose`** — root-cause a specific bug: reproduce → isolate → fix → verify.
- **`/code-review`** — review changed code for correctness/security/performance + conventions
  (review-only, no fixes).
- **`/refactor`** — apply quality cleanups to changed code (same behaviour), then format + test.
  The pair mirrors the built-in taxonomy: `/code-review` hunts **bugs**, `/refactor` (the kit's
  counterpart of the built-in `/simplify`) does **quality only** — route by which of the two the
  user actually wants, and never both for the same class of finding.
- **`/audit-quality`** — scoped architectural audit of a module or changeset: each file
  SOUND / SHORTCUT / HACK against *this* codebase's layer map and canonical patterns, behind an
  evidence gate (git log, callers, sanctioned exceptions, prior decisions) — plus a phased
  refactor plan with bugs split into Phase 0. *"Is this a hack or is it sound?"* Where
  `/code-review` hunts **defects in a diff** and `/arch-health` ranks debt across the **whole
  repo**, this one judges the **design of a scoped area**.
- **`/arch-health`** — periodic whole-codebase scan for shallow modules & ball-of-mud hotspots;
  ranks deepening opportunities and routes them.
- **`/clean-mvp`** — whole-codebase cruft sweep: dead code, unused files, legacy shims — with a
  proof-of-deadness evidence gate and batched delete confirmations.
- **`/sweep`** — mass mechanical migration across many files (rename an API, swap a library):
  complete site inventory → pilot batch → batched transform with per-batch verification → a
  zero-leftover re-scan; at ~30+ mechanical sites it writes an AST-based codemod instead of
  hand edits. Changes *live* things; `/clean-mvp` removes *dead* things.

## Architecture evolution (revisit what's built)

- **`/decompose`** — monolith vs modular monolith vs extracting a service, decided per
  boundary on evidence (real drivers vs the distributed tax; org facts asked, never
  guessed). Verdict STAY / MODULARIZE / EXTRACT, recorded as an ADR; extraction executes
  via `/rollout`. Governing rule: extract the seam before the service.
- **`/revisit`** — re-audit past decisions (ADRs, tech picks, undocumented load-bearing
  choices): extract each decision's assumptions, test them against today's reality
  (internal + live external research), verdict HOLDS / STRAINED (tripwire) / BROKEN
  (reopen → `/select-tech`, `/prepare`, `/decompose`). Assumption audit, not preference
  audit — no drive-by relitigation.
- **`/distill`** — mine the codebase's implicit conventions (error handling, construction,
  data access, test shape…), verdict each BLESS / UNIFY / BAN / DEEPEN with cited
  occurrences, install the verdicts as project rules / `CONTEXT.md`; migrations route to
  `/sweep`. Makes generated code copy the *best* pattern in the repo, not the most
  frequent one.

## Ship & learn

- **`/rollout`** — design the *strategy* for shipping a risky/irreversible change: expand-contract,
  strangler fig, feature flags / canary, versioned coexistence — a staged plan where every stage
  is deployable, verifiable, and reversible alone. *"How do we ship this safely?"*
- **`/deploy`** — *which* deploy command this change actually needs: classify the working tree
  against `PROJECT.md` → Deploy mapping, then name the **cheapest sufficient** command with its
  cost (a config edit does not buy a 5-minute rebuild), plus the post-deploy verification
  checklist and the rollback line. "No deployment needed" is a real answer. Commands are handed
  over as text, never run. Strategy for a risky change stays with `/rollout`.
- **`/preflight`** — release-readiness gate before shipping: full suite + lint, dependency &
  security quick pass, docs drift, config/migration check, behavior spot-check, changelog
  draft, and a GO / GO-WITH-RISKS / NO-GO verdict (deploy command suggested, never run).
- **`/incident`** — production is broken *right now*: triage → preserve evidence → mitigate toward
  known-good (rollback / flag off) → verify recovery → blameless review. The live-fire inversion
  of `/diagnose` (stabilize first, understand later); commands suggested, never run.
- **`/retro`** — the learning loop: mine archived plans' Deviation Reports, handoffs, and
  diagnose/arch-health reports for *recurring* patterns (≥2 cited occurrences, verified), then
  fold each confirmed lesson back into rules / PROJECT.md / CONTEXT.md / skills — with
  confirmation. Run after an epic or a rough week.

## Backlog & docs (local issue tracker)

- **`/to-prd`** — synthesize the current conversation into a PRD (no interview).
- **`/to-issues`** — break a plan/PRD into independently-grabbable vertical-slice issues (local
  files).
- **`/triage`** — move backlog issues through the triage state machine; answer "what's next".
- **`/epic-status`** — read-only dashboard over a wave-structured decomposition from `/prepare`:
  progress per wave, the next safe wave to launch, session-collision check, and the epic's
  `RUN-ORDER` read against the plans themselves — a `∥` mark is a claim, re-verified against the
  `Owns` sets, and any drift is reported rather than quietly fixed. Never writes.
- **`/close-epic`** — the terminal counterpart of `/epic-status`: verify every plan is terminal,
  then run the epic end-to-end — its declared `## E2E verify` block, or a battery *derived* from
  the surfaces the diff touched and disclosed as derived (drives delegated, verdict kept, one
  headline number re-derived by hand) — then plan↔code conformance + docs drift, a completeness
  critic, a **surface↔profile check in both directions** (dangling refs, *and* what the epic added
  that `PROJECT.md` / the rules / the docs never learned), small documentation debt fixed inline,
  pricing of every flagged follow-up against a closed list of consequence classes (default: a named
  known-undone clause, **not** a card) with only the survivors promoted into a **runnable board**
  (`<topic>-followups/` — cards + routed session prompts + RUN-ORDER, packed to the session context
  budget) and only when the open-debt stock allows a new one, a predicted-vs-actual ledger row, `## E2E
  results` written back into the epic overview, and a copy-paste archive command it never runs.
  **Takes a batch** — several epic paths in one invocation close per-epic under one agent budget.

## Security & dependencies

- **`/deps`** — dependency & vulnerability audit; proposes a safe upgrade path (propose-only).
- **`/audit-security`** — orchestrating OWASP-style security sweep that ties together the security
  rule, `/security-review`, the `security-reviewer` agent, and `/deps` into one risk-tiered report
  with a deploy verdict. (For a diff/PR-level check, use the `security-reviewer` agent directly.)

## Session & kit lifecycle

- **`/handoff`** — snapshot live state (done · next · decisions · files · how-to-verify) into a
  resume doc before a reset or handoff.
- **`/bootstrap`** — the front door: first install on a fresh project. On a project that's already
  adapted it hands off to `/update-kit` (never re-copies over your edits).
- **`/update-kit`** — any adaptation after the first install — a newer kit version *or* a re-adapt
  after structural changes. Stages the kit, 3-way merges (keeps your adaptations), re-adapts inline.
- **`/teardown`** — clean up kit leftovers or uninstall and restore.
- **`/prompt-master`** — compile an idea into a phased pack of self-contained, copy-paste
  prompts (research → spec → plan → implement → verify) to run in *other* sessions or with
  Opus/Sonnet-class models — instead of doing the work here and now. Also the **tier-1 home**:
  it authors the program pass (one orchestrator prompt, fan-out per phase, evidence files, a
  kill phase, then report + cards + RUN-ORDER — stopping before implementation), and emits a
  `Workflow` script for a deterministic pack. Emitted, never run: launching a workflow is the
  user's opt-in.
- **`/writing-skills`** — *(kit-internal)* reference for authoring new kit skills.

## Project layer (`PROJECT.md` → Project skills)

A project may carry its own skills next to the kit's — stack-aware deep passes, scaffolds for its recurring shapes. They are listed in `PROJECT.md` → `## Project skills`, never here: this file is kit-owned, and a project section pasted into it turns every `/update-kit` into a conflict on the router. When that section exists, read it before routing and treat its skills as part of the catalog. **Route by depth, not by name:** the kit skill is the general pass, the project skill is the deep pass over that codebase's own conventions — pick the one that fits the question, and never run both for the same one. The section's own notes (which kit skill each project skill deepens or replaces) win over this catalog. No section → there is no project layer; don't `Glob` for one.

---

## Matching guide (situation → route)

| The user says / wants… | Route |
|------------------------|-------|
| "Build a feature (start to finish)" | `/discover` → `/analyst` → `/prepare` → `/implement` → `/code-review`+`/test` |
| "I just want it so that… / user is non-technical / хочу вот так" | `/idea` (fronts and drives the whole pipeline in plain language) |
| "I have an idea but it's fuzzy" | `/discover` → `/analyst` |
| "Research / find out about X" | `/discover` (chains global `/deep-research` for open questions) |
| "Gather requirements / write a spec" | `/analyst` |
| "Poke holes in my plan / grill me" | `/grill` |
| "Grill me and write down what we decide" | `/grill-with-docs` |
| "What do we call this thing / our terms are a mess" | `/domain-model` |
| "Plan this before I build it / decompose it" | `/prepare` |
| "Build this approved plan" | `/implement` |
| "Add another module/command/adapter like the existing one" | `/scaffold` (exemplar + registration proved by command) |
| "Can X even do Y?" (one yes/no risk) | `/spike` |
| "Which library/gem/service for X / build or buy?" | `/select-tech` (then `/spike` if the winner carries a bet) |
| "Mock this up / which design looks better" | `/prototype` |
| "Build it test-first" | `/tdd` |
| "Add/clean up tests for existing code" | `/test` |
| "Test this against the spec / the plan says X" | `/test-spec` |
| "There's a bug / it's broken" (dev/CI, no live users bleeding) | `/diagnose` (then `/tdd` or `/test` to lock the fix) |
| "Production is down / users are hit RIGHT NOW" | `/incident` (mitigate first) → `/diagnose` (root cause after) |
| "How do we ship/migrate this safely / zero-downtime / feature-flag it" | `/rollout` (staged strategy) → `/prepare` → `/implement` per stage |
| "Review my changes / this PR" | `/code-review` |
| "Tidy / simplify / de-dup this code" | `/refactor` |
| "Where's the tech debt / what's rotting" | `/arch-health` |
| "Monolith or microservices / should we split X into a service — or merge two back" | `/decompose` (→ `/rollout` on EXTRACT) |
| "Is X still the right choice / we decided this long ago / why do we even use Y" | `/revisit` |
| "Make the code consistent / extract our conventions into rules / what patterns do we have" | `/distill` (unification → `/sweep`) |
| "New/inherited repo — разберись, как это устроено" | `/onboard` (then `/bootstrap` to write the profile) |
| "It's slow / optimize / reduce latency-memory" | `/perf` (budget → baseline → profile → fix → re-measure) |
| "Design this endpoint/webhook/public API" | `/api-design` (→ `/threat-model` if surface is external) |
| "What could go wrong security-wise with this design" | `/threat-model` (pre-code; existing code → `/audit-security`) |
| "Sweep out dead code / unused files / legacy shims" | `/clean-mvp` |
| "Rename/replace X everywhere / migrate all call sites / swap this library" | `/sweep` |
| "Are we ready to ship / release / deploy?" | `/preflight` |
| "What keeps going wrong / learn from the last epic / post-mortem" | `/retro` |
| "How should I design this module's interface" | `/codebase-design` |
| "Write up what we decided" | `/to-prd` |
| "Break this into tickets/work items" | `/to-issues` |
| "What should I work on next / sort the backlog" | `/triage` |
| "Where is this epic / what's the next wave / can I run these in parallel" | `/epic-status` |
| "This epic's done — settle and archive it" (one epic **or a list of them**) | `/close-epic` |
| "Turn what the close-out found into an epic with cards/prompts so we can finish it" | `/close-epic` (Phase 5b authors the board) — **not** `/prepare`, which takes one card at a time |
| "Are my dependencies safe" | `/deps` |
| "Security audit before deploy / full security sweep" | `/audit-security` |
| "I need to stop / hand this off" | `/handoff` |
| "Generate prompts for this idea / a prompt pack to run later or with another model" | `/prompt-master` |
| "Audit this whole surface / review every screen / map all of X and tell me what to fix" | `/prompt-master` (tier-1 program pass → cards) → `/prepare` per card — **not** `/prepare` on the surface |
| "Set up / remove the kit" | `/bootstrap` / `/teardown` |
| "Update the kit / pull a newer kit version" | `/update-kit` |

If the situation spans several rows, recommend the **chain** (e.g. *"`/diagnose` to root-cause,
then `/tdd` to lock it with a failing test"*) and offer to start the first step.

---

## End-to-end flows (when the situation is a whole journey, not one step)

When the user describes a **goal** rather than a single task ("build a feature", "refactor this",
"research X"), give the **whole route A→Z**, say where they are on it, and offer to start the first
step. Each kit skill also routes onward at its own end, so the flow self-propels — the user
confirms each handoff; nothing runs the whole pipeline silently.

- **Build a feature:** `/discover` → `/analyst` → `/prepare` → `/implement` → `/code-review` +
  `/test`. Run `/domain-model` alongside to capture terms/ADRs. Known/small change → start at
  `/prepare` or `/implement`; still fuzzy → `/grill-with-docs` first.
- **Research something:** `/discover` (repo prior-art & reuse; chains the global `/deep-research`
  for open external questions) → `/analyst` to turn findings into a spec.
- **Refactor / clean up:** *changed code* → `/code-review` → `/refactor`; *whole-codebase rot* →
  `/arch-health` → `/refactor` (small) or `/prepare` → `/implement` (large). `/codebase-design` is
  the shared vocabulary.
- **Requirements → backlog:** `/grill-with-docs` → `/analyst` → `/to-prd` → `/to-issues` → `/triage`.
- **Fix a bug:** `/diagnose` → `/tdd` or `/test` (lock it with a regression test).
- **De-risk a design:** `/spike` (one risk) or `/prototype` (compare options) → back into the pipeline.
- **Ship it:** `/close-epic` (settle the epic's plans) → `/preflight` (release gate: suite,
  deps/security, docs drift, changelog, GO/NO-GO) → deploy command from `PROJECT.md` (you run it).
  A risky/irreversible change gets a `/rollout` strategy *before* this — each stage then ships
  through the gate.
- **Production fire:** `/incident` (triage → preserve evidence → mitigate → verify recovery) →
  `/diagnose` (root cause) → `/tdd`/`/test` (regression test) → `/retro` if it's a repeat offender.
- **Learn from it:** `/retro` after an epic or a painful stretch — recurring lessons flow back
  into rules/profile so the same thing doesn't go wrong a third time.
- **Migrate mechanically:** `/sweep` (inventory → pilot → batches → zero-leftover re-scan);
  if judgment sites dominate, it's really a redesign → `/prepare` → `/implement`.
- **Audit a whole surface (tier 1):** `/prompt-master` authors the program pass (breadth sweep →
  lens passes → probes → adversarial kill → ranked report + cards + RUN-ORDER) → the user picks
  cards → `/prepare` per card → `/implement` per wave → `/close-epic`. The pass itself stops at
  cards; nothing is implemented from the report.

Pick the flow that matches, render it with the user's current position marked, and start step one.

---

## Hard rules

- **Recommend, don't run silently.** Name the skill (or chain) and the reason; let the user start it.
- **One disambiguation question max.** If two skills genuinely fit, ask once; otherwise just route.
- **Don't invent skills.** Only route to skills that exist in the catalog, in `PROJECT.md` →
  Project skills, or as a global built-in like `/deep-research`; if unsure the list is current, `Glob` `skills/*/SKILL.md` and reconcile.
  If nothing fits, say so and suggest the closest manual approach rather than inventing a `/skill`.
- **Stay in sync.** Every user-facing workflow skill appears here and in the kit repo's
  `guide/*/reference.md` — update both when the set changes (the router need not list itself or the pack-reference skills).

## See also

- **`/writing-skills`** — when the user wants to *add* a skill, not pick one.
- `guide/en/reference.md` (kit repo) — the same catalog in table form, kept in parity with this one.
