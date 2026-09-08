---
paths:
  - "app/services/**/*.rb"
  - "app/forms/**/*.rb"
  - "app/policies/**/*.rb"
  - "app/presenters/**/*.rb"
  - "app/values/**/*.rb"
  - "app/queries/**/*.rb"
---

# Rails Business Logic Patterns

The business-logic patterns this team follows — domain rules stay independent of Rails internals.

Service object fundamentals (Pattern 1: single `#call`, Pattern 2: multi-method facade) live in `ruby-oop.md` section 13. This file covers Rails-specific patterns and extensions.

> Worked examples live in the `rails-reference` skill (`references/business-logic.md`).

---

## 0. Layer Responsibilities

| Layer | Responsibility | Example |
|---|---|---|
| **Model** | Data logic: validations, associations, scopes, calculations **that belong to the entity**. Not a god object. | `order.total`, `Order.active`, `validates :email` |
| **Concern** | Reusable **single-model** behavior shared by 2+ models. Cohesive trait, <50 lines. | `Archivable`, `Sluggable` |
| **Service** (`app/services/`) | Complex logic: multi-step ops, cross-model orchestration, external API calls | `OrderFulfiller`, `PaymentProcessor` |
| **Controller** | **Thin:** receive request → authenticate → call models/services → respond. Coordinates, no business logic inside. | `OrdersController#create` |
| **Form Object** (`app/forms/`) | Multi-model forms, complex validation spanning models | `RegistrationForm` |
| **Query Object** (`app/queries/`) | Complex reusable queries with 3+ conditions or joins | `ActiveUsersQuery` |
| **Presenter** (`app/presenters/`) | View-specific logic for one model, beyond simple helpers | `OrderPresenter` |
| **Policy** (`app/policies/`) | Authorization rules: who can do what | `OrderPolicy` |
| **Job** | Async work: anything slow or non-critical to the request cycle. Delegates to services. | `OrderProcessingJob` |
| **Helper** | View formatting: one-liner methods. No HTML, no DB queries, no state. | `format_amount` |
| **View** | Display only — no data processing, no business logic | templates, partials |

**Key architecture rules:**
- **Models are not god objects.** When a model grows beyond its own data logic → extract to concern (shared trait) or service (orchestration).
- **Controllers have no business logic.** Only auth, params, coordinating calls, respond. Multiple calls are fine — business *decisions* are not.
- **Jobs have no business logic.** They delegate to services; jobs handle retries and scheduling.
- **Concerns are for reusable traits**, not dumping grounds. 2+ models need `archive!`/`archived?` → concern. One model's method is 50+ lines → service.

---

## 1. When to Extract (Decision Guide)

| Pattern | Extract When | Lives In |
|---------|-------------|----------|
| Model method | Logic belongs to a single entity, uses model's own data | `app/models/` |
| Concern | Shared behavior across 2+ models, cohesive trait | `app/models/concerns/` |
| Scope / Query Object | Reusable query logic, 3+ conditions | `app/models/` or `app/queries/` |
| Service Object | Multi-step operation, orchestrates multiple models | `app/services/` |
| Form Object | Form spans multiple models, complex validation | `app/forms/` |
| Presenter / Decorator | View-specific logic beyond helpers | `app/presenters/` |
| Policy Object | Authorization logic | `app/policies/` |
| Value Object | Concept with equality by value (Money, Address) | `app/values/` |

- Data logic in the model; orchestration (multi-model coordination, side effects, external calls) in a service.
- Never put orchestration in a model (god model) or controller (fat controller).

---

## 2. Service Objects in Rails Context

Structure (single `#call`, multi-method facade) is in `ruby-oop.md` section 13. Rails extensions:

