---
name: prepare
disable-model-invocation: true
description: >-
  Pre-implementation analysis — strategic brainstorm, impact mapping, SOLID extension
  checks, DRY reuse discovery, complexity tiering, and (for complex work) decomposition
  into an atomic, parallel-safe backlog. TRIGGER when the user wants pre-implementation
  analysis/decomposition before coding ("prepare", "analyze before building", "think
  through this", "decompose this task", "plan the work"). DO NOT TRIGGER when: the user
  already has a clear plan and just wants to build it → use /implement; the request is
  "add another <X> like the existing one" in a project that already has that shape →
  use /scaffold; or requirements are still unclear/ambiguous → use /analyst first.
allowed-tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, AskUserQuestion, Write, Agent
effort: high
---

# Pre-Implementation Analysis: $ARGUMENTS

Analyze BEFORE implementing. Do NOT write production code — only analyze, plan, and
(on confirmation) save decomposed plans. Previous step: `/analyst` (clarify requirements).
Next step: `/implement` (one invocation per subtask file).

**Input is one card / one coherent change — check the tier before Phase 0.** A whole-surface audit
or a program that plausibly yields 20+ cards ("review every screen", "audit this whole area") is
**tier 1**, and this skill is tier 2: run **`/prompt-master`**'s program pass first (breadth sweep →
`00-report.md` + `evidence/` + `cards/NN-<slug>.md` + `RUN-ORDER.md`, stopping before any
implementation), then come back here **one card at a time**. Decomposing a surface directly into
waves skips the discovery that decides which cards are worth cutting at all.

> **Risky work → suggest plan mode.** For a change the user flags as risky (production data,
> irreversible migrations, wide blast radius), recommend running the `/implement` session
> under Claude Code's built-in **plan mode** (plan approval before any edit) — it is the
> harness-level twin of this skill's plan-first pipeline: the kit plans the work, plan mode
> gates the execution. `/rewind` checkpoints add per-edit undo on top.

---

## Deliver, don't halt — ask only when the choice is material (governing rule)

This skill's job is to hand back the **finished analysis + plan**. An undertold detail must never
end the run at "tell me (a)/(b)/(c)". Sort every unknown into one of two buckets:

- **Material / irreversible / direction choice** — adopting a framework or major dependency,
  a one-way data migration, changing architectural style, anything expensive to undo
  (`core.md` → Decisions). → confirm via `AskUserQuestion`, **one at a time, each with your
  recommended answer**, before finalizing. (Unchanged.)
- **Undertold but cheap-reversible** — a threshold value, a default mode, a reject-vs-reprice
  behavior that can hide behind a flag, a config default. → **do NOT halt.** Adopt a sensible
  **reversible default**, name it explicitly as *your* assumption with its cost-of-undo, produce
  the full artifact anyway, and surface the alternative **after** the deliverable:
  *"I assumed X (reversible via `<flag>`; default `0.0` = off); say so if you want Y."*

The clarifying question rides **alongside** the delivered plan, never **instead of** it. If a
default lets you finish, finish — then offer the choice. Halting a whole analysis on a question a
default could unblock is the failure mode this rule exists to kill.

**Raw idea, not a spec, is valid input.** If `$ARGUMENTS` is a plain text idea (not an `/analyst`
spec or spec file), don't demand a spec — crystallize a 3–5 line working spec inline (goal, scope,
known parameters + their reversible defaults) and proceed through the phases on it. Ask at most the
1–2 genuinely material questions; default the rest and deliver.

---

## Phase 0 — Load Profile (MANDATORY FIRST)

