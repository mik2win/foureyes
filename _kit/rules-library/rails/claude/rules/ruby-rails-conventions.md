---
paths:
  - "**/*.rb"
---

# Ruby and Rails Conventions

Always-apply conventions for this codebase — object design, naming, and the Rails idioms the team follows.

> Worked GOOD/BAD examples and the optional patterns (value/query/form objects, custom
> validators, focused concerns) live in the **`rails-conventions-reference` skill** — invoke
> it when you need an idiomatic example or are introducing one of those patterns.

---

# Part A: Ruby

## Naming

- `snake_case` for files, methods, variables; `CamelCase` for classes/modules;
  `SCREAMING_SNAKE_CASE` for constants.
- Rails naming: `User` model → `users_controller.rb` → `UsersController`.
- Predicate methods end with `?` (`active?`, `valid?`); dangerous/bang methods end with `!`
  (`save!`, `destroy!`).
- Descriptive names: `user_signed_in?`, `calculate_total` — never `calc`.

## Ruby usage

- Single quotes unless interpolation is needed.
- Safe navigation `user&.name`; Ruby 3.x features (pattern matching, endless methods) where
  they read well.
- `Time.current` / `Date.current` (timezone-aware) — never `Time.now` / `Date.today`.
- Freeze constants: `STATUSES = %w[active inactive].freeze`.

## OOP principles (actively followed)

- **SRP** — one reason to change; split a class that does two unrelated things.
- **Dependency Injection** — pass collaborators in; don't instantiate them inside.
- **Tell, Don't Ask** — tell objects to act; don't interrogate state to decide for them.
- **Law of Demeter** — limit chaining; talk to immediate neighbors (chaining on the same
  type, e.g. `select.map`, is fine).
- **Duck typing** — depend on what objects do, not what they are; avoid `is_a?` dispatch.
- **Dependency direction** — depend on things that change less often; abstractions over
  concretions.
- **Shameless green** — simplest passing solution first; don't extract until the abstraction
  is clear (rule of three). Wrong abstraction costs more than duplication.
- **Open/Closed** — extend without modifying existing code (e.g. strategy injection).
- **Name by what a thing IS** — `ReportGenerator` (noun), not `GenerateReport`.
- **Composition over inheritance** — concerns/modules for shared behavior; avoid deep
  hierarchies; STI only for truly identical types.
- **YAGNI > premature abstraction**; **DRY applies to knowledge** (one business decision in
  one place); apply SOLID pragmatically for a small team.

---

# Part B: Rails architecture

## Layer responsibilities

| Layer | Responsibility |
|---|---|
| **Model** | Data logic: validations, associations, scopes, query methods, calculations that belong to the entity |
| **Service** (`app/services/`) | Business logic: multi-step operations, orchestrating models, use cases |
| **Controller** | Thin: request → coordinate calls to models/services → render/redirect. No business logic. |
| **Helper** | View formatting only. No HTML, no DB queries. |
| **View** | Display only — no data processing, no business logic. |
| **Job** | Async work; delegates logic to a service. |

- **Models are not god objects** — extract unrelated responsibilities into a **concern**
  (cohesive trait) or a **service** (orchestration).
- **Controllers have no business logic** — only authenticate/authorize, parse params,
  coordinate calls, respond. Multiple calls are fine; business *decisions* are not.

## Models

- Structure order: (1) extend/include (2) constants (3) attribute overrides (4) enums
  (5) associations (6) delegations (7) validations (8) scopes (9) callbacks (10) class
  methods (11) instance methods.
- **Enums** — positional syntax with explicit integer values (`enum :status, { draft: 0, active: 1 }`)
  — the keyword form `enum status: {...}` was removed in Rails 8; never implicit array ordering.
- **Callbacks sparingly** — prefer explicit service calls over hidden side-effects; OK for
  defaults and same-model data consistency.

## ActiveRecord

- Eager-load associations used in views (`includes` / `preload` / `eager_load`) — no N+1.
- `exists?` for presence (not `present?`); `pluck` for single-column arrays; `find_each` for
  large datasets; `transaction` for atomic multi-write; `load_async` for independent parallel
  queries.
- Enforce simple validations in the DB (null, unique indexes); keep reusable queries in scopes.

## Services

- Live in `app/services/`, named as **nouns** (`OrderFulfiller`, `PricingCalculator`) — not
  verbs.
- Two shapes: a single `#call` for one focused operation, or multiple public methods as a
  facade. Namespace with modules (`Orders::FulfillmentService`).
- **Dependency rule** — domain logic must not depend on framework specifics; keep it testable
  and reusable without Rails.

## Controllers and routing

- Skinny controllers: params, auth, call models/services, respond with the right status
  (`:unprocessable_entity` on validation failure).
- RESTful resources, **max 1 level of nesting**, `shallow: true` for clean URLs, named routes
  for readability.

## Security

- **Strong params always** — `params.expect(model: [:attr, ...])` on Rails 8+ (400s on tampering instead of 500); `params.require(...).permit(...)` on ≤7.x. Never `permit!`.
- CSRF protection on (Rails default) — do not disable.
- No `html_safe` / `raw` without a justifying comment.
- Parameterized queries — never interpolate user input into SQL.
- No sensitive data in logs.

## Background jobs

- **Idempotent** — safe to retry. Keep jobs small and single-purpose.
- Delegate business logic to a service; never inline it in the job.
- `find_by` (not `find`) to guard against stale references; pass only primitives (ids,
  strings) as arguments — never ActiveRecord objects.

## Migrations

- Reversible; add indexes for columns used in WHERE / JOIN / ORDER; `add_reference ...,
  foreign_key: true`.
- Never auto-run migrations — show the file and let the developer run it.

## Error handling and performance

- Exceptions for exceptional cases, not control flow; custom hierarchies for domain errors;
  handle in controllers with flash messages; log properly.
- Index hot columns; eager-load to avoid N+1; `find_each` for large sets; fragment caching for
  expensive views; `counter_cache` for frequently counted associations.

## Optional patterns

Value objects, query objects, form objects, custom validators, and focused concerns — use
only when the simpler approach (scope, model method, inline validation) no longer fits; do not
introduce them preemptively. Worked examples are in the `rails-conventions-reference` skill.