- **Transactions** — wrap multi-model writes in `ActiveRecord::Base.transaction`. Return meaningful results on failure (e.g. rescue `ActiveRecord::RecordInvalid` and return `e.record`, which carries its errors).
- **A check-then-write inside the transaction is a race, not a guard.** `exists?`/`find` then `create!` lets two requests pass the same check and both write — snapshot isolation does not catch it, and `.lock` on the overlap query locks nothing because the conflicting row does not exist yet. Enforce an absence invariant ("no overlapping reservation") with a unique or exclusion constraint and rescue `ActiveRecord::RecordNotUnique`; a presence invariant with `lock` (`FOR UPDATE`) on the rows read; or run the path `isolation: :serializable` with a retry — and say which in the plan.
- **Module organization** — group related services under a domain namespace (`Orders::Creator`, `Orders::Fulfiller`). Avoid flat, verbose `XxxService` names.
- **Dependency injection** — pass collaborators in (`ruby-oop.md` section 2). Common Rails injectables: mailers, job classes, external clients. Lets tests swap in fakes.

---

## 3. Form Objects

- Use when a form spans multiple models, needs cross-model validation, or when `accepts_nested_attributes_for` creates tight coupling.
- Build on `ActiveModel::Model` + `ActiveModel::Attributes`; declare attributes and validations; `#save` runs `valid?`, writes inside a transaction, and on `ActiveRecord::RecordInvalid` does `errors.merge!(e.record.errors)` to surface model errors.
- Controller treats it like a model: `Form.new(params)`, `if @form.save`, `form_with model: @form`. Testable as a PORO.
- **Multi-step wizard** — one form object per step (each its own `ActiveModel::Model` PORO). Controller validates the step, merges its data into the session, then advances.

---

## 4. Result Objects

- Return structured results from services. Don't raise exceptions for expected business failures, and don't return bare booleans that lose error context.
- Define with `Result = Data.define(:success?, :value, :error)` (Ruby 3.2+); rescue expected failures and return a failure `Result` carrying the error message.
- **Anti-patterns:** raising for an expected declined card (exceptions as flow control); returning bare `false` (caller has no idea why it failed).
- **Why:** explicit success/failure; carries error context; pattern-matchable with `case/in`; composable across services.

---

## 5. Presenters / Decorators

- Extract view-specific logic from models and helpers. Use `SimpleDelegator` for transparent wrapping (all model methods remain available).
- Keep display logic (e.g. `avatar_url`, `display_name`) out of the model — it's a view concern leaking in.

### Decision Guide: Helper vs Presenter vs ViewComponent

| Use | When |
|-----|------|
| Helper | One-liner formatting (`format_amount`, `status_class`). No state. |
| Presenter | Multiple related formatting methods for one model. Wraps model instance. |
| ViewComponent | Complex reusable UI with HTML, variants, slots, Stimulus. |

---

## 6. Value Objects

- Immutable, identified by their attributes (not an ID). Use `Data.define` (Ruby 3.2+) for concise, frozen value objects (e.g. `Money`, `Address`).
- **Custom ActiveRecord attribute type** — bridge value objects to columns with a `ActiveRecord::Type::Value` subclass: `cast` (input → VO), `serialize` (VO → DB), `deserialize` (DB → VO). Register with `ActiveRecord::Type.register`, then `attribute :total, :money`.

---

## 7. Policy Objects

- Encapsulate authorization rules; keep controllers and models free of permission checks.
- `ApplicationPolicy` holds `(user, record)` and defaults every action to `false`; subclasses override `show?`/`update?`/`cancel?`/etc., with a private `owner?` helper.
- **Controller integration** — an `Authorization` concern provides `authorize!(record, action = "#{action_name}?")`, constantizes `"#{record.class}Policy"`, raises `NotAuthorizedError` unless permitted, and `rescue_from`s it into a denied response.
- **Why:** authorization in one place per model; testable in isolation; easy to audit; composable with scopes for collection filtering.

---

## 8. Current Attributes

- Thread-safe, request-scoped global state for cross-cutting concerns. Subclass `ActiveSupport::CurrentAttributes`; set from an `ApplicationController` `before_action`; read anywhere (`Current.user`, `Current.request_id`).

### When to Use `Current` vs Passing Explicitly