**Tooling preflight — one call, before step 1.** Some tools this skill relies on are **deferred**
by the harness: the session lists them by name only and loads their schemas on demand, so calling
one before it is fetched fails. Listing a tool in `allowed-tools` does **not** un-defer it. Issue
a single `ToolSearch` up front covering the whole run — `select:WebFetch,WebSearch,SendMessage`
(Phase 1's external-service docs check, continuing a design-panel agent in 2.5) — instead of
one round-trip per discovery. A name already loaded costs nothing to include; a schema discovered
missing mid-run costs a turn.

1. Read `.claude/PROJECT.md`. It is the single source of project facts:
   **Commands** (lint/test/typecheck/run), **Architecture** (layers/modules, boundaries,
   backlog/plans location), **Integrations** (external services), **Conventions**.
2. Read applicable `.claude/rules/*` — select rules whose `paths`/scope match the files
   this change will touch. These define the project's invariants and patterns.
3. If `CONTEXT.md` exists, read it — name modules, entities, and the plan in the project's
   **ubiquitous language**, and respect any ADRs in `docs/adr/` touching the area.
4. **If `PROJECT.md` is missing or still a TEMPLATE** (placeholder markers, unfilled
   sections) → fall back to the root `CLAUDE.md` (always in context) when it carries the
   commands/architecture/integrations above — proceed on it, noting you're running
   without a kit profile. Only if *neither* has those facts, STOP and tell the user to
   run `/bootstrap` first.
5. **If `$ARGUMENTS` is an `/analyst` spec, check its stage gate on entry**
   (`rules/_generic/planning-artifacts.md` → Stage gates): ACs falsifiable with concrete
   examples, unhappy paths per US, assumptions/open questions listed. A failing spec goes
   back to `/analyst` with the missing items named — don't silently compensate by inventing
   the missing requirements here.

All commands, paths, layer names, and external services below come from `PROJECT.md`
and installed rules — never hardcode them.

---

## Phase 0.5 — Evidence to Gather (read the code BEFORE brainstorming)

Do not brainstorm blind. Gather evidence FIRST, as a checklist of stack-neutral commands
(runner/paths come from `PROJECT.md`, never hardcoded) — Phases 2–2.5 must rest on what the
code actually is, not on assumptions:

- [ ] Read the **adjacent files** you expect to touch (from `PROJECT.md` → Architecture and
      `CONTEXT.md`) + their doc comments — understand the shape before proposing changes.
- [ ] `git log --oneline -15 -- <each file likely to change>` — why it looks this way; prior
      attempts. Use `git blame` / `git log -p` on the specific lines when history matters.
- [ ] Grep the codebase for the feature's key nouns/verbs — is there an existing impl to reuse
      or extend? (feeds Phase 5.2 DRY.)
- [ ] Check the **backlog / plans location** (`PROJECT.md` → Plans / backlog) for a prior or
      in-flight plan on this topic — don't re-decompose something already planned or shipped.
- [ ] Note the applicable `.claude/rules/*` for the paths you'll touch (feeds Phase 5.3).

**No planned edit to unread code (hard rule).** Every file the plan will modify must have
had its relevant region **Read in this session** before the step is written, and every
signature/type/route/config key a step builds against is **quoted verbatim in the plan**
next to the step (so `/implement` codes against the real shape, not the plan's guess).
"We'll check the details during implementation" is banned — it is the exact sentence that
becomes a mid-build surprise, an improvised architecture decision, and a changed plan.
When the file list is too large to read whole, read the regions the steps touch and say
which regions were read; delegate wide reconnaissance to an Explore-type agent and
spot-check its load-bearing citations (`delegation.md`).

---

## Phase 1 — External-Service Check

If the feature touches any external service listed in `PROJECT.md` → Integrations:

1. WebFetch the official API docs for that service (URL from the Integrations entry or
   the matching rule). WebSearch if the doc URL is unknown.
2. Record exact endpoints, request/response fields, auth model, error codes, rate limits.
3. Note breaking changes vs. the current integration; fold API complexity into the estimate.

Skip entirely if no listed integration is involved.

---

## Phase 2 — Strategic Analysis (Brainstorm)

Think the idea through before touching code. Challenge assumptions, explore alternatives.

| Question | Answer |
|----------|--------|
| What problem does this solve (concrete pain/gap)? | |
| Who benefits (user / operator / developer / system)? | |
| Expected impact — quantify if possible? | |
| Simpler 80/20 approach or existing solution? | |
| Minimal viable version — smallest useful slice? | |
| Trade-offs given up (simplicity vs. flexibility, speed vs. correctness)? | |
| Risks, unknowns, assumptions to validate? | |
| In scope · out of context (another part owns it) · in context but out of scope (ours, deferred)? | |
| Definition of done + acceptance criteria? | |
| Future implications — enables what, locks out what? | |
| Horizon — throwaway probe / internal tool / living surface, and the next two plausible features? (operator-confirmed, from the spec or one question — `core.md`) | |

**The two out-buckets differ.** *Out of context* leaves an integration edge the steps must
call and Phase 4 must map; *in context, out of scope* stays in the vocabulary. The filter
runs both ways — it also names a core concept nobody has.

If an answer is unknown AND **materially** blocks the analysis (a choice expensive to undo), ask via
AskUserQuestion. Otherwise adopt a **named reversible default** and continue — see *Deliver, don't
halt* above. Never stall the whole brainstorm on a question a default could unblock.

---

## Phase 2.5 — Design Alternatives & Assumptions to Confirm

### 2.5.1 Design alternatives (2–3 viable approaches + trade-off table)

Do not commit to one path implicitly. Generate **2–3 genuinely different** viable approaches —
extend-in-place · new-abstraction · buy/reuse-existing · delegate to a layer you already run ·
cordon off — comparable in *kind* and at one level of granularity, then
score them (a "buy" approach that needs an external library/service *chosen* routes
through `/select-tech` — its verdict and adapter seam come back as plan steps) — a lightweight, single-agent adaptation of the multi-approach pattern. A
"new-abstraction" approach must justify itself as a **deeper module** (small interface, more
behaviour hidden) — invoke `/codebase-design` for that lens, not just "more files".

**New seam → design first.** If the change introduces a new module / seam / abstraction, run
`/codebase-design` **before** committing to the decomposition, per the Artifact-Continuity
Contract (`rules/_generic/planning-artifacts.md`) — a new abstraction is justified as a deeper
module, not accepted as more files.
Whether that seam is due yet, and along which axis, is `skills/codebase-design/WHEN-TO-CUT.md`;
when the alternatives differ in *shape* (function or class, a subtype, a pattern), `SHAPE.md` beside it.

**Row A is the least-machinery option** — extend what exists, a config change, the framework
default, or do not build it. A row above A is earned by naming the point at which A fails: the
input, load, or requirement it cannot carry ("it won't scale" is not that point). A minimal
recommendation ships labelled: its failure point and the number at which it stops being enough.

**Complex reads climb one step at a time, each with its price named:** the repository you have →
a query through the mapper → hand-written SQL on the read path (legitimate; the mapper is
justified per path, not per project) → a denormalised table → a store fed by events.

**The two rungs that get skipped.** *Delegate to a layer you already run* — a proxy, gateway or
broker that can log, throttle, retry or route for you, often by configuration and no code; when
it does not fit, write the line saying why. *Cordon off* — when the plan must touch code too
tangled to clean now, draw the boundary where coupling is weakest, force everything crossing it
through one named interface, and record where the pile now lives. A "rewrite it first" row is
legitimate after a post-mortem of what the old code does well and two cheaper options priced.

**Size the problem before you name a component.** Write the arithmetic first — rows · bytes ·
peak requests/s · the working set that must stay hot — and name the fattest real row. Settle the
shape of the stored data and its access patterns before the module layout. The estimate has veto
power: if it all fits one server, drop the cache and leave the number.

**Before you add a hop, multiply.** Four synchronous dependencies at 99.5% are 97.5% together,
and it is blocking on the answer that costs — request/response over a queue multiplies the same
way, and a timeout changes the failure mode, not the product. Answer first and finish the rest
behind an outbox when the promise can be weakened. Price the hop in the same breath: p95/p99
round-trip (never the average), hops per user action, bytes crossing versus bytes actually used.

**At most three driving characteristics, unranked** — ranking the full list never converges. Cap
the drivers at three and demote every other quality the user named into ordinary requirements,
never drop them. Two tests each: if one had to go, which; and does it force a module, service or
seam that hygiene inside the existing shape would not? If the winning approach is a day of CRUD
while the spec calls the area differentiating, that mismatch is a finding, not a step to take.

| Approach | Effort | Risk | Reversibility | Fit-to-architecture | Notes |
|----------|--------|------|---------------|---------------------|-------|
| A — <name> | low/med/high | low/med/high | undo: <mechanism, cost> | aligns / strains layers (per PROJECT.md) | <key trade-off> · prerequisite: <what must already hold, or none> |
| B — <name> | | | | | |
| C — <name> | | | | | |

**Notes carries the prerequisite** — the condition that must already hold for the approach to
be legitimate — or the word `none`; an unverified prerequisite is an assumption and goes to
§2.5.2 before it can be recommended. **Score on the failure branch:** two options that look
equally simple until something fails have not been compared — say what each does on a partial
failure and on a step that succeeded and must be undone. **A winner overlapping an incumbent**
carries two commitments: a step retiring the old one, and the named way back.

Then state a **recommendation with reasoning** — which approach and *why* it wins on
the columns that matter for this change. If the trade-offs are close or the choice is
genuinely the user's (cost vs. flexibility, speed vs. correctness), surface it via
`AskUserQuestion` rather than deciding silently. **Direction decisions are always the
user's**: adopting a framework/major dependency, hand-rolling past the trajectory test,
or changing architectural style gets recommended + explicitly confirmed, never taken
silently (`docs/decision-craft.md` §8).

**Judge panel (Complex tier, wide solution space — design-it-N-times).** When the change is
Complex AND the approaches genuinely diverge (different seams, different data models — not
three flavors of one idea), upgrade DESIGN-IT-TWICE to a panel instead of scoring the table
yourself:

1. **Generate** — spawn 2–3 Agents in parallel, **synchronously**
   (`run_in_background: false`), each
   designing the solution from ONE assigned angle: *MVP-first* (smallest useful slice),
   *risk-first* (kill the scariest unknown first), *user/domain-first* (model the domain
   cleanly, per `/codebase-design`). Each returns a sketch: seams, touched files, trade-offs.
2. **Judge** — spawn 1–2 judge Agents in parallel (**synchronously**, same reason), blind to
   each other, scoring all sketches on the table's columns (effort · risk · reversibility ·
   fit-to-architecture, per `PROJECT.md`) **plus each sketch's prerequisite and what it does on
   the failure branch**, each returning a ranked verdict with reasons.
3. **Synthesize** — you (not an agent) build the recommendation from the winner, grafting in
   any runner-up idea the judges scored higher on a column that matters. Record what each
   losing approach contributed or why it lost — that reasoning is what makes the plan
   defensible later.

**Why synchronously, and not "background; collect on notification":** `/prepare` is routinely
dispatched into a subagent — the session then holds zero assistant records and this entire
skill runs in `subagents/`. A subagent **never receives** a background agent's completion
notification (`delegation.md`; measured 0 of 18 across the archive) — it is routed to the root
session and arrives after this run is already dead. A backgrounded panel here is launched and
abandoned: you will wait for a message that cannot come, then re-derive the answers by hand.
Take the block.

One attempt iterated beats a panel when the space is narrow — don't panel a config change.
For a merely "complex enough" comparison with one plausible shape, a single scoring Agent
still suffices.

**Optional upgrade the *user* can run: this panel as a deterministic `Workflow`.** Generate →
judge → synthesize is a fixed fan-out shape, and the harness can run it as a script with each
sketch and verdict returned against a `schema` instead of as prose. Two limits, both hard:
(1) **user-opt-in only** — a workflow runs on the user's explicit ask, never on this skill's
initiative, so mention it in one line and run the agent panel above if they don't take it;
(2) **read-only fan-out only** — it qualifies because the agents read source and return *designs*,
with no file edited inside; the recommendation is still synthesized here, in this session, where
the user can push back on it. See `rules/_generic/delegation.md` → *Deterministic fan-out*.

### 2.5.2 Assumptions to confirm (common-ground)

List the **assumptions** the analysis rests on that the user should validate **before**
implementation — misaligned assumptions caught here are cheap; caught in `/implement`
they are not. Cover: requirement/scope assumptions, data/state assumptions, integration
behavior, and "we'll reuse X" bets.

| # | Assumption | If wrong → impact | Confirm? |
|---|------------|-------------------|----------|
| A1 | <what we are taking as given> | <what breaks / re-plans> | user / verified-in-repo |

When an assumption is **material** (getting it wrong changes the chosen approach or
scope), confirm it via `AskUserQuestion` before finalizing — apply the `/grill` discipline here:
one question at a time, each with your recommended answer, never a batch. Assumptions verified
against the repo (cite `path:line`) need no question — mark them verified.

**An unvalidated material assumption becomes a spike step, not a hope.** If, by the end of
this phase, a material assumption is neither user-confirmed nor repo-verified (typically a
framework/library behavior claim — see the Artifact-Continuity Contract's
ASSUMPTION-TO-VALIDATE), it must not survive as a bare table row: add an explicit **`/spike`
validation step to the plan, scheduled before anything that builds on it** (wave 0 / first
wave — risk-first). The Phase 7 gate fails while a material assumption dangles unrouted.

---

## Phase 3 — Complexity Tier

Estimate size to decide whether decomposition (Phase 6) is required. Thresholds are rough
guidance, not hard rules — adjust to the project's grain.

| Tier | Rough size | Decomposition |
|------|-----------|---------------|
| **Simple** | 1–2 files, < ~200 LOC, single layer | Skip Phases 5–6 |
| **Medium** | 3–5 files, ~200–500 LOC | Phase 6 optional |
| **Complex** | 5+ files, 500+ LOC, or crosses layers/modules | Phases 5–6 **required** |

**Tier measures size; this check measures *count*.** One plan carries **one intent you can state
in a single sentence**. If you cannot, you are holding several changes — and Complex is the wrong
answer to that: decomposition splits one intent into waves, it never fuses three intents into one.
Any of these signs means split first, then run this skill per piece:

- the scope reads as a list of unrelated features joined by "and";
- reviewing the result would take the operator half a day — so nobody will review it;
- two people could not work on it without colliding, even across different files;
- a good half of it could ship on its own and still be worth shipping.

(Splitting into ≥2 plans is different from tier 1 above: that is a whole surface to be swept by
`/prompt-master`; this is a handful of separable changes you can name right now.)

---

## Phase 4 — Impact Analysis

Map the blast radius using `PROJECT.md` → Architecture (its layer/module model and
boundary rules) — do not assume any particular framework's layout.

1. **Directly modified**: list every file that will change.
2. **Ripple effects — three sources, not one**: files that import from or depend on the
   modified files; files git shows changing in the same commits (`git log --format=%H
   --name-only`, grouped by commit — copy-paste, shadow contracts and paired configs are
   invisible to the import graph); and effects travelling by mutation of arguments or writes
   to module-level state, which no signature shows. Cite it; do not turn it into a rule.
3. **Layer / module classification**: place each affected file in the project's layers or
   modules as defined in `PROJECT.md`. Flag any boundary crossing and its direction.
4. **Boundary integrity**: will the change introduce an import/dependency that violates the
   project's declared boundary rules (from `PROJECT.md` or a boundaries rule)?
5. **Cross-module**: does it span more than one module/context? If so, does it go through
   the sanctioned interfaces?
6. **Moving parts**: for each queue, cache, worker pool, replica or external provider the
   change introduces or leans on, write one line — what the system does while it is down. A
   part you cannot write that line for is the single point of failure you just found.
7. **Readers outside this repository**: when the change alters the shape, owner or location of
   stored data, name who else reads it — analytics, exports, another team's scripts — and how
   that was checked; the import graph cannot see them.

---

## Phase 4.5 — Agent Validation (Complex tasks, optional)

> **Spawn contract — the whole skill, every phase.** `/prepare` is itself routinely dispatched
> into a subagent, and a subagent **never receives** a background agent's completion
> notification (`delegation.md`; measured 0 of 18 across the archive — it is routed to the root
> session and lands after this run is already dead). So **every** Agent this skill spawns — the
> judge panel, the validators below, the challenger, any one-off probe — goes out with
> `run_in_background: false`. A background spawn here means launched-and-abandoned: the work
> gets done, gets paid for, and is lost, while you wait for a message that cannot arrive.
>
> Observed 2026-07-29, after the first half of this fix shipped: a `/prepare` run spawned four
> background `Seam analysis` agents from this very phase and collected none of them — their
> reports never appear in its transcript. Its challenger, spawned synchronously, came back fine.

For a **Complex** plan, you MAY delegate validation to the kit's agents before decomposing
(**synchronously**, per the contract above; model comes from each agent's own frontmatter —
never pass or assume one):

| Agent | Launch when | Checks |
|-------|-------------|--------|
| `deep-analyzer` | new abstraction/interface, hot paths, or significant refactor of existing code | logic-level architectural issues, concrete refactoring |
| `arch-tracer` | the plan crosses layers/modules (per `PROJECT.md` → Architecture) | no new boundary/layer violations introduced |
| `security-reviewer` | the change touches an external API, the datastore, or credential/config handling | secrets, injection, unsafe patterns |

**New/changed external surface with no threat model yet** (endpoint, webhook, upload,
auth change — and the spec carries no threat-model table): run **`/threat-model`** before
decomposing — its mitigations become plan steps here, at paper price.

**Integrate findings** — after agents report, fold them into the plan: add prep steps, adjust
the complexity estimate, flag blocked dependencies.

---

## Phase 5 — Extension Readiness (SOLID) + Reuse (DRY)

### 5.1 SOLID — is the code ready to receive the change cleanly?

| Principle | Check | Issue? |
|-----------|-------|--------|
| **Open/Closed** | Can we ADD code without modifying working code? | |
| **Single Responsibility** | Will any unit gain a second *actor* — another role asking for its changes — or exceed the project's size limits? | |
| **Dependency Inversion** | Does new code depend on abstractions — declared in the caller's module, not beside the implementation — or on concretions? | |
| **Interface Segregation** | Will any interface/component grow fat with unrelated members? | |
| **Liskov Substitution** | Do existing implementations/consumers still conform? | |

If existing code must be modified to extend it, list the abstractions to introduce FIRST.

### 5.2 DRY — find what already exists before writing new code

- Grep for keywords related to the feature across the codebase.
- For each shared location named in `PROJECT.md` → Architecture (shared/utility/helper
  layers, common components, domain types), check whether the needed thing already exists.
- Find the closest existing pattern to replicate (so new code matches house style).

**Vet the exemplar.** The closest existing pattern is a **candidate, not an authority** — read it
before copying. If it hardcodes what your change must configure, skips the layer your change needs,
or is the only instance of its shape, pick a different exemplar and say why. Replicating a bad
pattern spreads it and makes the review defend it as consistency. This does not contradict
`core.md` → *rewrites regress to the mean*: an odd pattern is **left alone where it is**
and **not chosen as the template** for new code — don't normalize surprising code, don't propagate
it either.

**Extract-before-implement**: logic duplicated across 2+ places that both old and new code
will need — extract to the shared location FIRST, then build on it.

**An abstraction's approval expires.** Before extending a shared unit, count the switches that
pick a branch for one caller rather than express a real variation in the domain. A requirement
the current shape fits *almost* perfectly is the danger sign; plan both options with costs.

### 5.3 Rules Checklist (assembled from INSTALLED rules)

Build this table at runtime from the files in `.claude/rules/` that apply to the touched
paths. One row per applicable rule — do not invent rows for rules that are not installed.

| Rule (file) | What it enforces | Plan complies? |
|-------------|------------------|----------------|
| `<rules/...>` | `<one-line summary from the rule>` | |

---

## Phase 6 — Decomposition (Complex tasks only)

Break complex work into atomic, **independently committable** subtasks saved to the
project's backlog/plans location (from `PROJECT.md` → Architecture). Make subtasks
**parallel-safe by default**: group into *waves* where every subtask in a wave owns a
**disjoint** file set. (This is the *execution* decomposition — file-ownership waves. Breaking a
PRD into product-level vertical-slice **issues** is `/to-issues`; one of its slices can feed this.)

**Full model + templates:** the canonical wave model, the `Owns`/`Reads`/`Shared-edits`
ownership contract, the wave-safety check, the backlog file layout, and the overview /
subtask / per-session-brief / wave-schedule / file-ownership-matrix templates all live in
[`reference/parallel-wave-execution.md`](reference/parallel-wave-execution.md). Read it
before decomposing and use its templates verbatim — the model below is the gist.

### 6.1 Per-subtask sizing

Three things bind first: each subtask is **independently committable**, **reviewable by the
operator in one sitting**, and owns a **disjoint file set**. Then context, stated concretely: the
subtask must be projected to stay **under ~200k of session context** — if its file set alone
approaches that, it is two subtasks. It also declares its dependencies and states its verification
method (unit-testable pure logic vs. manual/integration check). Aim for a small, coherent slice
(roughly a session's worth of changes plus tests), not a mega-task.

> The number is explicit because nothing warns you anymore. On a large-window model there is no
> compaction event to signal that a session outgrew itself; past ~200k, recall of mid-window detail
> degrades and every further turn re-reads the whole prefix (`core.md` → Context
> economy). Sizing "with margin" against an invisible ceiling is not a constraint.

**Plan the verification before the change (reverse planning).** Every subtask — and every
ordered prep step — carries a `Verify:` line: the command to run or the behavior to observe,
and the expected result ("run `<test:targeted> <path>` → new cases green", "hit `<route>` →
response contains `<field>`"). A step whose completion cannot be observed isn't a step, it's a
hope — and `/implement` executes these lines instead of inventing its own definition of done.

**An increment is a whole abstraction, not a slice of one.** Growing one mechanism across three
phases makes every intermediate version special-purpose, and "generalize it later" is the step
that gets cut: merge the phases, or say why the intermediate version earns its own review.

### 6.2 Wave & ownership model (gist)

Declare for every subtask: **Owns** (files it exclusively edits), **Reads** (read-only),
**Deps** (subtasks that must finish first), **Shared edits** (hot files touched by 2+
subtasks). Rules:

- Within one wave, `Owns` sets are **pairwise disjoint** — no two concurrent sessions ever
  write the same file.
- Files in a shared/hot set get exactly **one wave-owner**; other subtasks touching them go
  to a later wave (this defines the serialization *spine*).
- A subtask that must run alone (broad refactor, hot-file hub, gated final) is **Solo** —
  its own single-task wave, with `Solo: YES — <reason>`.
- **Risk-first scheduling.** Dependencies permitting, the subtask carrying the most
  unvalidated assumptions or the novel integration goes into the **earliest** wave — bad news
  must arrive while re-planning is cheap, not after three waves built on top of it. For a
  cross-layer feature, make wave 1 a **walking skeleton**: the thinnest end-to-end slice that
  proves every seam works, which later waves flesh out.
- **Interface-first steps.** When later subtasks build against a new module/seam, add an early
  step that pins its public contract (signatures, types, error behavior) so parallel sessions
  code against a stable interface instead of guessing at one. A hook placed for a later wave
  says what wave 1 ships if that wave is cut — otherwise it moves into the wave that uses it.
- **Model hint per row — state it, don't leave it ad-hoc.** Recommend the **strongest available
  model** for a subtask that is irreversible, touches a server-side or live-signal path, or carries
  a wide blast radius; the **default model** everywhere else. Record the hint in the wave schedule
  (and in the RUN-ORDER row where one exists) so whoever launches the parallel sessions doesn't
  re-derive it per session. It is advisory — the operator picks the launch model.
- Before saving, run the **wave-safety check** (mandatory — see the companion). If it fails,
  re-wave.

### 6.3 Saving the backlog — and what the output file is called

Write the decomposition to the backlog/plans location using the file layout and templates
from [`reference/parallel-wave-execution.md`](reference/parallel-wave-execution.md):
`00-overview.md` + one `NN-<subtask>.md` per subtask + `implementation-prompts.md`
(per-session briefs, grouped by wave). **Confirm with the user before creating any files.**

**Name the output for the case you are actually in.** The file name is a contract that downstream
skills key on, so every plan — decomposed or not — states where it was saved and under what name:

| Case | Files |
|------|-------|
| **≥2 subtasks** | `00-overview.md` (the index) + one `NN-<subtask>.md` each + `implementation-prompts.md` |
| **One plan, no wave to cut** — Simple/Medium tier, or Complex with a single dominant file | `<backlog>/<task-name>/plan.md`, or `NN-<slug>.md` if it came from a numbered card. **Never `00-overview.md`.** |

`00-overview.md` is written **only** when there are ≥2 subtask files for it to index. A step list
saved under that name misdescribes itself: `/epic-status` and `/close-epic` both read
`00-overview.md` as the wave map, and the next reader — human or model — opens it expecting an
index and finds steps.

**Parent RUN-ORDER — read it if it exists, never require it.** Walk up from the backlog path toward
the program directory looking for `RUN-ORDER.md` (the artifact is described in the companion):

- **Found** — this plan came from a program (tier 1: a `/prompt-master` program pass authored the
  cards and that RUN-ORDER; this run is one card of it). Read its row: inherit the row's **Mode**, **Model**,
  and wave position rather than re-deriving them, and **propose** a Status update in your report
  for the operator to apply. Never write into `RUN-ORDER.md` yourself — it has exactly one writer.
- **Not found, and this epic alone decomposes into >1 wave** — *offer* to emit one from the
  companion's template. Create it only on confirmation.
- **Not found, single wave** — proceed exactly as before, and say nothing about it. Absence is the
  normal case for a standalone epic, not a gap to report.

### 6.4 The E2E-verify block (any decomposed epic — mandatory)

`00-overview.md` carries a `## E2E verify` block written **now**, before any code exists — template
in [`reference/parallel-wave-execution.md`](reference/parallel-wave-execution.md). `/close-epic`
executes it row by row and writes the observed values back beneath it.

- **Written before implementation**, for the same reason as the per-step `Verify:` lines: a check
  invented after the fact is written to pass.
- **Checks are specific to this epic's own claims**, never a generic checklist ticked at close.
  *"Badge counts stay byte-identical across the mode boundary"* is a check; *"the UI works"* is not.
- **Baseline captured here, at prepare time** — the value, the command that took it, and the
  machine. A close-out pass cannot recover a baseline the change already destroyed. If it genuinely
  cannot be taken now, the block says so and that row's Expected column is qualitative.
- **Surfaces and drive methods come from `PROJECT.md`** (→ Architecture for what the epic touches,
  → Commands for how each surface is driven) — never hardcode a tool, a URL, or a host here.
- **Blocking vs informational, marked per row.** A failing non-blocking row becomes a follow-up
  card, not a blocked close.
- **A live-signal path is not driven to "verify" it.** State the blast radius and leave the call to
  the operator — that is the one surface where the check itself is the risk.

---

## Phase 7 — Quality Gates (before finalizing ANY plan)

### Completeness
- **If the input is an `/analyst` spec** (requirements numbered `US-1..n`, acceptance `AC-n`):
  include an explicit mapping table — one row per user story:

  | US-ID (from the /analyst spec) | Plan step(s) | Its ACs → step |
  |--------------------------------|--------------|----------------|
  | US-1 | Prep step 2 · subtask 03 | AC-1 → step 2 · AC-3 → subtask 03 |

  Every US-ID must appear; **a user story with no plan step FAILS the gate** — add the step,
  or mark it explicitly out-of-scope with user sign-off. **Every AC of that story too**, in the
  third cell, each pointing at a step: the happy path gets a step, the expired token does not,
  and the row still looks covered — that gap is what the column is for. An AC with no step is
  fixed or signed off out-of-scope exactly like a US.
- **No `/analyst` spec:** fall back to the self-check — every requirement from the user
  request maps to a step.
- [ ] Each file to modify is listed with a SPECIFIC change.
- [ ] Edge cases and integration points are addressed.
- [ ] **Decomposed epic:** `00-overview.md` declares its `## E2E verify` block (Phase 6.4) with at
      least one **blocking** row and a **baseline captured now** — or an explicit statement of why
      the baseline could not be taken. A block with no blocking row fails this gate.
- [ ] **The plan's file name matches its shape** (Phase 6.3) — `00-overview.md` only when ≥2
      subtask files index under it.
- [ ] **Production visibility**: the plan names the attributes or events the change adds and the
      exact query you will run after deploy — is it doing what I expected, how does it compare to
      the previous release, is anyone using it, is anything abnormal. A change nobody can see in
      production is not planned; if the attribute does not exist yet, adding it is a step.

### Plan challenge — the implementation that hasn't happened yet
**Mandatory for Complex tier (recommended for Medium):** launch the **`plan-challenger`**
agent on the draft plan — a fresh context briefed to hit, on paper, every wall
`/implement` would hit at full price: steps resting on unread code, guessed interfaces,
missing cases/migrations, ripples outside the impact map, unowned assumptions. It has the
plan but not your rationalizations — that asymmetry is the point (author blindness,
`core.md`).

**Launch it once, and synchronously.** Before spawning, check whether a challenge of this
same plan is already in flight — announcing "the mandatory final gate" is not proof you have
not already run it. One archive run announced that line twice, five minutes apart, and
spawned two challengers on the same plan; they overlapped, the second's findings arrived into
a plan already rewritten from the first's, and both had independently found the same two
BLOCKERs. The redundant run cost 36,905 output tokens and settled nothing. A gate you have
already dispatched is not a gate you may dispatch again — wait for the one in flight.

Route every finding before finalizing: **BLOCKER** → fix the plan or add the spike/step
now; **GAP** → fix, or take to the user if it changes scope; **NOTE** → fix or explicitly
accept. The gate fails while a BLOCKER stands. Record the verdict + routing in the plan
("Challenged: N findings → M plan changes, K accepted") — a challenge that changed nothing
in a non-trivial plan deserves suspicion, not celebration.

### Pre-mortem — assume it already failed
Run prospective hindsight on the finished plan (`rules/_generic/core.md`):
*"it shipped; it failed; it's three months later — what was the cause?"* Write the **top two
causes**, and route each one into the plan as exactly one of:
- a **probe run now** — if the cause is checkable today (one grep/query/docs fetch), check it
  before the plan is finalized;
- a **plan risk with a `Verify:` line** — if it's only observable during/after execution;
- a **restructure** — if the cause is catastrophic, change the door: isolate the one-way step,
  add a flag/backup stage, or route the step through `/rollout`.

A pre-mortem that changes nothing in the plan was theater — the gate row states which of the
three each cause became.

### Anti-vagueness — REJECT and rewrite vague steps
| Vague | Specific |
|-------|----------|
| "Implement feature X" | "Add `fn()` to `path:LINE` returning <type/range>" |
| "Update the config" | "Set `<key> = <value>` in `<config>` at `path:LINE`" |
| "Handle edge cases" | "Return <value> when `<condition>` in `fn()` at `path:LINE`" |
| "Add error handling" | "Wrap `<call>` in try/except for `<error>`, retry/log as <policy>" |

### Actionability — every step answers all four
1. **WHERE** — file path + line/function. 2. **WHAT** — exact change. 3. **HOW** — enough
detail that `/implement` never has to decide. 4. **VERIFY** — the observable check proving the
step landed (see Phase 6.1's `Verify:` line — applies to non-decomposed plans too). All
decisions are made HERE.

---

## Phase 8 — Artifact continuity (before you finish)

Per the Artifact-Continuity Contract (`rules/_generic/planning-artifacts.md`), the plan is the
single source of truth — a fresh `/implement` session reads only the file:

- **Persist every decision into the plan** the turn it's made — user choices, resolved
  ambiguities, trade-offs, and **test scope** (promote it from a "suggested" note to a required
  step with acceptance criteria). Decisions that live only in this conversation are lost.
- **Fold later findings back.** A `/spike`, `/grill`, or review run this plan triggers folds its
  verdict **into the affected plan** and cross-links the report from the plan header — don't
  leave it stranded in its own file.
- **Sweep siblings + the overview** after any decision ripples, and **verify** each affected file
  before claiming "all updated". Add the report links to the overview's "Reviews & decisions —
  READ FIRST" index.
- **Flag git-ignored plans** — if the backlog location is local-only (per `PROJECT.md` → Artifact
  git policy), warn the user it won't persist across machines or reach teammates.

---

## Output Format

1. **Strategic Assessment** — problem, value, recommended approach, scope boundaries.
2. **Design Alternatives** (Phase 2.5.1) — the 2–3 approaches trade-off table (effort · risk ·
   reversibility · fit-to-architecture · `Notes` = prerequisite) and the recommendation +
   reasoning, labelled with its failure point and the number at which it stops being enough.
3. **Assumptions to Confirm** (Phase 2.5.2) — the assumptions list with impact-if-wrong;
   flag which were confirmed via `AskUserQuestion` and which were verified in the repo.
4. **Impact Summary**

   | Files | Layers/Modules (per PROJECT.md) | Cross-module? | Boundary risk |
   |-------|--------------------------------|---------------|---------------|

5. **SOLID/DRY**

   | Issue | Principle | Severity (Block/Warn/Info) | Action |
   |-------|-----------|----------------------------|--------|

6. **Reuse** — existing code to leverage; extract-before-implement candidates.
7. **Ordered Prep Steps**

   | # | Action | Files | Reason (SOLID/DRY/rule) | Blast radius |
   |---|--------|-------|-------------------------|--------------|

8. **Where the plan is saved** — every run states the path and the file name (Phase 6.3).
   - **Decomposed** (complex only) — subtask table + dependency graph + wave schedule + the model
     hint per row. `Save to <backlog>/<task-name>/?` — **confirm before creating files**, then
     write `00-overview.md` (with its `## E2E verify` block), `NN-<subtask>.md` per subtask, and
     `implementation-prompts.md`.
   - **Not decomposed** — `Save to <backlog>/<task-name>/plan.md?` (or `NN-<slug>.md` from a card).
     Never `00-overview.md`; that name is the ≥2-subtask index.
   - **Parent RUN-ORDER found** — report the row's Mode/Model/wave as inherited, and the Status
     update you *propose* for the operator to apply. Do not edit that file.
9. **Quality Verification**

   | Check | Status |
   |-------|--------|
   | US-ID **and its ACs** → step mapping complete (or fallback: every requirement has a step) | |
   | All steps specific (WHERE+WHAT+HOW) | |
   | No vague language | |
   | Edge cases addressed | |
   | Rules checklist satisfied | |
   | Design alternatives weighed; assumptions confirmed | |
   | Material assumptions confirmed / repo-verified / routed to `/spike` (wave 0) | |
   | Exemplars vetted, not just found (Phase 5.2) | |
   | Decomposed epic: `## E2E verify` block present, ≥1 blocking row, baseline captured | |
   | Plan file name matches its shape — `00-overview.md` only as a ≥2-subtask index | |

10. **Go / No-Go** — can implementation start now, or must prep steps (or assumption
    confirmations) land first?

---

## Hand-off — how the human should read this plan

Hand the reading order over with the plan, ordered for **early exit**: **intent & scope
boundaries → requirements / AC coverage → the steps**. A wrong intent means *stop reading* —
everything below it is downstream of that error. Then the line that earns those two minutes:

> I faithfully wrote down what you told me. The costliest find here is what you **forgot** to
> tell me — in a plan, absence looks exactly like agreement.

**Right-size it or it becomes ceremony** (`core.md` → reversibility prices the decision): a
one-line reversible fix is a twenty-second look at the intent; an irreversible change —
migration, money, authorization, an external contract — earns the full pass.

---

## DO NOT
- Implement production code — only analyze, plan, and (on confirmation) save the backlog.
- Hardcode commands, paths, layer names, frameworks, or services — read them from
  `PROJECT.md` and installed `.claude/rules/*`.
- Skip Phase 6 for complex tasks, or create backlog files without user confirmation.
- Forget `implementation-prompts.md` after decomposition.
- Save a single-session plan as `00-overview.md` — that name is reserved for the ≥2-subtask index.
- Write into a parent `RUN-ORDER.md`, or create one silently, or report its absence as a gap.
- Invent the E2E baseline at close time — it is captured here or declared missing here.
- Write vague steps, or any step requiring `/implement` to make a decision.
- Propose backward-compat shims, legacy aliases, dead-code comments, or "for now" hacks.
