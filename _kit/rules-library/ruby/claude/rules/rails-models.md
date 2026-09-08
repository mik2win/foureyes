---
paths:
  - "app/models/**/*.rb"
---

# Rails Model Layer

Based on Rails Guides (Active Record).

For OOP principles (SRP, composition, duck typing), see `ruby-oop.md`.

> Worked examples live in the `rails-reference` skill (`references/models.md`).

---

## 1. Model File Structure

Canonical ordering inside every model — declarations (what the model IS) before methods (what it DOES):

1. extend / include
2. Constants
3. Attribute overrides (`store`, `serialize`, `attribute`)
4. Enums (always explicit integers)
5. Associations
6. Delegations
7. Validations
8. Scopes
9. Callbacks (sparingly)
10. Class methods
11. Instance methods

---

## 2. Associations

- **`inverse_of`** — Rails auto-detects simple pairs; you MUST specify it for `through`, `foreign_key`, and polymorphic associations. Without it Rails keeps stale in-memory copies, so parent validation on child save sees the wrong data.
- **`dependent:` is mandatory** on every `has_many` / `has_one` — omitting it leaves orphan records.

| Option | Behavior | Use when |
|--------|----------|----------|
| `:destroy` | Calls `destroy` on each child (runs callbacks) | Children have own callbacks/dependents |
| `:delete_all` | SQL DELETE, no callbacks | Performance-critical, simple children |
| `:nullify` | Sets FK to NULL | Children can exist independently |
| `:restrict_with_error` | Prevents delete, adds error | Soft protection with user-friendly message |
| `:restrict_with_exception` | Prevents delete, raises | Hard protection in jobs/APIs |

- **`counter_cache: true`** to avoid `COUNT(*)`; **`touch: true`** to bump parent `updated_at` for cache invalidation.
- **Polymorphic:** no DB-level FK; always add a composite index on `[type, id]`; the `_type` column stores the class name, so renames need a data migration.
- **STI** only when subtypes share the same columns (differ by 1-2 nullable at most). If subtypes need different columns (a table full of NULLs), use separate tables or polymorphic instead.

---

## 3. Validations

- Use **BOTH** a DB constraint and a model validation: the DB is the safety net (catches races), the model gives a friendly early error.

| DB constraint | Model validation |
|---------------|------------------|
| `NOT NULL` | `validates :name, presence: true` |
| `UNIQUE index` | `validates :email, uniqueness: true` |
| `CHECK (amount >= 0)` | `validates :amount, numericality: { >= 0 }` |
| Foreign key | `belongs_to :user` (validates by default) |

- **Uniqueness race:** model validation alone is NOT enough — always pair with a unique DB index and handle `ActiveRecord::RecordNotUnique`.
- **Conditional validations** — use a method reference (`if: :requires_billing?`), not an inline proc for complex logic.
- **`validates_associated`** on ONE side only (the parent); both sides cause an infinite loop.
- **Uniqueness with `scope:`** — always pair with a matching composite unique index.
- **Custom validators** — subclass `ActiveModel::EachValidator`, return early on `blank?`, add to `record.errors`.

---

## 4. Enums

- Rails 7+ syntax with **explicit integers**: `enum :status, { draft: 0, published: 1, archived: 2 }`. Never the old `enum status:` hash form or the position-dependent array form.
- Explicit integers mean inserting a new value never shifts existing mappings or corrupts data.
- Use `prefix:` / `suffix:` when value names collide across enums (`status_active?` vs `subscription_active?`).
- Generates a scope (`Article.published`), a predicate (`article.published?`), and a bang updater (`article.published!`).

---

## 5. normalizes (Rails 7.1+)

- Prefer `normalizes :email, with: ->(e) { e.strip.downcase }` over a `before_validation` callback.
- **Why:** `normalizes` applies on assignment, in finders (`find_by`), and in uniqueness checks. Callbacks run only on save, leaving gaps in queries and comparisons.

---

## 6. strict_loading

- Available per-association, per-query (`User.strict_loading.includes(:posts)`), per-record (`user.strict_loading!`), or globally via `config.active_record.strict_loading_by_default`.
- Raises `ActiveRecord::StrictLoadingViolationError` on lazy loading — catches N+1 before production. Fix with `includes` / `preload` / `eager_load`.

---

## 7. Callbacks

