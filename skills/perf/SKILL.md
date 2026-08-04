---
name: perf
disable-model-invocation: true
description: >-
  Measurement-first performance work — define the budget and metric, measure a reproducible
  baseline, profile to find the REAL hotspot, fix the biggest lever first (algorithmic >
  batching/caching > micro), re-measure after every single change, stop at the budget.
  TRIGGER when: something is slow, memory-hungry, or the user wants it faster/cheaper
  ("optimize", "why is this slow", "speed this up", "reduce latency/memory").
  DO NOT TRIGGER when: it's a correctness bug that happens to involve time (timeout because
  of a hang → /diagnose), or a whole-codebase perf *audit* with no target metric (use the
  performance-analyzer agent directly).
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, WebFetch, AskUserQuestion, Agent
effort: high
---

# Performance Work: $ARGUMENTS

## Principle

**No optimization without a measurement — intuition names the wrong hotspot more often
than not**, and a model's intuition is trained on other people's codebases. The profile
decides where to work; the baseline decides whether it worked; the budget decides when to
stop. An optimization that was never measured is a complexity purchase with an unknown
price and an imagined benefit.

## Phase 0 — Load profile

Read `.claude/PROJECT.md` (Commands — test/run/bench if present; Architecture;
Integrations — external calls are frequent culprits) and applicable rules. Missing/TEMPLATE
→ fall back to the root `CLAUDE.md` (always in context) when it carries those facts, noting you're
running without a kit profile; only if *neither* has them, STOP, `/bootstrap` first.

## Phase 1 — Budget and metric (before any code is read)

- **One metric, named precisely**: p95 latency of endpoint X / wall-time of job Y / RSS
  after N ops / cold-start / throughput. "Faster" is not a metric.
- **The budget**: the number at which this is *done* ("p95 < 300ms", "import of 100k rows
  < 2min"). From the user if it's product-facing (one question, with your recommended
  number); from you (stated) if it's internal. **No budget → no stopping criterion →
  optimization becomes a hobby** — don't start without one.
- **Realistic load shape**: the N, the data skew, the concurrency this must hold at
  (`code-quality.md` → algorithmic sizing). Measuring at toy N is measuring nothing.

## Phase 2 — Baseline, reproducibly

Build the smallest **repeatable** measurement: the profile's bench command, a timing
harness around the real operation, or a scripted request loop — warm-up excluded, ≥3 runs,
report median + spread. Save the exact command in the report so anyone can re-run it.
If the operation can't be exercised reproducibly, that's the first task — a perf fix you
can't measure is a guess wearing a stopwatch.

## Phase 3 — Profile: find where the time actually goes

Use the stack's profiler (from rules/PROJECT.md; WebFetch its docs if unsure — not from
memory). No profiler available → bisect with coarse timers around the operation's phases.
**Predict before you peek** (`core.md`): write down where you *think* the time
goes, then look — a wrong prediction here is the cheapest possible lesson about this
codebase. Attribute the budget: "78% in <fn> at `path:line`, of which 60% is the N+1 to
<service>". The top item is the only sanctioned target.

## Phase 4 — Fix the biggest lever, one change at a time

Lever order — never micro-tune while a bigger lever is unpulled:

1. **Don't do the work**: cache the answer, dedupe the calls, early-exit, move it
   off the hot path / async, do it once at startup.
2. **Do it in bulk**: batch the N+1 (queries, HTTP, IPC), vectorize, stream instead of
   materializing.
3. **Do it with the right algorithm/structure**: the O(n²) scan → index/hash/sort;
   the linear search in a loop → set; per `code-quality.md` sizing.
4. **Micro**: allocation churn, serialization, hot-loop costs — only inside the measured
   hotspot, only after 1–3 are exhausted.

Per change: state the expected effect ("batching should cut ~60% of the 78%"), apply
**one change**, re-run Phase 2, keep or revert on the numbers. Two changes at once =
attribution destroyed. Correctness stays gated: the suite runs after each kept change.

**Caching is a liability, declared**: every cache added names its invalidation trigger,
staleness bound, and memory ceiling — an uninvalidated cache is a scheduled `/diagnose`
session (and often a security bug: per-user data in a shared cache).

## Phase 5 — Stop at the budget

Budget met → **stop**. Further optimization is negative-value work: complexity bought
with no requirement behind it. Report over-budget ideas as a ranked "if it's ever needed"
list instead of implementing them. Budget NOT reachable at this altitude (the architecture
is the bottleneck — sync pipeline, chatty protocol, wrong storage) → **stop and escalate**
per `core.md`: that's a `/prepare`-level redesign decision, not a hot-loop patch.

## Report

```
## Perf: <operation> — <BUDGET MET / NOT MET / ESCALATED>
Metric & budget · Baseline → Final (median ± spread, exact command)
Profile: where the time went (top-3, % + path:line)
Changes kept: <one line each — lever, expected vs actual effect>
Changes reverted: <what didn't pay + the number that said so>
Caches added: <trigger / staleness / ceiling> or none
Regression guard: <perf test / bench command + threshold recorded where>
Not optimized (over budget met): <ranked list>
```

Offer to add the bench command + threshold as a regression guard (a perf test or a CI
step) — a perf win without a tripwire erodes silently.

## Hard rules

- **No edit before a baseline; no keep without a re-measure.** Numbers, not adjectives.
- **One change per measurement.**
- **The profile picks the target** — never optimize code the profile didn't indict,
  however ugly it looks (route that to `/refactor` as a separate pass).
- **Suite green after every kept change** — a fast wrong answer is a regression.
- Report expected-vs-actual for every change: misses are calibration data, not shame.

## See also

- `performance-analyzer` agent — broad audit / second opinion on a hotspot.
- `/diagnose` — when "slow" is actually "hanging/broken"; `/rollout` — shipping a risky
  perf change behind a flag; `rules/_generic/core.md` — predict-before-peek.
