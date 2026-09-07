---
name: decompose
disable-model-invocation: true
description: >-
  Service-architecture decision discipline — decide monolith vs modular monolith vs
  extracting a service, per candidate boundary, on evidence: real extraction drivers
  (deploy contention, asymmetric scaling, failure isolation, team ownership) weighed
  against the distributed tax, with "extract the seam before the service" as the
  governing rule. Verdict per boundary: STAY / MODULARIZE / EXTRACT / MERGE, recorded as an
  ADR and routed to the right executor.
  TRIGGER when: the user asks "should we split this into services", "monolith or microservices",
  "extract X into its own service", "is it time to break this up", "should we merge these two
  services back", or a plan proposes a new service and the boundary hasn't been justified.
  DO NOT TRIGGER when: the user wants in-process module/interface design (use
  /codebase-design), a whole-tree rot scan (use /arch-health), the extraction is already
  decided and needs a shipping strategy (use /rollout), or a past architecture decision
  needs re-examination first (use /revisit).
allowed-tools: Read, Grep, Glob, Bash, Write, WebFetch, WebSearch, AskUserQuestion, Agent
effort: high
---

# Service Decomposition: $ARGUMENTS

`$ARGUMENTS` names the candidate boundary ("billing", "the notifications module") or an existing
service to audit; empty = survey the whole system, extraction candidates and existing splits both.

## Principle

A service boundary is not a code-quality tool — it is an **organizational and operational**
tool that happens to involve code. Splitting a process buys independent deploys, independent
scaling, and failure isolation; it pays for them with network partial-failure, the loss of
cross-boundary transactions, contract versioning, and an operational floor per service.
Messy code is never a driver: **a mess cut in two is two messes joined by a network**.

The governing rule is **extract the seam before the service**. Every good service boundary
must first exist and hold as a clean in-process module boundary — own interface, own data
access, no reach-ins. If the boundary can't be drawn inside one process, the network will
not draw it for you. This is `core.md`'s door rule: extraction is a heavy,
nearly-one-way door, but **modularization is how you change the door** — a proven in-process
seam makes later extraction cheap and is worth having even if you never extract. So the
default verdict is always the modular monolith, and extraction must argue its way past it.

This skill **decides and records** — it does not restructure. Execution routes out
(Phase 4).

## Phase 0 — Load profile

**Tooling preflight — one call, before step 1.** Some tools this skill relies on are **deferred**
by the harness: the session lists them by name only and loads their schemas on demand, so calling
one before it is fetched fails. Listing a tool in `allowed-tools` does **not** un-defer it. Issue
a single `ToolSearch` up front covering the whole run — `select:WebFetch,WebSearch` (Phase 1's
live feasibility checks on infra and platform limits) — instead of one round-trip per discovery.
A name already loaded costs nothing to include; a schema discovered missing mid-run costs a turn.

1. Read `.claude/PROJECT.md` — **Architecture** (layers, module map, dependency direction),
   **Integrations** (existing infra: queues, gateways, deploy platform), **Commands**. If
   missing or still `TEMPLATE`, fall back to the root `CLAUDE.md` (always in context) when it
   carries those facts — proceed on it, noting you're running without a kit profile. Only if
   *neither* has them, **STOP** and tell the user to run `/bootstrap` first.
2. Read `CONTEXT.md` / `CONTEXT-MAP.md` if present — bounded contexts are the natural
   candidate boundaries; name candidates in their terms.
3. Read `docs/adr/` (or the ADR location in `PROJECT.md`) — a prior decision about this
   boundary means **start at `/revisit`**, not here: reopening it requires a broken
   assumption, not a second opinion.
4. Read `skills/codebase-design/SKILL.md` for the seam/interface vocabulary — every
   boundary statement uses it — and `WHEN-TO-CUT.md` for the tests a boundary must pass
   (axis of change, writer census, next feature).

## Phase 1 — Evidence, not vibes

Collect per candidate boundary. Fan out `arch-tracer` agents for the coupling map on
anything beyond a small tree; pass `.claude/schemas/finding.schema.json` for mergeable
output. Ground every claim in `path:line` or a command's output.

