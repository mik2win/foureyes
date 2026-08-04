---
name: api-design
disable-model-invocation: true
description: >-
  Design a public contract (HTTP/REST, RPC, webhook, CLI, or library API) before building it —
  consumers & compatibility promise first, resource model in the domain language, the
  contract checklist (error model, pagination, idempotency, partial updates, versioning),
  worked request/response examples including errors, and a consumer's-eyes review pass.
  TRIGGER when: designing or extending an API/endpoint/webhook/CLI surface or a library's
  public interface — "design the API", "какой сделать контракт/эндпоинт", adding endpoints
  consumers outside this repo will call.
  DO NOT TRIGGER when: designing an internal module seam (use /codebase-design), or the
  contract exists and the question is shipping a change to it safely (use /rollout).
allowed-tools: Read, Grep, Glob, Bash, WebFetch, AskUserQuestion, Write
effort: high
---

# API Design: $ARGUMENTS

## Principle

A public contract is the kit's heaviest door: once a consumer you don't control depends on
it, every field name is permanent and every quirk is load-bearing (Hyrum's law — with
enough consumers, *all* observable behavior becomes the contract, including your bugs).
So the design order is fixed: **consumers and compatibility promise first, then the
resource model, then the mechanics** — and consistency with the house's existing API
beats global best practice every time: one project, one dialect.

## Phase 0 — Load context

Read `.claude/PROJECT.md` (Architecture — where API code lives; Domain; Integrations),
`CONTEXT.md` (names come from the ubiquitous language), and — decisive — **grep the
existing API surface**: current endpoints/commands, their casing, envelope shape, error
format, auth pattern. Missing/TEMPLATE profile → fall back to the root `CLAUDE.md` (always in
context) when it carries the architecture/integrations (note you're running without a kit profile);
STOP for `/bootstrap` first only if *neither* has them — the API-surface grep runs regardless. An `/analyst`
spec for the feature is the ideal input; without one, get WHAT/WHY first.

## Phase 1 — Consumers and the compatibility promise

- **Who calls this** — own frontend / other internal services / third parties / public?
  Each step outward hardens the door (`core.md`).
- **Can you break them?** Sets the promise: internal-only (coordinated change possible) vs
  versioned-public (additive-only within a version; breaking = new version via `/rollout`
  coexistence). Write the promise into the contract doc — it's the contract's contract.
- **The hard consumer case** — the ugliest real call pattern (bulk import, polling at
  scale, retry storms, mobile on flaky network). Designs are judged against it in Phase 5.

## Phase 2 — Resource model, in the domain language

Name the nouns from `CONTEXT.md`/domain vocabulary — the API is the domain made visible,
not the database made public:

- Resources, their identifiers (opaque IDs; never enumerable integers on anything
  tenant-scoped), relationships and nesting depth (flat + link beats deep nesting).
- Which internal fields are **not** exposed (default-closed: expose what the consumer
  needs, not what the model has — every exposed field is forever, per Hyrum).
- Actions that aren't CRUD: model state transitions explicitly (`/orders/{id}/cancel`
  or a status-transition body — pick the house's existing dialect) instead of overloading
  generic updates with side effects.

## Phase 3 — The contract checklist

One decision per row; "same as existing API" is the default answer, deviations are
declared with a reason:

| Concern | Decide |
|---|---|
| **Error model** | One envelope for all errors: machine-readable `code`, human `message`, per-field details for validation. Status codes used honestly (4xx consumer / 5xx producer). No existence oracles on protected resources (404 over 403 where hiding matters — per `/threat-model`). |
| **Pagination** | Cursor-based for anything unbounded (offset breaks under concurrent writes); page size capped; the cap documented. Every list endpoint paginates from day one — retrofitting pagination is a breaking change. |
| **Filtering/sorting** | Explicit whitelisted params, never pass-through to the query layer. |
| **Idempotency** | Every non-GET states its retry story. Money/creation ops take an idempotency key; consumers on flaky networks WILL retry (`resilience.md`). |
| **Partial updates** | Pick the house convention (PATCH semantics / explicit fields); define null-vs-absent once, project-wide. |
| **Formats** | Timestamps (UTC ISO-8601), money (integer minor units or decimal-as-string — never floats), enums as strings with an "unknown value" evolution rule for consumers. |
| **Auth & authz** | House mechanism; per-object checks stated per endpoint (role × action from the spec's matrix). |
| **Limits** | Rate limits, payload caps, list caps — numbers, not vibes; the DoS row of `/threat-model` lands here. |
| **Evolution** | Additive-only within version; deprecation = header/doc + sunset date + observed-zero-traffic gate before removal (`/rollout`). |

## Phase 4 — Worked examples (the real spec)

For each endpoint: one happy request/response pair **plus the errors** — validation
failure, authz denial, not-found, conflict/idempotent-replay — with exact bodies. Examples
are the executable part of a contract doc: they pin what prose leaves open, and the error
examples force the error model to actually get designed (the unhappy-path floor,
`core.md`, applied to contracts). If the project uses OpenAPI/schema files, draft the
stub; else the contract doc carries the examples.

## Phase 5 — Consumer's-eyes review

Before finalizing, switch sides (lens activation, `core.md`): **write the
client code for the hard consumer case from Phase 1** — the actual calls, the pagination
loop, the retry-on-409, the error handling — against your draft. Every place the client
code gets awkward (three calls where one is needed, ambiguous error branching, undocumented
ordering) is a contract bug found at paper price. Check consistency against the existing
surface one last time — a second dialect in one API is a permanent tax on every consumer.

Deliver: contract doc (+ schema stub) to the Plans location
(`<slug>-api-contract.md`), route to `/threat-model` if the surface is new/external
(entry points are already enumerated — cheap now), then `/prepare` (the contract becomes
plan steps; interface-first, so parallel sessions build against it).

## Hard rules

- **Consistency beats best practice** — deviations from the house dialect are declared
  decisions, not silent improvements.
- **Every list paginates; every non-GET has a retry story; every endpoint has error
  examples.** No exceptions without an "accepted — why" line.
- **Expose default-closed** — each field earns its place; you can add later, you can
  never remove (from a public version).
- **Breaking changes don't ship in place** — they route through `/rollout` coexistence.
- Read-only on app code — the deliverables are the contract doc and schema stub.

## See also

- `/codebase-design` — internal seams (this skill is its public-boundary sibling);
- `/threat-model` — the same surface, attacker's eyes; `/rollout` — shipping contract
  changes; `/analyst` — the WHAT/WHY feeding this; `rules/_generic/resilience.md`,
  `code.md` — the always-on floor the contract must satisfy.
