[← README](../../README.md) · **English** · [Русский](../ru/why.md)

# Why FourEyes looks like this

## The discipline layer — what you won't find in another kit

Most kits give you *workflow*. The pipeline shape (`discover → ship`, one-question interviews, living glossaries) is real but not rare — it's shared methodology, and FourEyes [credits its lineage](#why-foureyes-not-another-agent-collection). What sets FourEyes apart is the **discipline layer underneath the workflow**: an explicit model of *how agents fail* and countermeasures wired into structure, not hope. If you take one thing, take this.

- **A field catalog of 22 agent failure modes** — [`docs/agent-failure-modes.md`](../../docs/agent-failure-modes.md). Each entry is *symptom → mechanism (why it happens) → countermeasure → where the kit already wires it*. `/retro` classifies recurring problems against it; `/writing-skills` designs new skills *against* it. Most kits ship "best practices"; this ships a theory of the defects and the fix for each.
- **Generation-from-the-inside rules** — [`docs/self-knowledge.md`](../../docs/self-knowledge.md) + the distilled [`self-knowledge`](../../rules/_generic/core.md), [`diligence`](../../rules/_generic/core.md), and [`decision-craft`](../../rules/_generic/core.md) rules. These target the defaults a strong model *won't* self-correct: recalled facts are stale-by-default (verify against the lockfile, not memory); evidence is derived before the verdict (a verdict written first anchors the analysis under it); you can't fairly review what you just wrote (real review goes to a fresh context); rewrites regress to the training mean (surprising code is load-bearing until proven decorative); effort is *allocation, not motivation* (done is an external list, the hard part goes first, homework isn't handed back). This is behavioral override, not encouragement.
- **Greppability as an architectural contract** — [`rules/_generic/code.md`](../../rules/_generic/code.md). Premise: *the next maintainer is an agent that navigates by exact-name search*, so every future inventory (a `/sweep`, a dead-code proof, an audit) is only as complete as what search can see. One symbol = one greppable definition site; no runtime-constructed names outside a declared, enumerable seam. Boilerplate is not an excuse — the human motive for metaprogramming (typing fatigue) doesn't apply to an agent, while its costs hit agents harder.
- **Adversarial, lens-diverse verification** — the **Finding Contract** across the whole fleet, plus `finding-verifier`'s **panel mode**: N clones briefed identically share blind spots (their agreement is an echo), so CRITICAL findings get one *distinct lens* per instance (correctness / security / does-it-reproduce), default-REFUTED, majority vote. Independence is bought with framing, not head-count.

The workflow is the part you'll recognize from other kits. The discipline layer is the part that makes a 10-agent review return signal instead of confident noise.

## Why FourEyes, not another agent collection

Most Claude Code repos are *catalogs* — a pile of independent agents you wire together yourself. FourEyes is the opposite: **one opinionated path with quality gates**, engineered so it stays generic.

- **A pipeline, not a pile.** `discover → spec → plan → build → review` as a single self-propelling flow, not 200 à-la-carte agents.
- **Subagents that respect your context window.** Every finder honors one **Finding Contract** — bounded, structured findings (`path:line` + severity + effort + concrete harm) — so a 10-agent review returns signal, not an 8k-token dump. This discipline, applied across the whole fleet, is the part you won't find elsewhere.
- **Drop-in and stack-adaptive.** `/bootstrap` reads your repo into `PROJECT.md`; skills stay generic and adapt at runtime. Porting = copy + bootstrap, never editing skills. The design is stack-neutral by construction — no skill names a language — but it has been *exercised* on Python; the ruby / rails / react-ts / postgres packs ship untested by the bench.
- **Survives long work.** The plan is the single source of truth across compaction and sessions (the *Artifact-Continuity Contract*) — resume mid-feature without re-explaining. Stage gates make the pipeline mechanical: each stage checks the previous artifact on entry and returns a weak one with reasons, instead of silently compensating downstream.
- **A learning loop, not a static pack.** Every `/implement` writes a Deviation Report; `/retro` mines them (plus handoffs and diagnose logs) for recurring, evidence-verified patterns and folds the lessons back into your rules and profile — the kit adapts to your project over time.

**Lineage — honest about its roots.** FourEyes builds on ideas popularized by [Matt Pocock's skills](https://github.com/mattpocock/skills) and [obra/superpowers](https://github.com/obra/superpowers) (the relentless one-question interview, living ubiquitous-language + ADRs, deep-module design, a discover→ship methodology — with nods to Eric Evans's DDD and John Ousterhout's *A Philosophy of Software Design*). What FourEyes adds is a **disciplined multi-agent layer** (the Finding Contract) and a **portable, stack-adaptive distribution** (`PROJECT.md` + `/bootstrap` + stack rule packs) so the whole methodology drops into any repo and stays generic.

What is borrowed is *method*, not text — no file here is a copy of theirs, and the two kits' skills differ in structure, phases, and output format. Both upstreams are MIT, as is FourEyes ([LICENSE](../../LICENSE)); the credit above is owed to the ideas regardless of what the license requires.

## FourEyes vs the two common archetypes

| | **Catalogs** (wshobson, VoltAgent) | **Methodologies** (superpowers, mattpocock) | **FourEyes** |
|---|---|---|---|
| Shape | à-la-carte agents you wire up | opinionated skill flow | opinionated flow **+ portable distribution** |
| Adapts to your repo | manual | via a root doc | `/bootstrap` → `PROJECT.md`, skills stay generic |
| Multi-agent noise control | per-agent, ad hoc | light | one **Finding Contract** across the whole fleet |
| Always-on rules | rare | rare | generic + stack `paths:`-scoped rule packs |
| Context survival | — | plan/handoff files | Artifact-Continuity Contract (plan = SSOT) |

## Distribution model

FourEyes ships **copy-in**, not as a pure plugin — deliberately. As of 2026 the Claude Code plugin model can't carry three things FourEyes depends on:

- **always-on `paths:`-scoped rules** — there's no `rules/` plugin component, and a plugin-root `CLAUDE.md` isn't loaded as context;
- **unprefixed commands** — plugin commands are mandatorily namespaced (`/foureyes:discover`), so `/discover` is only possible from files in the project's own `.claude/`;
- **an interactive `/bootstrap`** on install — there are no install-time lifecycle hooks.

So the product is the copy-in bundle + `/bootstrap`, and the lifecycle is three skills rather than a package manager: **`/bootstrap`** installs and adapts, **`/update-kit`** upgrades in place (3-way merge, keeps your adaptations), **`/teardown`** removes and restores.

A thin *installer* plugin — a marketplace wrapper whose one command clones the kit into your real `.claude/` and then hands off to `/bootstrap` — would add discoverability without giving up either property, and is the most likely future addition. It is deliberately **not shipped yet**: a `.claude-plugin/marketplace.json` in a public repo root is not a draft, it is a live marketplace anyone can add, and advertising an install path that has not been run end to end against a throwaway project is the exact thing [`rules/_generic/core.md`](../../rules/_generic/core.md) calls a guess dressed as done.
