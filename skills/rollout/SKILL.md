---
name: rollout
disable-model-invocation: true
description: >-
  Design a safe rollout/migration strategy for a risky or irreversible change — expand-contract
  (parallel change), strangler fig, feature flags / dark launch / canary — as a staged plan where
  every stage is independently deployable, verifiable, and reversible.
  TRIGGER when: the user asks how to ship/deploy/migrate something safely — a schema or data
  migration, an API contract change, a library/system replacement, a risky behavior change, or
  mentions zero-downtime, feature flags, canary, backfill, or "how do we roll this out".
  DO NOT TRIGGER when: the change is a mechanical many-file edit with no production sequencing
  concern (use /sweep), the user wants a release-readiness check on work already done (use
  /preflight), or an ordinary reversible code change is being planned (use /prepare).
allowed-tools: Read, Grep, Glob, Bash, Write, WebFetch, AskUserQuestion
effort: high
---

# Rollout Strategy

Change to roll out: $ARGUMENTS

## Principle

A risky change is never shipped as one atomic act of courage. It is decomposed into a
sequence of stages where **each stage is deployable alone, verifiable alone, and reversible
alone** — so maximum learning happens before the one-way step, and the one-way step is as
small as it can be made. This is `core.md`'s door rule made operational: when a
change looks irreversible, first try to **change the door**.

This skill designs the strategy and writes the staged plan. It does not deploy anything —
execution of each stage goes through the normal pipeline (`/prepare` → `/implement`), and
deploy/migrate commands are always suggested, never run.

## Phase 0 — Load profile

- [ ] Read `.claude/PROJECT.md` — note **Architecture**, **Commands** (test / run / deploy /
      migrate, if present), **Integrations** (monitoring/error tracking — verification signals
      live there), and **Plans location** (the strategy doc lands there).
- [ ] Read applicable `.claude/rules/*` (e.g. a postgres pack's migration rules).
- [ ] If `PROJECT.md` is missing **or still `TEMPLATE`**, fall back to the root `CLAUDE.md` (always
      in context) when it carries the architecture and deploy/migrate commands — note you're running
      without a kit profile. Only if *neither* has them, STOP and tell the user to run `/bootstrap`.

## Phase 1 — Characterize the change

Before picking a pattern, establish the facts that select it (cite evidence — `path:line`,
schema definitions, caller inventories; per `core.md` this gates one-way
actions on *observed* evidence):

- [ ] **What mutates?** Code only / schema / data rows / an external contract (API consumers,
      message formats, webhooks) / infrastructure.
- [ ] **Find the one-way components.** Rewritten or dropped data, messages sent, contracts
      third parties depend on, names published. Everything else is two-way and needs no
      ceremony. If **no one-way component exists and no old/new coexistence is needed**,
      say so and route to `/prepare` — don't stage what doesn't need staging.
- [ ] **Who reads/writes the thing being changed?** Inventory the call sites / consumers
      (grep; for external consumers, what the repo can prove — logs, API docs, contract
      tests) — the coexistence window exists exactly for them.
- [ ] **What signal proves each stage healthy?** Tests, metrics, error rates, row counts —
      from PROJECT.md → Integrations/Commands. **A stage without a checkable signal cannot
      be in the plan** — find the signal or add the instrumentation as its own prior stage.
- [ ] **Blast radius if the worst stage fails anyway** — who/what is affected, for how long,
      recovered how.

## Phase 2 — Pick the pattern

| Situation | Pattern |
|---|---|
| Schema/data shape changes under live readers+writers | **Expand–contract** (parallel change): expand (add new alongside old) → migrate writers → backfill → migrate readers → verify adoption is total → contract (drop old) |
| Replacing a system/module/library wholesale | **Strangler fig**: route through a seam, move one slice at a time behind it, old path stays alive until the new one has eaten everything |
| Behavior change with product/user risk | **Flag + progressive exposure**: dark launch (run hidden, compare outputs) → canary (small %) → ramp → 100% → remove the flag |
| External contract change (API/message consumers you don't control) | **Versioned coexistence**: publish v2 alongside v1, migrate consumers, deprecate with evidence of zero v1 traffic, then remove |
| One-shot data fix (backfill/correction) | **Rehearse–snapshot–apply**: dry-run against a copy with row-count expectations stated first (predict-before-peek), snapshot/backup, apply, verify counts |

Combine when the change spans rows (a strangler slice may itself need expand–contract).
Present the chosen pattern and *why the situation's facts select it* — one paragraph, plus
the rejected runner-up with the fact that killed it.

## Phase 3 — Write the staged plan

For **every stage**, all four fields — a stage missing one is not a stage:

```
### Stage N — <name>
**Change**: what ships (code/schema/config), and whether it's two-way or one-way.
**Verify**: the signal that proves it healthy, with the expected value stated
  BEFORE looking (e.g. "v1 endpoint traffic: expect 0 over 7 days").
**Bake**: how long / what volume the stage must survive before the next one.
**Rollback**: the concrete undo for THIS stage (command/flag/revert) — and its limits.
```

Sequencing rules (hard):

- **The contract/destructive stage comes last** and is gated on *observed* evidence of zero
  dependence on the old path (traffic counts, log queries — not on "should be fine").
- **Every stage before the one-way stage must be safe to stop at** — the system runs
  indefinitely in any intermediate state (that's what makes the sequence abortable).
- **Old and new must not silently diverge during coexistence**: name the mechanism that
  keeps them consistent (dual-write, sync job, comparison shadow-read) and the check that
  would catch drift.
- **A kill switch is not a rollback.** State both when they differ (a flag flips fast; a
  dropped column comes back slow — from the snapshot named in the plan).

Run a **pre-mortem** on the finished sequence (`core.md`): "the rollout failed —
why?" The top two causes get a mitigation stage, a widened bake, or an added signal.

## Phase 4 — Deliver

Write the strategy to the **Plans location** from PROJECT.md
(`<plans>/<YYYY-MM-DD>-<slug>-rollout.md`) — this doc *is* the deliverable; confirm before
writing per the Artifact-Continuity Contract (`planning-artifacts.md`). Report: pattern +
why, the stage table, the one-way stage highlighted, and the pre-mortem outcome. Each stage
then flows through `/prepare` → `/implement` as normal work.

## Hard rules

- **Never execute the rollout.** Deploy/migrate/flag commands are suggested for the user to
  run — this skill produces a strategy, not a deployment.
- **No stage without a Verify signal and a Rollback.** "Monitor closely" is not a signal;
  "revert if needed" is not a rollback.
- **The destructive step is gated on observed zero-dependence evidence**, never on
  schedule ("after two weeks") alone — time is a proxy, traffic is the fact.
- **If nothing is one-way, say so and stand down** to `/prepare` — ceremony where wrong is
  cheap is waste (`core.md`).

## See also

- `/sweep` — the mechanical many-file edit inside a stage (inventory → batches → re-scan).
- `/preflight` — release-readiness gate before each stage ships.
- `/incident` — if a stage goes wrong in production, mitigate first.
- `rules/_generic/core.md` — doors, pre-mortem, predict-before-peek.