**Code evidence (agents can find this):**
- **Runtime coupling** — synchronous call chains crossing the candidate boundary, shared
  tables/schemas, shared transactions, shared caches, shared in-memory state. Each one is
  either severed before extraction or becomes a distributed failure mode after it.
- **Data ownership** — can each side own its data outright? A table written by both sides
  is the single strongest STAY/MODULARIZE-first signal.
- **Connection budget** — services × pool size × expected instances against the store's
  ceiling; waits surface as request timeouts and tripped breakers, not connection errors.
- **Change coupling** — `git log --format=%H --name-only` mined for commits touching both
  sides of the boundary: code that ships together wants to live together. Independent
  change histories support a split; interleaved ones refute it.
- **Scaling asymmetry** — evidence (from `/perf` reports, profiles, infra dashboards named
  in Integrations) that one part needs materially different resources or scale.

**Organizational evidence (agents cannot see the org — ASK, never guess):**
Use `AskUserQuestion` for: team count and ownership map (Conway's law: the service
topology you can sustain is the team topology you have), deploy cadence and who blocks
whom, on-call/ops capacity, and the platform's operational maturity (CI/CD per service,
observability, service discovery). **One team ≈ one deployable** is the reference class;
a one-team org extracting microservices is buying tax with no driver.

**External evidence (research, when the answer isn't in the repo):**
Platform capabilities, event-bus/gateway options, reference-class outcomes for this kind
of split — verify live via WebSearch/WebFetch; route a load-bearing unknown ("can our
platform even run N services?") to `/spike`, and an infra component choice (broker,
gateway) to `/select-tech`. Never decide on remembered facts about platforms or tools.

## Phase 2 — Weigh drivers against the tax

**Real extraction drivers** (each needs Phase-1 evidence to count):

| Driver | Evidence that makes it real |
|--------|-----------------------------|
| Independent deploy cadence | releases demonstrably blocked/serialized across the boundary |
| Asymmetric scaling | measured resource profile divergence that replicas or sharding cannot absorb |
| Failure isolation | a part whose failure must not take the rest down (and currently can) |
| Team ownership | a real team wanting an independent roadmap for exactly this boundary |
| Divergent constraints | runtime/latency/compliance needs one side genuinely can't share |

**Fake drivers — name them when you see them, they never justify extraction:**
"the code is a mess" (→ `/arch-health`), "microservices are best practice", "it'll be
easier to understand" (locality *drops* across a network), "we might need to scale
someday" (speculative scale = STAY; extract when measured), résumé-driven architecture,
"it's too big" / "it's too small" (size is not a finding — co-change is).
**Against every driver that counts, name the boring alternative** — a bigger machine, reassigned
ownership, a deploy pipeline replacing manual testing and long-lived branches — say why it is
insufficient, and name the measure that will show in three months whether the split worked.

**Vetoes — no driver outweighs these; when one fires the verdict is STAY and the report says
which.** *Atomicity*: two updates the business needs both-or-neither stay in one transaction and
one service — a saga buys "both eventually, or an observable compensation". *Consistent read*: a
decision needing one consistent view of both sides must read it from one store. *Operated by the
customer*: someone else's per-service ops floor is not yours to spend — cap at MODULARIZE.

**The distributed tax — the extraction side must accept ALL of these, listed explicitly:**
network calls that partially fail (timeouts, retries, idempotency per `resilience` rule),
no cross-service transactions (sagas / eventual consistency where a `BEGIN` used to do; durable
execution is a third option, priced in class limits not vendor ones — deterministic replay, and
workflow code versioned while old runs are still in flight),
versioned contracts between the parts (Hyrum's law now applies internally), per-service
observability + deploy + on-call floor, harder local dev, and data duplication where
joins used to be — plus the **agent tax**, which nobody prices in: one user-visible flow
now spans N repos, N deploys, and N telemetry stacks, so no single agent session can trace
it end-to-end with Read and Grep. Comprehension shifts from code-reading (cheap, always
available) to distributed tracing (needs the observability floor *already built*). The
monolith's most under-priced asset is that its entire truth fits one context window.

**Which axis?** A cut runs along **abstraction** (layers inside one deployable), **subdomain**
(services) or **instances** (replicas, shards): say in one line why the other two do not answer
this pressure, and while the domain is still being learned cut along abstraction only.

**Verdict per candidate boundary:**

- **STAY** — no evidenced driver. The monolith is the correct architecture; say so
  plainly. A monolith serving its load with one team is a success, not a smell.
- **MODULARIZE** — drivers are real or plausible **but** Phase-1 found reach-ins, shared
  data, or interleaved change history. Make the boundary real in-process first: own
  interface, own data access, composition-root wiring. This is the default when in doubt —
  it captures most of the benefit, keeps transactions, and leaves the door open.
- **EXTRACT** — evidenced drivers outweigh the accepted tax **and** the in-process seam
  already exists and holds (no reach-ins, data ownable, contracts nameable). Both
  conditions, not either. **Name the remainder**, not just the piece cut out: one sentence,
  no "and", for what the other side does. A remainder that survives only as "the rest of X"
  means the cut is in the wrong place — move it, cut into three, or leave it whole.
- **MERGE** — the boundary already exists and is wrong: co-change, lockstep deploys, a shared
  transaction, workflow, hot domain code or unownable data. Name the blast radius bought back.

## Phase 3 — Grill and record

Take the top-ranked verdict (user picks via `AskUserQuestion` if it's a genuine toss-up)
and `/grill` it: the exact interface at the seam, who owns which data, what happens on
partial failure, the migration's first reversible step. Then record the verdict — including
STAY — as an ADR via `/domain-model`, with the drivers, the accepted tax, and the
assumptions it rests on stated explicitly (that's what a future `/revisit` will test).

## Phase 4 — Route to the executor

| Verdict | Route |
|---------|-------|
| STAY | nothing to build; if the mess prompted the question, → `/arch-health` |
| MODULARIZE | `/prepare` → `/implement` (large) or `/refactor` (small, local) |
| EXTRACT | `/rollout` — strangler-fig staged strategy; each stage through `/prepare` → `/implement` |
| MERGE | `/rollout` — merging back is a migration; `/revisit` first if an ADR recorded the split |
| Missing evidence blocked a verdict | `/spike` (feasibility) · `/select-tech` (infra component) |

## Output

`Write` the report below to the **Plans location** from `PROJECT.md` (e.g.
`<plans>/<YYYY-MM-DD>-decompose.md`; git policy per `PROJECT.md` → Artifact git policy),
then present it:

```
## Decomposition — <scope>

### Verdicts
| Boundary | Verdict | Drivers (evidenced) | Blockers / tax accepted | Route |

### Evidence
- <boundary>: coupling `path:line`…, change-coupling stats, org facts (from user)

### Recommended next
- ⭐ <boundary> — <verdict> — <one-line why> → <route>

### ADR
- <recorded / to record via /domain-model>
```

## Hard rules

- **Decide and record only** — never restructure here; execution goes through Phase-4 routes.
- **Default is the modular monolith.** Extraction must clear both bars: evidenced drivers
  AND a proven in-process seam. Never extract along a seam that doesn't hold in-process.
- **Org facts come from the user.** Team topology, ops maturity, deploy pain — ask; never
  infer from code.
- **Fake drivers are findings.** Name them in the report instead of acting on them.
- **STAY is a first-class verdict.** Record it as an ADR so the question isn't relitigated.
- **External facts verified live**, never from memory.

## Cross-reference

- **`/codebase-design`** — the seam/interface vocabulary; MODULARIZE work is designed in it.
- **`/arch-health`** — finds the rot that often masquerades as an extraction driver.
- **`/revisit`** — start there when a prior ADR already covers this boundary.
- **`/rollout`** — the staged execution of an EXTRACT or MERGE verdict, and the behaviour freeze
  that keeps its stages reversible.
- **`/domain-model`** — bounded contexts in; the verdict ADR out.
- **`/select-tech`, `/spike`** — infra component choice / feasibility unknowns.