| Acceptable callbacks | Avoid callbacks for |
|---|---|
| Setting defaults (`before_validation`) | Sending emails / notifications |
| Generating slugs, tokens on create | Touching external services / APIs |
| Maintaining derived data within same model | Creating / modifying other models |
| Normalizing data (prefer `normalizes`) | Complex business logic orchestration |
| `after_commit` for cache invalidation | Enqueuing jobs (use `after_commit` only) |

- **`after_commit`, not `after_save`, for jobs/external effects.** `after_save` fires inside the transaction, so a job on another connection may not see the uncommitted record; `after_commit` fires only after a successful commit.
- More than 2-3 callbacks means the model is doing too much — extract to a service (see `ruby-oop.md`, section 13).

---

## 8. Scopes

- Use chainable, descriptive `scope`s; chain freely (`Article.active.recent.by_author(user)`).
- A class method returning an Array (`all.select(&:active?)`) breaks chaining and loads every record into memory — keep scopes relation-returning.
- Use a class method instead of a scope only for conditional logic / early returns (e.g. `return all if query.blank?`).
- **Never `default_scope`** — it leaks into new-record defaults, joins, `count`/`exists?`, and is hard to override (`unscoped` removes ALL scopes). Use an explicit named scope.

---

## 9. Concerns

- One concern = one cohesive behavior; name after the trait (`Archivable`, `Sluggable`, `Trackable`, `Publishable`).
- Keep under ~50 lines; if it grows past that, extract to a service or separate model.
- Avoid concerns that depend on other concerns (implicit coupling).
- Concerns are not a substitute for domain modeling — see `ruby-oop.md` (SRP, composition).

---

## 10. Query Patterns

- Eager-load to kill N+1 (`Post.includes(:author)`):

| Method | Strategy | Use when |
|--------|----------|----------|
| `includes` | Rails chooses | Default choice |
| `preload` | Separate queries | Many associations, avoid huge JOIN |
| `eager_load` | LEFT OUTER JOIN | Need to filter/order by association columns |

- `pluck` for raw values (skips AR instantiation); `select(:id, :name)` to limit loaded columns — don't `map(&:email)` over full objects for one field.
- `find_each(batch_size:)` for batch processing at constant memory — never `.each` over a full table.
- Compose cross-model scopes with `merge` (`Post.joins(:comments).merge(Comment.approved)`).

---

## 11. Data Integrity Patterns

- Wrap multi-write operations in `ActiveRecord::Base.transaction` (all succeed or all roll back); use `record.with_lock` for pessimistic locking on critical records.
- **Migration safety:** add NOT NULL with a default or backfill first; add indexes concurrently on large tables (`algorithm: :concurrently`); never rename columns in one step; always add FK constraints for `belongs_to`.

---

## 12. Encrypted Attributes (Rails 7+)

- `encrypts :email, deterministic: true` — same plaintext = same ciphertext; enables `find_by`/`where` but reveals value equality.
- `encrypts :ssn` (non-deterministic) — more secure but cannot be queried.

---

## 13. Common Anti-Patterns

- **Fat model** — a model orchestrating multi-step workflows (`validate_inventory! && charge_payment! && send_email!`). Keep the model to its own data (`place!`); push orchestration to a service.
- **Business logic in controllers** — computing status/discounts in `create`. The controller coordinates; logic lives in model/service.
- **Query logic in controllers** — raw `where(...)` chains in actions belong in scopes (`Order.active.recent.includes(:customer)`).
- More than 3 callbacks signals accumulating responsibilities — extract to service objects (see `ruby-oop.md`).
- **Schema-shaped model** — the model needs relationships, collections or subtypes the tables do not carry, or the schema belongs to another system and is not yours to change. A thin model with no callbacks can sit past this line: size is the other axis, not this one.
- The move: extract the diverging part into a PORO or a value object, read a foreign schema through a query object or a gateway, and stop closing the gap by adding one more attribute to the model.

---

## 14. Testing Models

When tests are requested, focus on:

| Test | Skip |
|------|------|
| Custom validations and edge cases | Default Rails validations (presence, numericality) |
| Scope correctness (returns right records) | Association declarations |
| Callback side effects (if any) | Enum method generation |
| Instance/class methods with logic | Simple delegations, `normalizes` |

Test custom logic, not Rails internals. For full testing conventions, see `rspec-testing.md`.