| Use `Current` for | Pass explicitly for |
|---|---|
| Audit logging (who changed what) | Service object dependencies |
| Time zone setting | Business logic inputs |
| Request-scoped metadata (request ID, IP) | Testable collaborators |
| Locale setting | Anything that affects the return value |

`Current` is for cross-cutting context, not business inputs. An audit concern reading `Current.user&.id` in `before_create`/`before_update` is fine. A service reading `Current.user` internally is a hidden dependency that's hard to test — pass `fulfilled_by:` in instead.

---

## 9. Domain Events with ActiveSupport::Notifications

- Decouple core actions from side effects: the action `ActiveSupport::Notifications.instrument`s an event; independent subscribers (in an initializer) react. Subscribers can be added/removed without touching the publisher.

### When to Use Events vs Direct Calls

| Use Events | Use Direct Calls |
|---|---|
| Side effects (email, analytics, webhooks) | Core business logic that must succeed together |
| Multiple independent subscribers | Sequential steps where order matters |
| Adding subscribers should not require changing the publisher | Tight coupling is intentional (transaction boundary) |

Core logic that must succeed-or-roll-back together (e.g. `Order.create!` + `InventoryManager#reserve!`) belongs in a transaction with direct calls, not events.

---

## 10. Query Objects

- Extract complex queries that span 3+ conditions, involve multiple joins, or appear in multiple places. See `rails-activerecord-queries.md` section 5 for fundamentals.
- Initialize with a default scope (`scope = Order.all`) so the object is composable with other scopes (`OverdueOrdersQuery.new(company.orders).call(...)`).
- Aggregations work the same way — `group`/`select` for stats.

---

## 11. Interactors (Multi-Step Orchestration)

- When a business operation has 3+ steps that must succeed or fail together, each complex enough to be its own service, use a single orchestrator that wraps them in one transaction and rescues each domain error into a failure `Result`.
- **Why a single orchestrator over chained services:** the transaction boundary is explicit, error handling is centralized, and the controller calls one object.

---

## 12. Callbacks vs Services (Decision Guide)

Callbacks fundamentals in `rails-models.md` section 7.

| Use Callback | Use Service |
|---|---|
| Setting defaults before validation | Multi-model orchestration |
| Generating slugs/tokens on create | Sending emails or notifications |
| Normalizing data within same model | External API calls |
| Cache invalidation (`after_commit`) | Complex business logic |
| 1-2 simple callbacks | 3+ callbacks (model is doing too much) |

**Anti-pattern:** stacking side effects in callbacks (`after_commit :send_confirmation`, `:track_analytics`, `:notify_warehouse`...) — hidden, hard to test, hard to skip, and they fire even in tests/seeds/console. Put those in a service instead.

---

## 13. Testing Business Logic Objects

Full RSpec conventions in `rspec-testing.md`.

| Object | Test Focus | Mock Strategy |
|--------|-----------|---------------|
| Service | Side effects (DB changes, job enqueue) + return value | Mock external APIs, verify model state |
| Form Object | Validation rules + `save` creates correct records | Test as PORO, check DB state |
| Result Object | Success/failure branching, error messages | N/A (pure data) |
| Presenter | Formatting output for each state | Wrap real or stubbed model |
| Policy | Each action returns correct boolean per role | Build user + record combinations |
| Query Object | Returns correct records, excludes wrong ones | Use real DB (create test records) |

---

## 14. Summary: Where Does It Go?

- Reads/writes one model's own columns → **Model method**
- Shared by 2+ unrelated models → **Concern** (trait) or **Service** (orchestration)
- Coordinates 2+ models in a transaction → **Service Object**
- Form touches multiple models → **Form Object**
- View/display formatting → **Presenter** (model-specific) or **Helper** (stateless one-liner)
- Decides who can do what → **Policy Object**
- Concept with no ID, equality by value → **Value Object**
- Complex reusable query → **Query Object** (or scope if simple)
- Side effect (email, analytics, webhook) → **Domain Event subscriber** or background job

**Goal:** models stay focused on data and simple business rules; controllers stay thin (route, authorize, delegate); everything else lives in a purpose-built object with a clear name.
