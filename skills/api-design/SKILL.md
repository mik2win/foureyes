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

- **Who calls this** — own frontend / other internal services / third parties / public /
  **an LLM agent** (an MCP server, a tool API, a CLI a model drives)? Each step outward
  hardens the door (`core.md`).
- **Can you break them?** Sets the promise **per edge, not per endpoint**: internal-only where
  both sides ship together, versioned-public (additive-only within a version; breaking = new
  version via `/rollout` coexistence) where the counterpart releases on a clock you don't
  control — an app-store review queue is reason enough. Write each edge's promise into the
  contract doc, with the condition that would tighten a loose edge again; the dialect stays one.
- **The hard consumer case** — the ugliest real call pattern (bulk import, polling at
  scale, retry storms, mobile on flaky network). Designs are judged against it in Phase 5.
- **What counts as breaking** — safe iff the change requires a subset of what it required,
  accepts a superset, returns a superset, and enforces a subset of the old constraints. Adding
  validation to a field you never validated is breaking: the implementation is the spec.

**When an agent is on that list**, the hard consumer case becomes a caller whose only memory is
its context window, and Phase 5 is run against it. The unit of the contract is a completed step
of work, not a resource row (`schedule_event`, not list_users + list_events + create_event);
wrapping each existing endpoint one-to-one is the default failure, and the endpoints you
deliberately did *not* expose belong in the doc beside the ones you did. Responses lead with
what the caller can act on, technical ids behind an explicit `response_format=detailed` — a
second response mode, never a guessable id scheme, both modes under one promise and both in
Phase 4. Name the surface so its boundary reads from outside (`acme_invoices_search`): your
names will sit in a list beside other people's.

## Phase 2 — Resource model, in the domain language

Name the nouns from `CONTEXT.md`/domain vocabulary — the API is the domain made visible,
not the database made public:

- Resources, their identifiers (opaque IDs; never enumerable integers on anything
  tenant-scoped), relationships and nesting depth (flat + link beats deep nesting — nest only
  when the child cannot be listed, linked to, or acted on without its parent; "unknown" = no).
  An identifier you only pass through belongs to someone else: keep the type as received, never
  re-type or format-validate it, and name its one authority in the contract doc.
- Which internal fields are **not** exposed (default-closed: expose what the consumer needs, not
  what the model has — every exposed field is forever, per Hyrum). The decomposition freezes
  too: label each resource "client use case" or "internal structure", and mark the mirrored ones
  "shape frozen, accepted" — a 1:1 mirror makes your next model refactor their breaking change.
- Actions that aren't CRUD: model state transitions explicitly (`/orders/{id}/cancel`
  or a status-transition body — pick the house's existing dialect) instead of overloading
  generic updates with side effects.

## Phase 3 — The contract checklist

One decision per row; "same as existing API" is the default answer, deviations are
declared with a reason. Whatever a row decides is enforced on the server: a client-side copy of
a rule (a validation, a limit) is a hint that drifts, never the enforcement point.

| Concern | Decide |
|---|---|
| **Error model** | One envelope for all errors: machine-readable `code`, human `message`, per-field details for validation. Status codes used honestly (4xx consumer / 5xx producer). No existence oracles on protected resources (404 over 403 where hiding matters — per `/threat-model`). An error body is an instruction, not a status: name the specific fix and show one correctly formed input, or a caller that cannot improvise re-issues the same wrong call. |
| **Pagination & size** | Cursor-based for anything unbounded (offset breaks under concurrent writes); page size capped; the cap documented. Every list endpoint paginates from day one — retrofitting pagination is a breaking change. Anything else that can grow — a document body, an export, a log blob — carries its own bound (range selection, filtering, truncation) with a default and a documented ceiling, and a truncated response says how to narrow the next call. |
| **Filtering/sorting** | Explicit whitelisted params, never pass-through to the query layer. |
| **Idempotency** | Every non-GET states its retry story. Money/creation ops take an idempotency key; consumers on flaky networks WILL retry (`resilience.md`). |
| **Read-after-write** | If a read path is served by anything other than the write store — replica, cache, search index, projection — the staleness window is client-visible and part of the contract, not an infra detail. Per read endpoint: either the write response carries enough to render the new state without re-reading, or both sides expose a version/sequence the client can compare and poll on. Silence here reads as "consistent". |
| **Partial updates** | Pick the house convention (PATCH semantics / explicit fields); define null-vs-absent once, project-wide. |
| **Formats** | Timestamps (UTC ISO-8601), money (integer minor units or decimal-as-string — never floats, always paired with an explicit ISO 4217 currency), enums as strings with an "unknown value" evolution rule for consumers. |
| **Auth & authz** | House mechanism; per-object checks stated per endpoint (role × action from the spec's matrix). |
| **Limits** | Rate limits, payload caps, list caps — numbers, not vibes; the DoS row of `/threat-model` lands here. A documented limit needs a documented refusal: the status, the ceiling, what is left in the window, and how many seconds to wait (`Retry-After`; the rest follow the house convention). Per non-GET, say whether a refused request is dropped or parked — a read is dropped, an order the user meant to place is queued and the docs say so. Multiply payload size by request rate before shipping a fat contract. |
| **Evolution** | Additive-only within version; deprecation = header/doc + sunset date + observed-zero-traffic gate before removal (`/rollout`). |

## Phase 4 — Worked examples (the real spec)

For each endpoint: one happy request/response pair **plus the errors** — validation failure,
authz denial, not-found, conflict/idempotent-replay, limit refusal — with exact bodies.
Examples are the executable part of a contract doc: they pin what prose leaves open, and error
examples force the error model to actually get designed (the unhappy-path floor,
`core.md`, applied to contracts). If the project uses OpenAPI/schema files, draft the
stub; else the contract doc carries the examples.

## Phase 5 — Consumer's-eyes review

Before finalizing, switch sides (lens activation, `core.md`): **write the
client code for the hard consumer case from Phase 1** — the actual calls, the pagination
loop, the retry-on-409, the error handling — against your draft. Every place the client
code gets awkward (three calls where one is needed, ambiguous error branching, undocumented
ordering) is a contract bug found at paper price. Then write the careless client — the one that
ignores the return value: if misreading an entry point fails open, change the shape until it
fails closed; when both a quiet and a loud form are needed, ship two differently named
operations rather than one with a flag. Check consistency against the existing surface one last
time — a second dialect in one API is a permanent tax on every consumer.

When the awkwardness is that one call is too general, layer it: one entry point makes the
dominant case a single obvious call, an explicit path serves the rare one over the same
implementation — not seven optional parameters, and not a thin wrapper to delete. Per parameter,
keep it when dropping would drag a dependency into the body; never trade one for global state.

Deliver: contract doc (+ schema stub) to the Plans location
(`<slug>-api-contract.md`), route to `/threat-model` if the surface is new/external
(entry points are already enumerated — cheap now), then `/prepare` (the contract becomes
plan steps; interface-first, so parallel sessions build against it).

## Hard rules

- **Consistency beats best practice** — deviations from the house dialect are declared
  decisions, not silent improvements. A departure costs the reader a learning curve: say what
  the convention already buys, then justify the departure as self-explanatory or worth the curve.
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
