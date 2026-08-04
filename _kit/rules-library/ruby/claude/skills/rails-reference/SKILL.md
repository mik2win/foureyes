---
name: rails-reference
description: >-
  Worked code examples for this project's Rails layer conventions — models, ActiveRecord
  queries, database/migrations, controllers & routing, business logic (services/forms/
  policies), background jobs, caching & storage, and security.
  CONSULT when implementing or reviewing a Rails layer and you need the idiomatic example
  (model structure, N+1 fixes, service patterns, thin controllers, idempotent jobs, caching,
  strong params/SQL safety). Reference loaded on demand — the always-apply rules live in the
  matching `rails-*` rules.
allowed-tools:
  - Read
  - Grep
  - Glob
---

# Rails layer conventions — worked examples

Companion to the `rails-*` layer rules. Read the reference file (in this skill's folder) for
the layer you're working in:

- **Models** — structure order, enums, associations, scopes, callbacks → `references/models.md`
- **ActiveRecord queries** — N+1, eager loading, batching, indexes-in-queries → `references/queries.md`
- **Database & migrations** — zero-downtime, types, indexes, constraints → `references/database.md`
- **Controllers & routing** — thin controllers, REST, status codes, routes → `references/controllers-routing.md`
- **Business logic** — services, forms, policies, queries, value objects → `references/business-logic.md`
- **Background jobs** — idempotency, retries, primitive args, Solid Queue → `references/background-jobs.md`
- **Caching & storage** — fragment/Russian-doll caching, Solid Cache, storage → `references/caching-storage.md`
- **Security** — strong params, SQL safety, html_safe, auth, secrets → `references/security.md`
