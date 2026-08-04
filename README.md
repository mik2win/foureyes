**English** · [Русский](README.ru.md)

<img src="assets/logo.svg" alt="" width="88" align="right">

# FourEyes 🤓

> A self-contained `.claude/` that turns any repo into a disciplined feature factory — one
> adaptive pipeline from discovery to shipped code, backed by a fleet of subagents that report
> signal, not noise.

*Two meanings, both meant. **Four-eyes** is the kid in glasses who actually read the manual. The
**four-eyes principle** is the rule that no consequential work is accepted on one pair of eyes.
This kit automates the second one so you can afford to be the first.*

A portable, **stack-adaptive** feature pipeline (`/discover → /analyst → /prepare → /implement`)
plus quality, alignment, and backlog skills, 16 subagents, generic + stack rule packs, hooks, and a
`/bootstrap` adapter that tailors the whole thing to any project. Drop it into a project's
`.claude/`, run `/bootstrap`, and you get the full workflow + project-specific rules — no per-project
skill rewrites.

## What was measured — including the results that argue against the kit

Most kits ship claims. This one was put on a blind A/B bench first: two arms of the same real
repository differing by exactly one thing, a sealed mixing map, a 5-axis rubric (correctness ·
edge/unhappy-path · verification · report honesty · process fit), and a written noise-limits
section. Four rounds. Everything it returned is below, negatives included.

