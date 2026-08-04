---
name: select-tech
disable-model-invocation: true
description: >-
  Technology selection discipline — choose a library/gem/package/framework/external service
  (or decide to build it) via hard filters, an adversarial deep-dive on 2–3 finalists
  (issue-tracker-over-README, the hard-case probe, upgrade-path history, bus factor, escape
  cost), a scored matrix with one recommendation, and an adapter-seam integration contract.
  TRIGGER when: the user asks which library/gem/framework/service to use for X, wants to
  compare candidates, asks build-vs-buy, or a plan needs a new dependency chosen ("какую
  библиотеку взять", "what should we use for", "is there a gem for").
  DO NOT TRIGGER when: auditing dependencies already installed (use /deps), researching
  what the repo itself already has (use /discover), validating ONE already-chosen
  candidate's feasibility (use /spike), or questioning whether a PAST choice still holds —
  start from /revisit, which reopens it into this skill only on a broken assumption.
allowed-tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, AskUserQuestion, Write, Agent, Skill
effort: high
---

# Technology Selection: $ARGUMENTS

## Principle

Adopting a dependency is signing a **permanent trust relationship**: its bugs become your
bugs, its release cadence your upgrade tax, its abandonment your migration project. So the
selection is decision-craft applied to the supply chain: treat adoption as a heavy door —
and then **lighten it** (adapter seam, pinned version, escape plan) rather than pretending
the choice is casual. Three working truths this skill is built on:

- **The README is marketing; the issue tracker is the truth.** Every library demos
  beautifully on the case it was designed around. Its real shape is in the open issues
  that match *your* use case.
- **Probe your hard case, not the tutorial case.** The demo is optimized for the demo;
  fit is decided by the ugliest real requirement you have.
- **The best dependency is often one you already carry** — or 100 lines you own.

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` — **Stack** (runtime + versions), **Architecture** (where an
   integration would live), **Integrations**, **Conventions** (license policy if stated),
   **Plans location**. Missing/TEMPLATE → fall back to the root `CLAUDE.md` (always in context)
   when it carries the stack and architecture — note you're running without a kit profile; STOP to
   run `/bootstrap` first only if *neither* has them.
2. Read the **lockfile / manifest** (Gemfile.lock, package-lock.json, poetry.lock, go.sum…)
   — the installed ecosystem, versions, and *transitive* deps you already carry.
3. Check the Plans location for a prior selection on this topic — don't re-litigate a
   recorded decision without new evidence (also check `docs/adr/`).

## Phase 1 — The need, the hard case, and the zero option

Before any candidate is named:

- **Capability in one sentence** — what must this thing do (not which product does it).
- **The hard case** — the ugliest *real* requirement: the 100k-row import, the retry
  under partial failure, the RTL locale, the multi-tenant boundary. Written down FIRST,
  because Phase 4 probes it and marketing never mentions it.
- **Constraints** — license policy, runtime/version compat (from the lockfile), perf/size
  envelope, operational limits (self-hosted vs SaaS, data residency).
- **Horizon** (from the spec, or one question to the operator): a throwaway probe biases
  hard toward the zero option / stdlib; a living surface with a feature trajectory biases
  toward adopting the ecosystem (`core.md` → Horizon prices the build).
- **The zero option — always a candidate.** "Write it ourselves / stdlib / vendor 100
  lines" enters the matrix like any other option. For narrow needs, code you own and can
  read beats a dependency with 40 transitive deps; the threshold is honest scope — a
  regex is not a date library, and half of an auth system is a breach.

If the need is fuzzy enough that candidates can't be filtered, that's a framing problem —
route back through `/discover`/`/analyst` first.

## Phase 2 — Candidate sweep

- **Already installed?** Grep the lockfile and existing code first — the capability may be
  inside a dependency (or transitive dep) you already carry, or half-built in the repo
  (`/discover`'s territory; check its brief if one exists).
- **Ecosystem gravity**: what do your existing framework/major libs officially integrate
  with? First-party adapters age better than community glue.
- **The field**: WebSearch the registry + comparisons; for a genuinely open landscape,
  chain the global **`deep-research`** skill and fold its cited findings in. Collect
  5–10 names max — breadth here, depth in Phase 4.

**Verify-today rule:** every fact about a candidate — existence, API shape, maintenance
status, license — comes from a live source (registry page, repo, docs) fetched *now*, never
from memory. Recalled library knowledge is stale-by-default (`core.md`): the
library you remember may be renamed, abandoned, or two majors ahead.

## Phase 3 — Hard filters (kill fast, kill cheap)

Run every candidate through binary filters; record each kill with its reason:

- **License** compatible with the project's policy (and the licenses of *its* deps).
- **Runtime/version compat** with the lockfile reality (not with "latest").
- **Alive**: recent releases AND recent maintainer *responses* to issues/PRs — activity of
  the maintainer, not stars. Stars measure marketing; response latency measures support.
- **Security process**: advisories handled and disclosed. A project with well-handled
  CVEs beats one with zero CVEs and no security policy — the first has a process, the
  second has no audit history.
- **Weight**: install size + transitive dependency count within the envelope.

2–3 survivors proceed. If zero survive, the zero option or a constraint change is the
answer — say so; don't lower the bar silently.

## Phase 4 — Deep dive (the part nobody does)

For each finalist, in this order:

1. **Issue-tracker probe**: search its issues/discussions for *your hard case's* keywords.
   Open bugs, workaround threads, and "wontfix" verdicts on your use case are
   disqualifying evidence no benchmark outweighs. Cite the issue links.
2. **The hard-case sketch**: write (on paper, in the report — not in the repo) the
   10–30 lines that would implement YOUR hard case against the candidate's *real docs*
   (WebFetch). If the docs can't answer how, that's a finding; if the sketch needs
   fighting the library's grain, fit is wrong regardless of features.
3. **Upgrade-path history**: read the changelog/releases across the last 2–3 majors — did
   breaking changes come with migration guides and deprecation windows? A project that
   broke its users three times will do it a fourth; you are choosing your future upgrade
   tax.
4. **Bus factor**: contributor distribution and backing (foundation / company / one
   burning-out maintainer). One-maintainer is not a kill — but it prices the escape plan.
5. **Escape cost**: if this had to be replaced in two years — what leaks past the seam
   (data formats, schema, idioms in call sites)? Cheap-escape candidates get credit;
   lock-in gets priced, not ignored.

When finalists are close, spawn parallel agents one-per-candidate for steps 1–3
(`delegation.md` brief shape) — but the verdict synthesis stays here, not in an agent.

## Phase 5 — Matrix and verdict

| Candidate | Capability fit | Hard case | Maintenance | Upgrade history | Weight | Escape cost | Verdict |
|-----------|---------------|-----------|-------------|-----------------|--------|-------------|---------|

One **recommendation with reasoning** — which candidate and why it wins on the columns
that matter *here* (never a tie presented as a conclusion; `core.md` — a
recommendation is the deliverable). Each loser gets its one-line kill reason (that's what
makes the decision defensible in six months). If the winner still carries an unproven
load-bearing bet, the verdict is **"spike first"** with the exact hypothesis for `/spike`.
Genuine user-preference ties (cost vs. flexibility) → one `AskUserQuestion` with your
recommended default.

## Phase 6 — Integration contract

The selection isn't done until the door is lightened:

- **Adapter seam**: the dependency enters behind a project-owned interface **sized to
  actual use** — expose the 3 calls you need, not the library's 40. This keeps the choice
  swappable (two-way door), gives tests a boundary to mock (`testing` rules), and contains
  idiom leakage. Trivial-scope exceptions (a dev-only CLI tool) — say so explicitly.
- **Pin + provenance**: exact version pinned per the ecosystem's practice; note the
  registry/source. New-dep security posture follows `code.md` / `/deps`.
- **Record the decision**: write the selection report to the Plans location
  (`<plans>/<YYYY-MM-DD>-<slug>-tech-selection.md`) — matrix, kill reasons, hard-case
  sketch, escape notes; offer `/domain-model` to cut an ADR when the choice shapes
  architecture. Route onward to `/prepare` (the adapter seam becomes a plan step).

## Hard rules

- **No facts from memory** — every candidate claim is verified against a live source
  fetched this session, or labeled a guess and excluded from the matrix.
- **The zero option is always scored** — a matrix without "build/vendor it" is a
  leading question.
- **The hard case is probed for every finalist** — a selection that only checked the
  happy path selected the README, not the library.
- **One recommendation**, losers with kill reasons; "here are three options" without a
  verdict is homework returned (`core.md`).
- **No dependency without a seam decision** — adopt-behind-adapter, adopt-bare (declared,
  with why), or don't adopt.
- **Read-only on app code** — the only file you create is the selection report.

## See also

- `/deps` — audit of dependencies already installed; `/spike` — validate the winner's
  load-bearing bet; `/discover` — what the repo already has; `/rollout` — replacing an
  incumbent dependency in stages (strangler).
- `rules/_generic/core.md` — doors, probes, falsifiable confidence.