| Question the bench was asked | What came back |
|---|---|
| Do the generic rules beat no rules at all? | **Yes, weakly.** Round 1, 16 runs: the arm *with* rules wins 2 of 4 task types, ties 2, loses 0 — mean Δ ≈ +0.5 on the rubric, cleanest on implementation and planning. It also burned **1.3–2× the tokens.** |
| Does the always-on rule tier make output *better*? | **No — three rounds running, no measurable quality gain.** It is reliably *cheaper* (0.82× and 0.93× tokens on two slots). The honest sentence is *"the same result for less money"*, not *"it works better"*. This result is why the always-on tier was cut from 13 rules to 4. |
| Do skills fire by themselves when a prompt matches one? | **No. Zero invocations across all 16 runs.** ~10k of always-on skill descriptions never matched anything. That is the finding behind [manual-by-default and its three escape hatches](#skills-are-manual-by-default--and-the-three-escape-hatches). |
| Does *this particular rule* pay for its context? | **The bench cannot answer that** — isolating one rule and keeping a run valid turned out to be mutually exclusive conditions. Saying so was more useful than a number; the candidate queue was closed with transcript counters instead. |

**Limits, stated plainly.** One production Python repo plus neutral arms, n=2 per cell, and the
judge is a model. The stack packs (ruby / rails / react-ts / postgres) were never in an arm — they
are contributed templates, not measured ones. Read the table as directional, not as a benchmark.

The reason to publish the negatives is that they are the expensive part. Anyone can write a rule
file; knowing that a tier of them buys cost and not quality took four rounds and ~40 judged
sessions, and it changed the kit's shape.

### The discipline layer — what you won't find in another kit

Most kits give you *workflow*. The pipeline shape (`discover → ship`, one-question interviews,
living glossaries) is real but not rare — it's shared methodology, and FourEyes
[credits its lineage](#why-foureyes-not-another-agent-collection). What sets FourEyes apart is the **discipline layer underneath the
workflow**: an explicit model of *how agents fail* and countermeasures wired into structure, not
hope. If you take one thing, take this.

- **A field catalog of 22 agent failure modes** — [`docs/agent-failure-modes.md`](docs/agent-failure-modes.md).
  Each entry is *symptom → mechanism (why it happens) → countermeasure → where the kit already wires
  it*. `/retro` classifies recurring problems against it; `/writing-skills` designs new skills
  *against* it. Most kits ship "best practices"; this ships a theory of the defects and the fix for
  each.
- **Generation-from-the-inside rules** — [`docs/self-knowledge.md`](docs/self-knowledge.md) + the
  distilled [`self-knowledge`](rules/_generic/core.md), [`diligence`](rules/_generic/core.md),
  and [`decision-craft`](rules/_generic/core.md) rules. These target the defaults a strong
  model *won't* self-correct: recalled facts are stale-by-default (verify against the lockfile, not
  memory); evidence is derived before the verdict (a verdict written first anchors the analysis under
  it); you can't fairly review what you just wrote (real review goes to a fresh context); rewrites
  regress to the training mean (surprising code is load-bearing until proven decorative); effort is
  *allocation, not motivation* (done is an external list, the hard part goes first, homework isn't
  handed back). This is behavioral override, not encouragement.
- **Greppability as an architectural contract** — [`rules/_generic/code.md`](rules/_generic/code.md).
  Premise: *the next maintainer is an agent that navigates by exact-name search*, so every future
  inventory (a `/sweep`, a dead-code proof, an audit) is only as complete as what search can see.
  One symbol = one greppable definition site; no runtime-constructed names outside a declared,
  enumerable seam. Boilerplate is not an excuse — the human motive for metaprogramming (typing
  fatigue) doesn't apply to an agent, while its costs hit agents harder.
- **Adversarial, lens-diverse verification** — the **Finding Contract** across
  the whole fleet, plus `finding-verifier`'s **panel mode**: N clones briefed identically share blind
  spots (their agreement is an echo), so CRITICAL findings get one *distinct lens* per instance
  (correctness / security / does-it-reproduce), default-REFUTED, majority vote. Independence is bought
  with framing, not head-count.

The workflow is the part you'll recognize from other kits. The discipline layer is the part that
makes a 10-agent review return signal instead of confident noise.

### Why FourEyes, not another agent collection

Most Claude Code repos are *catalogs* — a pile of independent agents you wire together yourself.
FourEyes is the opposite: **one opinionated path with quality gates**, engineered so it stays generic.

- **A pipeline, not a pile.** `discover → spec → plan → build → review` as a single self-propelling
  flow, not 200 à-la-carte agents.
- **Subagents that respect your context window.** Every finder honors one **Finding Contract** —
  bounded, structured findings (`path:line` + severity + effort + concrete harm) — so a 10-agent
  review returns signal, not an 8k-token dump. This discipline, applied across the whole fleet, is
  the part you won't find elsewhere.
- **Drop-in and stack-adaptive.** `/bootstrap` reads your repo into `PROJECT.md`; skills stay
  generic and adapt at runtime. Porting = copy + bootstrap, never editing skills. The design is
  stack-neutral by construction — no skill names a language — but it has been *exercised* on
  Python; the ruby / rails / react-ts / postgres packs ship untested by the bench.
- **Survives long work.** The plan is the single source of truth across compaction and sessions
  (the *Artifact-Continuity Contract*) — resume mid-feature without re-explaining. Stage gates
  make the pipeline mechanical: each stage checks the previous artifact on entry and returns a
  weak one with reasons, instead of silently compensating downstream.
- **A learning loop, not a static pack.** Every `/implement` writes a Deviation Report; `/retro`
  mines them (plus handoffs and diagnose logs) for recurring, evidence-verified patterns and
  folds the lessons back into your rules and profile — the kit adapts to your project over time.

**Lineage — honest about its roots.** FourEyes builds on ideas popularized by
[Matt Pocock's skills](https://github.com/mattpocock/skills) and
[obra/superpowers](https://github.com/obra/superpowers) (the relentless one-question interview,
living ubiquitous-language + ADRs, deep-module design, a discover→ship methodology — with nods to
Eric Evans's DDD and John Ousterhout's *A Philosophy of Software Design*). What FourEyes adds is a
**disciplined multi-agent layer** (the Finding Contract) and a **portable, stack-adaptive
distribution** (`PROJECT.md` + `/bootstrap` + stack rule packs) so the whole methodology drops into
any repo and stays generic.

What is borrowed is *method*, not text — no file here is a copy of theirs, and the two kits'
skills differ in structure, phases, and output format. Both upstreams are MIT, as is FourEyes
([LICENSE](LICENSE)); the credit above is owed to the ideas regardless of what the license
requires.

### FourEyes vs the two common archetypes

| | **Catalogs** (wshobson, VoltAgent) | **Methodologies** (superpowers, mattpocock) | **FourEyes** |
|---|---|---|---|
| Shape | à-la-carte agents you wire up | opinionated skill flow | opinionated flow **+ portable distribution** |
| Adapts to your repo | manual | via a root doc | `/bootstrap` → `PROJECT.md`, skills stay generic |
| Multi-agent noise control | per-agent, ad hoc | light | one **Finding Contract** across the whole fleet |
| Always-on rules | rare | rare | generic + stack `paths:`-scoped rule packs |
| Context survival | — | plan/handoff files | Artifact-Continuity Contract (plan = SSOT) |

## Install

FourEyes is **copy-in**: the files live in your project's `.claude/` (that's what keeps commands
unprefixed and rules always-on — [plugins can't do either](#distribution-model)).

**Copy the kit in, then adapt it:**
```bash
git clone https://github.com/mik2win/foureyes.git foureyes
[ -e <project>/.claude ] && cp -r <project>/.claude <project>/.claude.bak   # back up first
rsync -a --exclude='.git' --exclude='.claude' --exclude='_backlog' --exclude='tools' \
  --exclude='.github' --exclude='LICENSE' --exclude='CONTRIBUTING.md' --exclude='CHANGELOG.md' \
  --exclude='CODE_OF_CONDUCT.md' --exclude='SECURITY.md' --exclude='.gitignore' \
  foureyes/ <project>/.claude/
```
Then open the project in Claude Code and run **`/bootstrap`**. Full walkthrough:
[Integrate into a new project](#integrate-into-a-new-project).

Copy-in is the **only** install path, by design — see [Distribution model](#distribution-model)
for why a plugin can't carry this kit.

## What's in it

| Part | What |
|------|------|
| **Pipeline skills** | `/discover` → `/analyst` → `/prepare` → `/implement` (research → spec → plan → code — `/implement` routes every finding it hits down one of four branches: fix it, file it, STOP and ask, or hand it to the sibling that owns the file) · `/idea` — the plain-language front door over the whole spine: a non-technical user describes an outcome, the agent elicits the wish in outcome scenarios, shows 2–3 solution shapes with felt trade-offs, then drives the pipeline itself, owning every technical decision (register contract: `docs/audience-altitude.md`) · `/scaffold` — the short branch off the spine for "add another one like the existing one": read the canonical exemplar first, place it per the profile, then wire every registration point and **prove each one with a command** (the failure this task really has is silent — an unexecuted load-bearing import raises nothing, the artifact is just missing from `--help`) |
| **Orientation** | `/onboard` — fast comprehension of an unfamiliar/inherited codebase: run-it-first (behavior anchors reading), one flow traced end-to-end (the architecture's dialect), git-history archaeology (churn hotspots = where the business lives, bus factor, the feared-old code), tests-as-documentation, a load-bearing-weirdness list (surprising code is never normalized on first contact) → a written orientation map that feeds `/bootstrap` |
| **Explore-first** | `/spike` (validate ONE risky hypothesis, time-boxed, throwaway) · `/prototype` (explore a design space — runnable logic or several UI variations) · `/select-tech` (choose a library/gem/framework/service or decide to build: hard filters kill fast, then an adversarial deep-dive on 2–3 finalists — the issue tracker over the README, a hard-case probe against real docs instead of the tutorial case, upgrade-path history as your future tax, bus factor, escape cost — scored matrix with ONE recommendation, the "build it ourselves" zero option always on the ballot, and an adapter-seam integration contract so the choice stays a two-way door; all candidate facts verified live, never from memory) |
| **Alignment & design** | `/grill` (relentless one-question interview primitive the pipeline reuses) · `/grill-with-docs` (grill + capture terms/ADRs inline) · `/domain-model` (living `CONTEXT.md` glossary + ADRs — the project's shared language) · `/codebase-design` (deep-module design vocabulary) · `/api-design` (public contracts — endpoint/webhook/CLI/library: consumers & compatibility promise first, resource model in the domain language, the contract checklist — one error envelope, cursor pagination on every list from day one, idempotency keys for retried non-GETs, additive-only evolution — worked examples including the error cases, and a consumer's-eyes pass that writes the client code for the hard case before the contract ships; Hyrum's law taken seriously: every exposed field is forever) |
| **Quality skills** | `/code-review` (CRITICAL findings pass an adversarial `finding-verifier` gate before you see them), `/refactor`, `/diagnose`, `/test`, `/tdd` (red-green-refactor, test-first), `/test-spec` (spec-first — derive tests from a plan *without reading the code*; the spec is truth), `/arch-health` (periodic ball-of-mud scan + PROJECT.md drift check) · `/clean-mvp` (whole-codebase cruft sweep — dead code, unused files, legacy shims, with a proof-of-deadness gate) · `/sweep` (mass mechanical migration: full site inventory → pilot batch → verified batches → zero-leftover re-scan; at ~30+ mechanical sites it writes the tool, not the edits — an AST-based codemod proven on the pilot and kept as a re-runnable artifact, because hand-editing a long tail is a compounding error surface) · `/perf` (measurement-first optimization: named metric + budget before any code is read, reproducible baseline, the profile picks the target — never intuition, biggest-lever order (don't do the work > batch it > right algorithm > micro), one change per re-measure with expected-vs-actual, caches declared with invalidation + ceiling, stop at the budget — over-optimization is negative-value work) |
| **Architecture evolution** | `/decompose` (monolith vs modular monolith vs service extraction, decided per boundary on evidence — real drivers (deploy contention, asymmetric scaling, failure isolation, team ownership — org facts *asked*, never inferred from code) weighed against the explicitly-accepted distributed tax; verdict STAY / MODULARIZE / EXTRACT with "extract the seam before the service" as the governing rule, STAY recorded as a first-class ADR so it isn't relitigated; EXTRACT executes via `/rollout`'s strangler stages) · `/revisit` (decisions rot silently — re-audit past choices (ADRs, `/select-tech` picks, undocumented load-bearing choices via git archaeology) by extracting each decision's falsifiable assumptions and testing them against today: internal evidence from the repo, external evidence verified live (never from memory), org changes asked; verdict HOLDS / STRAINED (measurable tripwire set) / BROKEN (reopened only on a named broken assumption with evidence — an assumption audit, not a preference audit); supersede ADRs, never rewrite) · `/distill` (mine the repo's implicit conventions along ten dimensions with ≥3 cited occurrences each; verdict BLESS / UNIFY (fork tax — winner picked with the user, loser's sites → `/sweep`) / BAN (replacement always named) / DEEPEN (copy-paste family → deep module); intent gate before any ban — weird-but-consistent beats familiar-but-foreign; verdicts installed at the right altitude: lean always-on rules with in-repo GOOD/BAD exemplars, heavy reference on-demand, terms → `CONTEXT.md`) — the review-what's-built triad: structure (`/decompose`), decisions (`/revisit`), conventions (`/distill`) |
| **Ship & learn** | `/rollout` (staged strategy for risky/irreversible changes — expand-contract, strangler fig, flags/canary, versioned coexistence; every stage deployable, verifiable, and reversible alone; the destructive step last, gated on observed zero-dependence) · `/preflight` (release-readiness gate: full suite, deps/security quick pass, docs drift, config/migration check, changelog draft, GO/NO-GO verdict — deploy suggested, never run) · `/incident` (production fire discipline — the live inversion of `/diagnose`: triage → preserve evidence *before* mitigation destroys it → mitigate toward known-good (rollback/flag-off, no novel code under adrenaline) → verify recovery by user-visible signal → blameless review; commands suggested, never run) · `/retro` (the learning loop: mine Deviation Reports, handoffs, and diagnose logs for recurring, verified patterns and fold each lesson back into rules/PROJECT.md/skills with confirmation) |
| **Backlog (local tracker)** | `/to-prd` (conversation → PRD) · `/to-issues` (plan → vertical-slice issues) · `/triage` (move issues through the state machine) · `/epic-status` (read-only progress dashboard over a wave-structured decomposition: next safe wave, session-collision check, and the epic's `RUN-ORDER` read against the plans' own frontmatter — a `∥` mark is a *claim*, re-verified against the `Owns` sets, and drift between the two is reported, never silently reconciled) · `/close-epic` (its terminal counterpart — every plan terminal, then an **end-to-end battery**: the epic's declared `## E2E verify` block if it has one, otherwise a battery *derived* from the surfaces the diff touched and disclosed as derived; drives are delegated but the verdict is not, and one headline number is always re-derived by hand; then plan↔code conformance + docs-drift, a completeness critic, **promotion of every flagged follow-up into a numbered card** (`F<wave>.<n>`, with where it goes and why), a predicted-vs-actual ledger row, `## E2E results` written back into the epic overview, and a copy-paste archive command it never runs) — all local markdown, no external tracker |
| **Session / context** | `/handoff` — snapshot live state (done · next · decisions · files · how to verify) into a resume doc; the `precompact.sh` hook re-injects a preservation checklist on every context compaction |
| **Meta** | `/which-skill` (router — "which skill fits my situation") · `/prompt-master` (compile an idea into a phased pack of self-contained prompts to run in other sessions/models — wraps the kit pipeline or embeds the full methodology standalone; also authors the **tier-1 program pass**: a whole-surface discovery sweep whose emitted agent prompts carry the evidence-file convention and whose output contract is report + evidence + cards + RUN-ORDER, stopping before implementation. A deterministic pack is *also* emitted as a `Workflow` script — emitted, never run: invoking one is the user's opt-in, not a skill's) · `/writing-skills` (kit-internal authoring reference) |
| **Security** | `/threat-model` (design-time STRIDE-lite BEFORE code exists — entry points × trust boundaries × data classes, the two actors every spec forgets (the unauthenticated stranger, the authenticated-wrong-tenant user), abuse cases: hostile power user / curious insider / forged webhooks; every threat lands as a falsifiable AC, a plan step, or a user-signed accepted risk — never advice) · `/audit-security` (orchestrating OWASP-style sweep over EXISTING code → risk-tiered report + deploy verdict) · `/deps` (dependency-vulnerability audit) · the `security-reviewer` agent (delegates to the built-in `/security-review`), the `guard-secrets` warn-only hook, and always-on `rules/_generic/code.md` |
| **Code-publish control** | The agent **never publishes code without you**: `git add`/`commit`/`merge`/`push` are denied in `settings.json` and hard-blocked by `guard-bash.sh` (suggest-only — it outputs the command, you run it). `/bootstrap` surveys the policy and lets you forbid more commands. Web search/fetch for research stay available — this governs *code leaving the machine*, not reading the web. Complementary built-in safety layers: **`/rewind` checkpoints** (undo the agent's edits per-step) and Claude Code's **`sandbox` settings** (OS-level isolation for risky runs) — use them alongside the kit's guards, not instead |
| **Adapter** | `/bootstrap` — detect stack, write profile, install & reconcile rule packs (backs up first, confirms keep/rollback at the end); `/update-kit` — pull a newer kit version into an already-bootstrapped project (3-way merge, keeps your adaptations); `/teardown` — clean up leftovers or uninstall & restore |
| **Agents** | Review & verify: `code-reviewer`, `parallel-reviewer` (modular fan-out), `security-reviewer`, `finding-verifier` (adversarial 3-lens check of findings before they become plans; panel mode for CRITICALs — 3 instances, one lens each, majority vote), `plan-verifier` (implemented plan vs git history), `quality-auditor` (SOUND/SHORTCUT/HACK post-implementation), `completeness-critic` (final-pass "what's missing" hunter over reports/specs/close-outs), `plan-challenger` (adversarial PRE-implementation review — the implementation session that hasn't happened yet: opens every file the plan touches and checks the plan's model of it, demands quoted interfaces, walks case coverage, greps ripples past the impact map, audits assumption ownership; fresh-context on purpose so it has the plan but not the planner's rationalizations; /prepare's Complex-tier gate) · Analysis: `deep-analyzer`, `arch-tracer`, `test-gap-finder`, `performance-analyzer` (hot paths, complexity, memory, I/O & N+1, concurrency) · Writers: `docs-writer`, `test-writer` (parallel, worktree-isolated) · Research: `backlog-researcher` (feasibility pass on a backlog item). All read `PROJECT.md` at start and degrade gracefully pre-`/bootstrap`; per-agent `model:`/`effort:` frontmatter matches depth to the job (verifiers high, mechanical writers medium); finders share one anti-noise Finding Contract (`path:line` + severity + effort + concrete harm scenario), also shipped as a JSON Schema (`schemas/finding.schema.json`) for structured fan-out output |
| **Generic rules** | `rules/_generic/` — language-neutral, in **three load tiers** (visible in `/context`): **always-on** is a single file, [`core.md`](rules/_generic/core.md) (~950 tokens, no `paths:`) — Evidence, Done, Decisions, Reporting: the judgment that must be present in the first reasoning turn. It is the distillate of what were once five separate always-on rules; the 13→4 tier cut collapsed them after an A/B round measured **no behavioural delta and +13% cost** for the extra tier. Next, **`paths: "**/*"`-scoped** rules load on first file read — `code.md` (comments, greppability, boundary validation, security), `code-quality.md`, `exception-patterns.md`, `testing.md`, `observability.md`, `external-api-integration.md`, `resilience.md` (timeouts/retry/circuit-breaker/idempotency), `service-layer.md` (thin shells + CQS), `domain-events.md`. Last, a **narrow on-demand tier** scoped to where each fires — `delegation.md` (`.claude/agents,skills` — subagent briefs, reports-are-claims, honest aggregation, vary-the-lens fan-out, the tools a subagent will not get, an empty return is a failed unit), `memory.md` (`.claude/agents` — one fact per file, indexed, update-don't-duplicate), and the plan/spec pair `planning-artifacts.md` + `parallel-wave-execution.md` (the Artifact-Continuity Contract and stage gates; the in-flight wave contract — disjoint `Owns`, serialization points, the out-of-`Owns` classification table) |
| **Stack rule packs** | `_kit/rules-library/` — `python`, `react-ts`, `ruby`, `rails`, `postgres`; each bundles lean always-on rules + optional on-demand reference skills (e.g. `/ruby-idioms`, `/rails-reference`, `/postgres-reference`) |
| **Hooks** | `hooks/` — guard-bash (reconciled with 2026 built-in destructive-command protection — no double prompts; keeps the kit's publish policy), guard-secrets (warn-only), format-file, sessionstart, precompact (context-preservation on compaction), subagent-stop (warn-only Finding Contract gate on subagent reports), verify-stop (opt-in, OFF-by-default, non-blocking lint/test gate), skill-hint (opt-in, OFF-by-default, advisory prompt→skill hint — see [Skills are manual by default](#skills-are-manual-by-default--and-the-three-escape-hatches)) |
| **Contracts** | `PROJECT.template.md`, `settings.template.json`, `CLAUDE.snippet.md`, `schemas/finding.schema.json` (the Finding Contract as JSON Schema — pass it to fan-out finders for mechanically mergeable output) |
| **Docs** | `docs/observability.md` (your-code observability + opt-in Claude Code OTEL telemetry) · **the legacy quintet**: `docs/agent-failure-modes.md` (22 systematic agent failure modes with mechanisms & countermeasures — `/retro` classifies against it, `/writing-skills` designs against it) · `docs/self-knowledge.md` (generation from the inside — thirteen phenomena only visible from within the model, each with mechanism, detection, and technique. Part I, truth: confabulation tells & the neighborhood test, the snapshot problem, self-anchoring, author blindness, regression to the training mean, correlated blind spots, lens activation, the entropy budget, the correction gradient. Part II, the physics of effort — why "laziness" is allocation, not motivation, and why threats produce anxious text instead of work: the aesthetic stop, difficulty inversion, minimal-diff bias, homework return. Distilled into always-on `rules/_generic/core.md`) · `docs/working-with-agents.md` (the developer's side: briefing, steering, verifying, feeding the learning loop; + the worktree-inheritance limitation and its re-check test) · `docs/prompt-patterns.md` (design prompts/skills for the weakest model that will run them — 12 degradation-proof construction patterns) · `docs/decision-craft.md` (judgment under uncertainty — the layer above execution: doors/reversibility pricing, the cheapest killing probe, predict-before-you-peek, calibration & reference-class estimation, the pre-mortem as prospective hindsight, when *not* to decompose, invariants as review lens and property-test seed. Distilled into always-on `rules/_generic/core.md`) · `docs/agent-teams.md` (experimental agent-teams → kit-waves mapping — document, don't depend) |

## Using the kit — recommended flows

The skills are **composable**: reach for one directly, or chain them. Unsure which fits? Ask
**`/which-skill "<your situation>"`** — it routes any situation to the right skill or chain.

### Three tiers — pick the right entry point

Work arrives at three sizes, and each has its own entry point. Sending a whole surface to
`/prepare` is the common mistake this table exists to prevent.

| Tier | What you're holding | Entry point | What comes out |
|------|---------------------|-------------|----------------|
| **1 · Program** | a whole *surface* to audit or map — the output is plausibly 10+ separate pieces of work ("review every screen", "audit this whole area") | `/prompt-master` (program pass) | `00-report.md` (ranked findings) + `evidence/` (one file per agent) + `cards/NN-<slug>.md` + `RUN-ORDER.md` |
| **2 · Epic** | one card, or one coherent change | `/prepare` | `00-overview.md` + `NN-<subtask>.md` decomposed into file-disjoint waves |
| **3 · Session** | one prepared subtask | `/implement` | code + implementation log + deviation report |

A tier-1 pass **stops at cards** — it never writes plans and never implements; each card is
then one `/prepare` input. Tier 2's wave machinery is what makes tier 3 sessions safe to run
in parallel; `/epic-status` reports on it and `/close-epic` settles it.

```text
  ask  /which-skill "<situation>"   →   it routes you to a step or the whole chain below
  ─────────────────────────────────────────────────────────────────────────────────────

  MAIN PIPELINE
     /discover  →   /analyst   →   /prepare   →   /implement   →   /code-review + /test
     (research)     (spec)         (plan)          (build)           (verify)
  NON-TECHNICAL?    /idea — "I want it so that…" → the agent drives this whole pipeline
                    itself: plain-language questions, felt trade-offs, behavior-first delivery
                       ▲              ▲                │
                    /grill         /grill      test-first slice → /tdd
                       └──── /domain-model: CONTEXT.md glossary + ADRs (shared language) ────┘
       across all stages:  /codebase-design — deep-module vocabulary (prepare · tdd · refactor)

  BEFORE COMMITTING      /spike (one yes/no risk)   ·   /prototype (compare designs)
  FIX A BUG              /diagnose  →  /tdd | /test  (lock with a regression test)
  REFACTOR               changed code: /code-review  →  /refactor
  ARCHITECTURE HEALTH    /arch-health  →  /refactor (small) | /prepare → /implement (large)
  CODEBASE SWEEP         /clean-mvp (dead code & cruft, whole tree, proof-of-deadness first)
  PARALLEL WAVES         /prepare (decompose)  →  N × /implement  →  /epic-status (next wave?)
  REQUIREMENTS→BACKLOG   /grill-with-docs → /analyst → /to-prd → /to-issues → /triage
  MASS MIGRATION         /sweep (inventory → pilot → verified batches → zero-leftover re-scan)
  SHIP                   /close-epic → /preflight (suite·deps·security·docs·changelog → GO/NO-GO)
  LEARN                  /retro (recurring lessons from deviation reports → back into rules/profile)
  MAINTAIN               /deps  ·  /handoff  ·  /writing-skills (author a kit skill)
```

<details>
<summary>Same map as a Mermaid diagram (renders on GitHub)</summary>

```mermaid
flowchart LR
  WS(["/which-skill — describe a situation"])
  D["/discover<br/>research"]
  AN["/analyst<br/>spec"]
  PR["/prepare<br/>plan"]
  IM["/implement<br/>build"]
  V["/code-review + /test<br/>verify"]
  GR["/grill"]
  DM["/domain-model<br/>CONTEXT.md + ADRs"]
  TDD["/tdd"]
  SP["/spike"]
  PT["/prototype"]
  DG["/diagnose"]
  AH["/arch-health"]
  RF["/refactor"]
  PF["/preflight<br/>release gate"]
  RT["/retro<br/>learning loop"]

  WS -. routes .-> D
  D --> AN --> PR --> IM --> V
  V --> PF
  PF -. lessons .-> RT
  RT -. rules/profile updates .-> PR
  GR -. interview .-> AN
  GR -. interview .-> PR
  DM -. shared language .-> AN
  IM -. test-first slice .-> TDD
  SP --> PR
  PT --> PR
  DG --> TDD
  AH --> RF
  RF --> PR
```

</details>

Common flows by activity:

### Build a feature (the main pipeline)
`/discover` (prior art & reuse) → `/analyst` (spec via interview) → `/prepare` (design, impact,
decomposition) → `/implement` (build + architecture audit + tests, plus a behavior check that
drives *this* slice and names the epic's outstanding rows by number) → `/code-review` + `/test`.
Run `/domain-model` alongside to capture terms/decisions into `CONTEXT.md` as they surface.
- **Small, known change?** Skip ahead — `/prepare` then `/implement` (or `/implement` directly);
  finish with `/code-review`.
- **Still fuzzy?** Start at `/discover`, or `/grill-with-docs` to align *and* build the shared
  language in one session.

### Plan & analytics (requirements → work items)
`/grill` or `/grill-with-docs` (pressure-test the idea, one question at a time) → `/analyst`
(WHAT/WHY spec) → `/to-prd` (write up the discussion) → `/to-issues` (break into vertical-slice
issues) → `/triage` (sort the local backlog, pick what's next). `/domain-model` keeps the
ubiquitous language (`CONTEXT.md` + ADRs) sharp throughout. For a wave-structured epic from
`/prepare`, `/epic-status` reports progress, the next safe wave, and session collisions.

### Test
- **New code, test-first:** `/tdd` — red → green → refactor in vertical slices (`/implement` can
  delegate a slice to it).
- **Cover or clean existing tests:** `/test` — gap analysis, AAA/mocking discipline, refactor.
- **Lock a bug fix:** reproduce with a failing test first (see *Debug*).

### Debug
`/diagnose` (reproduce → isolate → root-cause → fix → verify) → `/tdd` or `/test` to lock the fix
with a regression test.

### Refactor & architecture health
- **Clean changed code (same behaviour):** `/code-review` (find) → `/refactor` (apply + format + test).
- **Whole-codebase health, every few days:** `/arch-health` (rank shallow-module / ball-of-mud
  opportunities) → `/refactor` (small) or `/prepare` → `/implement` (large). `/codebase-design` is
  the shared deep-module vocabulary both lean on.
- **Sweep the cruft (MVP stage):** `/clean-mvp` — whole-tree dead-code/legacy-shim removal with a
  proof-of-deadness evidence gate and batched confirmations before anything is deleted.

### Explore / de-risk before committing
- **One yes/no risk:** `/spike` (throwaway, time-boxed). **A design space (logic or UI options):**
  `/prototype` (several variations to compare).

### Maintain
- **Dependencies & vulnerabilities:** `/deps` + the `security-reviewer` agent.
- **Pausing / handing off:** `/handoff` (snapshot state into a resume doc).
- **Adding a kit skill:** `/writing-skills` (authoring reference).

### Skills are manual by default — and the three escape hatches

**42 of the kit's 49 skills carry `disable-model-invocation: true`.** They run when *you* type
`/prepare`, and never because the model decided a prompt looked like planning. That is the
deliberate default, and it is worth being explicit about both sides of it.

**What it buys.** No surprise activation. A skill is a long, opinionated procedure — `/close-epic`
alone spawns verifier agents, runs a battery, and edits two files. Auto-firing one on a
half-formed request costs a rewind, not a turn, and the *silent* variant is worse: work done under
a procedure you never chose and can't see in the transcript. Manual invocation also keeps the
skill index out of the model's decision loop on every prompt.

**What it costs, measured.** A concrete task request with a perfect skill match **silently runs
bare**. Three sessions asked "check if epic is done? `backlog/<name>`, run the verification steps
from the overview" and reconstructed `/close-epic`'s checklist by hand: 70–92 Bash calls each,
**zero** verifier agents spawned, the plan-status tool never run, and one session executed a
`git mv` the skill's DO-NOT list forbids. The output was still good — the loss is the verification
that never happened and roughly a quarter of each session spent rediscovering facts the skill
already knows.

The escape hatches exist because that failure is invisible from inside: nothing tells you a skill
*would* have fired. There are three, in increasing order of how much they change:

| # | Hatch | What it does | Cost |
|---|-------|--------------|------|
| 1 | **Seven skills stay invocable** | the terminal/verification five — `/close-epic`, `/epic-status`, `/diagnose`, `/triage`, `/preflight` — plus `/which-skill` (the router) and `/bootstrap` (the installer). Each of the five carries a task-shaped `TRIGGER ALSO` line written in the phrasing that actually failed above. Three of them write *files* (a ledger row, a `status:`, a report) but none touches code or git | the narrowest class where the miss hurt; no config |
| 2 | **`/which-skill`'s silent match** | the router also fires on a concrete task that matches an installed skill's domain *without* naming it. One obvious match → one line naming the skill, then it runs (on your yes, or when the task is plainly that skill's own job); two candidates → one `AskUserQuestion`; no match → it says nothing about routing and the work happens bare | a router that answers loudly on every task would just add a turn; the brevity rule is what makes this affordable |
| 3 | **`hooks/skill-hint.sh`** — opt-in, **OFF by default** | a `UserPromptSubmit` hook that scores the prompt against every installed skill's frontmatter and injects the top 1–2 names as advisory context. It never blocks, never rewrites the prompt, and stays silent when nothing scores or when the prompt already names a skill. ~29 ms/prompt, measured at 46 skills | not wired by the kit — merge the `UserPromptSubmit` block from `settings.skill-hint.example.json` into `.claude/settings.json` (or accept `/bootstrap`'s offer). `SKILL_HINT_DISABLE=1` turns it off without unwiring. **Matching is English-token based**, so a non-English prompt scores 0 and the hook stays silent — a missed hint, never a wrong one |

A hint is not an invocation: hatches 2 and 3 put the skill's *name* in front of the session and
stop there. The decision to run it stays yours, which is the property manual-by-default was
protecting in the first place.

## Design principle

Skills carry **only invariant workflow logic**. Every project fact (stack, commands,
paths, layers, domain, integrations) lives in one place — **`.claude/PROJECT.md`** — which
skills read at runtime. So porting = copy the kit + run `/bootstrap`, not editing skills.

A second, **living** document is the project's **`CONTEXT.md`** — the ubiquitous-language glossary
(plus ADRs in `docs/adr/`) that `/domain-model` builds as you work. `PROJECT.md` holds static
facts; `CONTEXT.md` holds the shared vocabulary, so the agent stays terse and names code
consistently. Skills read it when present and speak its language.

**Artifact-Continuity Contract.** Because a fresh session reads only the plan file — not the
chat — `rules/_generic/planning-artifacts.md` (on-demand, scoped to plan/spec/backlog files and
read by every planning skill on entry) makes the planning artifact the
single source of truth: every plan-touching skill and agent persists decisions (including test
scope) into the affected plan the turn they're made, cross-links each spike/review/grill report
from the plan header, sweeps sibling plans + the epic overview after a decision ripples, and
marks load-bearing framework behaviour as an assumption to validate via `/spike`. It's the
"Finding Contract" idea applied to plans, so context stops leaking between stages and sessions.

**Artifact git policy.** The agent's working artifacts (briefs, specs, plans, PRDs, issues,
handoff notes) and the shared model (`CONTEXT.md` + ADRs) each have a git policy you
choose **interactively at `/bootstrap`** — keep a category **local** (gitignored, never pushed) or
**commit** it (shared). The default offers working backlog as local scratch and `CONTEXT.md`/ADRs
as committed shared knowledge, but you decide per category; `/bootstrap` writes the choice to
`PROJECT.md` and adds the local paths to `.gitignore`. The agent never commits anything itself.

## Integrate into a new project

> **First install only.** The raw copy below is for a project that has **not** been bootstrapped
> yet. To pull a *newer* kit version into a project you already bootstrapped, do **not** re-copy by
> hand — use **`/update-kit`** (see [Update the kit](#update-the-kit)); it preserves your adaptations.

```bash
# 1. (existing project) back up anything the kit might overwrite, so you can fully restore later
[ -e <project>/.claude ] && cp -r <project>/.claude <project>/.claude.bak
[ -f <project>/CLAUDE.md ] && cp <project>/CLAUDE.md <project>/CLAUDE.md.bak

# 2. Copy the kit's contents into the project's .claude/ (skip git and repo infrastructure)
rsync -a --exclude='.git' --exclude='.claude' --exclude='_backlog' --exclude='tools' \
  --exclude='.github' --exclude='LICENSE' --exclude='CONTRIBUTING.md' --exclude='CHANGELOG.md' \
  --exclude='CODE_OF_CONDUCT.md' --exclude='SECURITY.md' --exclude='.gitignore' \
  foureyes/ <project>/.claude/
```
3. Open the project in Claude Code and run **`/bootstrap`**. It will:
   - back up the files it's about to change, then detect empty vs existing and scan the stack;
   - draft `.claude/PROJECT.md` (asking you for domain + anything ambiguous);
   - select rule packs from `_kit/rules-library/` matching the stack;
   - on an existing codebase, **reconcile** each pack's assumptions vs the real code and
     ask how to resolve divergences (adopt / relax / skip);
   - generate `.claude/rules/`, `settings.json`, git commands, and wire `CLAUDE.md`;
   - ask **keep or roll back**, then **clean up** `_kit/` and `*.template.*`.
4. Smoke-test: run `/analyst` (it interviews from the profile's domain) and the profile's
   `test` command.

## Rule packs

> **Maturity, honestly.** The packs are the least-proven part of the kit. Their *shape* — the
> path-scoped rule / on-demand reference split below — comes straight from what the bench
> measured about always-on context. Their *content* does not: only the generic rules were ever
> in an arm, and every pack here was written for a project, not validated by a run. Use them as
> a starting skeleton for your stack, expect to rewrite half, and PRs correcting them are the
> single most useful contribution to this repo.

Stack rules live in `_kit/rules-library/<stack>/` — edit them there. Each pack has a
`pack.yaml` (`detect` / `installs` / `assumptions`); the format is in
`_kit/rules-library/PACKS.md`. Kit manifest / internals: `_kit/KIT.md`.

Each pack ships two layers (the `rule` vs `skill` triage is spelled out in `PACKS.md`):
- **Path-scoped rules** (`claude/rules/*.md`) — lean, imperative conventions scoped to the
  tightest `paths:` for the layer they govern; they load in full whenever a matching file is read.
  (Kit judgment rules omit `paths:` on purpose so they load at launch — see the Generic-rules row.)
- **On-demand reference skills** (`claude/skills/*-reference/`) — worked GOOD/BAD examples,
  API tours, and checklists that load only when invoked, so always-on context stays lean. The
  `ruby` / `rails` / `postgres` packs split their heavy convention rules this way
  (e.g. `/ruby-idioms`, `/rails-reference`, `/postgres-reference`).

## Update the kit

When the kit gets a newer version and you want it in a project you **already bootstrapped** —
without losing skills you adapted, your `PROJECT.md`, `CONTEXT.md`, ADRs, or backlog — use
**`/update-kit`** instead of re-copying:

```bash
# Drop the new kit version into a staging folder inside the project (skip git + repo infrastructure)
rsync -a --exclude='.git' --exclude='.claude' --exclude='_backlog' --exclude='tools' \
  --exclude='.github' --exclude='LICENSE' --exclude='CONTRIBUTING.md' --exclude='CHANGELOG.md' \
  --exclude='CODE_OF_CONDUCT.md' --exclude='SECURITY.md' --exclude='.gitignore' \
  foureyes/ <project>/.claude/.kit-incoming/
```
Then open the project in Claude Code and run **`/update-kit`** (or `/update-kit <path-to-new-kit>`
and it stages for you). In one pass it:
- reads `.claude/.kit-manifest.json` (the install baseline) and does a **3-way merge** —
  BASE (what the kit shipped) vs MINE (your file) vs THEIRS (the new version) — so untouched files
  update silently and you're asked **only on real conflicts** (take-new / keep-mine / merge);
- **never touches** project-owned files (`PROJECT.md`, `CONTEXT.md`, `docs/adr/`, the backlog, or
  skills you created) — they aren't in the kit source, so the merge can't reach them;
- **re-adapts inline** (no separate `/bootstrap`): regenerates `settings.json`, `guard-bash.sh`,
  the `CLAUDE.md`/`.gitignore` blocks, and re-reconciles rule packs against the new version;
- backs up first and asks **keep or roll back**, then writes a fresh manifest.

Detection is hash-based, so it works even when `.claude/` is in `.gitignore` (git is not used).
A *legacy* project with no manifest yet falls back to a noisier 2-way diff once, then writes a
manifest so future updates are quiet.

## Remove the kit

Run **`/teardown`** and pick a scope:
- **Clean up leftovers** — delete build-time material (`_kit/`, `*.template.*`,
  `CLAUDE.snippet.md`, old `.bootstrap-backup/` snapshots), keep the working config.
- **Uninstall** — restore the project to its pre-kit state from the `.claude.bak/` /
  `CLAUDE.md.bak` backup (or, under git, `git checkout -- .claude CLAUDE.md && git clean -fd .claude`).

Bootstrap is reversible on its own too: it backs up before writing and asks **keep or roll
back** at the end, so a rejected run leaves no trace.

## Layout

```
foureyes/                     → its contents become <project>/.claude/
├── skills/{bootstrap,update-kit,teardown,idea,discover,analyst,prepare,spike,prototype,select-tech,implement,scaffold,code-review,refactor,diagnose,test,test-spec,tdd,arch-health,decompose,revisit,distill,clean-mvp,sweep,audit-security,deps,handoff}/
│         {grill,grill-with-docs,domain-model,codebase-design,api-design,threat-model,onboard,perf,to-prd,to-issues,triage,epic-status,close-epic,rollout,preflight,incident,retro,which-skill,prompt-master,writing-skills}/
├── agents/*.md             # 16 subagents (review/verify incl. finding-verifier + completeness-critic + plan-challenger, analysis, writers, research)
├── rules/_generic/*.md     # core.md is the ONLY always-on rule — evidence, done-is-external, decision pricing, honest reporting, merged from five earlier files by the 2026-08 tier cut (the bench found the tier bought cost, not quality); code rules paths:-scoped to **/* (code, code-quality, testing, resilience, service-layer, domain-events, observability, …); narrow on-demand (delegation, memory, planning-artifacts, parallel-wave-execution) scoped to where each fires
├── hooks/*.sh              # guard-bash, guard-secrets, format-file, sessionstart, precompact, subagent-stop, verify-stop, skill-hint (last two opt-in, unwired by default — see settings.*.example.json)
├── output-styles/review.md
├── schemas/finding.schema.json   # the Finding Contract as JSON Schema (structured fan-out output)
├── docs/{observability,agent-failure-modes,self-knowledge,decision-craft,working-with-agents,prompt-patterns,agent-teams}.md
├── PROJECT.template.md  settings.template.json  CLAUDE.snippet.md
├── settings.stop-gate.example.json  settings.skill-hint.example.json   # opt-in hook blocks to merge by hand
├── _kit/                    # build-time only — /bootstrap removes it after adapting
│   ├── KIT.md
│   ├── rules-library/{python,react-ts,ruby,rails,postgres}/ + PACKS.md
│   └── templates/commands/{commit,pr,mr}.md
├── assets/logo.svg
├── tools/validate-kit.py   # repo infrastructure, NOT copied in — frontmatter, listing budget,
├── .github/                #   dead links (markdown + backticked kit paths), hooks, JSON
│   ├── workflows/ci.yml
│   └── ISSUE_TEMPLATE/
├── CONTRIBUTING.md  CHANGELOG.md  CODE_OF_CONDUCT.md  SECURITY.md
└── LICENSE                 # MIT
```

Everything from `tools/` down is repo infrastructure and is excluded from the copy-in — it
validates the kit, it is not part of it. Run it before opening a PR:

```bash
python3 tools/validate-kit.py --stats
```

## Distribution model

FourEyes ships **copy-in**, not as a pure plugin — deliberately. As of 2026 the Claude Code plugin
model can't carry three things FourEyes depends on:

- **always-on `paths:`-scoped rules** — there's no `rules/` plugin component, and a plugin-root
  `CLAUDE.md` isn't loaded as context;
- **unprefixed commands** — plugin commands are mandatorily namespaced (`/foureyes:discover`), so
  `/discover` is only possible from files in the project's own `.claude/`;
- **an interactive `/bootstrap`** on install — there are no install-time lifecycle hooks.

So the product is the copy-in bundle + `/bootstrap`, and the lifecycle is three skills rather than
a package manager: **`/bootstrap`** installs and adapts, **`/update-kit`** upgrades in place
(3-way merge, keeps your adaptations), **`/teardown`** removes and restores.

A thin *installer* plugin — a marketplace wrapper whose one command clones the kit into your real
`.claude/` and then hands off to `/bootstrap` — would add discoverability without giving up either
property, and is the most likely future addition. It is deliberately **not shipped yet**: a
`.claude-plugin/marketplace.json` in a public repo root is not a draft, it is a live marketplace
anyone can add, and advertising an install path that has not been run end to end against a
throwaway project is the exact thing [`rules/_generic/core.md`](rules/_generic/core.md) calls a
guess dressed as done.
