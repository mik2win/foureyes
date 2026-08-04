---
paths:
  - "db/migrate/**/*.rb"
  - "db/schema.rb"
  - "db/structure.sql"
---

# Rails Database & Migrations

Based on Rails Guides (Active Record Migrations), PostgreSQL documentation, Strong Migrations patterns, Zero-Downtime Deployments.

> Worked examples live in the `rails-reference` skill (`references/database.md`).

---

## 1. Migration Fundamentals

- Use `change` (auto-reversible) when possible; Rails reverses `add_column`, `create_table`, `add_index`, `add_reference`, etc., so you never forget the `down`.
- Use `reversible` block or explicit `up`/`down` only for raw SQL or non-reversible operations.
- Never auto-run migrations — show the file, let the developer run `rails db:migrate`.
- **Naming:** `AddStatusToOrders`, `CreatePayments`, `RemoveOldColumns`, `AddIndexToUsersEmail`.

---

## 2. Zero-Downtime Migrations

- **Renaming a column — 3 steps:** add new column (write to both) → backfill + switch reads → remove old. One-step renames lock the table and break running instances referencing the old name.
- **Adding indexes (PostgreSQL):** use `algorithm: :concurrently` + `disable_ddl_transaction!` — `CONCURRENTLY` can't run in a transaction, and a plain `add_index` locks the table for writes on large tables. SQLite has no concurrent indexing, but its tables are typically small.
- **Adding a column with default:** safe in PostgreSQL 11+ (no rewrite). On older PG, or when adding NOT NULL to an existing column, go nullable → backfill in batches → add the constraint/default.
- **Removing a column:** add `self.ignored_columns += [...]` and deploy first, then drop in a later migration. AR caches column info at boot; a running instance referencing a removed column crashes.
- **Adding NOT NULL to an existing column (PostgreSQL):** add an unvalidated check constraint, then `validate_check_constraint` + `change_column_null` + drop the constraint. A bare `change_column_null` locks the table while scanning every row.

---

## 3. Data Migrations

- Separate data migrations from schema migrations — schema changes structure, data changes content.
- Run backfills via a rake task or the `maintenance_tasks` gem (recommended for Rails 8), never inside a schema migration.
- **Why separate:** the model class at migration time is the *current* class, not the one when the migration was written — columns, validations, and callbacks may differ.
- **Batching large updates:** `in_batches` + `update_all` (no callbacks, fastest); `find_each` when you need model callbacks. Never iterate the whole table with `.each` (memory) or run a single `update_all` over millions of rows (table lock).

---

## 4. Indexes

Indexes speed up reads but slow down writes — add them deliberately. Composite index column **order matters**: only the leftmost prefix is used. Use unique, partial (`where:`), expression (`lower(email)`), and GIN (JSONB/array) indexes where appropriate.

| Always Index | Consider Indexing | Skip Indexing |
|---|---|---|
| Foreign keys (`_id` columns) | Columns in frequent WHERE | Boolean columns (low cardinality) |
| Columns in UNIQUE constraints | Columns in ORDER BY | Tiny tables (<1000 rows) |
| Columns used in JOIN ON | Columns in GROUP BY | Columns rarely queried |
| Polymorphic type + id pairs | Columns used with LIKE prefix | Write-heavy columns with no reads |

**Why index foreign keys:** Rails does not auto-index FKs. Without an index, every `DELETE` on the parent triggers a sequential scan on the child table.

---

## 5. Foreign Keys

- Prefer `add_reference ..., foreign_key: true` — adds column + index + FK in one call.
- Always specify `on_delete` explicitly; a column without a foreign key allows orphaned records.

| on_delete | Behavior | Use When |
|-----------|----------|----------|
| `:cascade` | Delete child records | Comments on a post, line items on an order |
| `:nullify` | Set FK to NULL | Optional relationship (user deletes account, keep orders) |
| `:restrict` | Prevent parent deletion | Financial records (never orphan payments) |
| (none) | Same as `:restrict` in PostgreSQL | Default — be explicit instead |

**Note:** Polymorphic associations (`commentable_type` + `commentable_id`) cannot have DB-level foreign keys. Prefer separate tables or STI when referential integrity matters.

---

## 6. Database Constraints

Model validations give user-friendly errors; DB constraints are the safety net. Use `null: false`, unique indexes, and `add_check_constraint` (Rails 6.1+). On large tables add the check unvalidated, then `validate_check_constraint` separately.

| Rule | DB Constraint | Model Validation | Both? |
|------|--------------|-----------------|-------|
| NOT NULL | `null: false` | `validates :f, presence: true` | Yes |
| Unique | unique index | `validates :f, uniqueness: true` | Yes |
| Range check | CHECK constraint | `validates :f, numericality: {}` | Yes |
| Foreign key | `foreign_key: true` | `belongs_to` (validates by default) | Yes |
| Format (email) | -- | `validates :f, format: {}` | Model only |
| Business rule | -- | Custom validation | Model only |

**Why both:** DB constraints catch bugs in rake tasks, raw SQL, console, and race conditions. Model validations give actionable error messages.

---

## 7. Column Conventions

- Timestamps: `_at` suffix (`published_at`, `shipped_at`).
- Booleans: no `is_` prefix (`active`, not `is_active`) — generates the `active?` predicate. Always `null: false, default:`.
- Counters: `_count` suffix (for `counter_cache`).
- Money: `:decimal, precision:, scale:` — **never** `:float`.
- Email: `:citext` (PostgreSQL); `:string` + downcase for SQLite.
- UUID primary keys: `id: :uuid` (enable `pgcrypto`).
- JSON: `:jsonb` with a GIN index (PostgreSQL).
- Enum columns: integer with a CHECK constraint.

### Column Type Quick Reference

| Data | Type | Notes |
|------|------|-------|
| Short text | `:string` | Add length limit if known |
| Long text | `:text` | No limit in PostgreSQL |
| Money | `:decimal, precision: 12, scale: 2` | Never `:float` |
| Date + time | `:datetime` / `:timestamptz` | Prefer `timestamptz` in PG |
| Boolean | `:boolean` | Always `null: false, default:` |
| JSON | `:jsonb` | With GIN index (PG) |
| Email | `:citext` | PG only; use `:string` + downcase for SQLite |
| UUID | `:uuid` | Enable `pgcrypto` extension |

---

## 8. Enums

- Model: Rails 7+ `enum :status, { ... }` with **explicit integer values** (safe against reordering). Migration: integer column `default: 0, null: false`, an index, and a CHECK constraint on the value range.
- Never use array syntax — inserting a value between others shifts every value after it.
- **Why integer over PostgreSQL ENUM type:** simpler to extend; PG `ALTER TYPE ... ADD VALUE` can't run inside a transaction.

---

## 9. Transactions and Locking

Wrap related writes in `ActiveRecord::Base.transaction`.

| Locking | Use When | Mechanism |
|---------|----------|-----------|
| Optimistic | Low contention, conflict is rare | `lock_version` column, raises on conflict |
| Pessimistic | High contention, must guarantee exclusive | `FOR UPDATE` (`Order.lock.find`), blocks others |
| Advisory | Application-level (cron, migrations) | `pg_advisory_lock`, lightweight |

---

## 10. Schema Management

- Always check `schema.rb` / `structure.sql` into version control.
- Use `structure.sql` (`config.active_record.schema_format = :sql`) when you need PostgreSQL-specific features (custom types, materialized views, functions, exclusion constraints); otherwise stick with `schema.rb` for readability.
- **One logical change per migration** — don't mix unrelated table changes in a single file.
- PostgreSQL-specific: enable extensions (`pgcrypto`, `citext`, `pg_trgm`); create materialized views via `scenic` or raw SQL in a `reversible` block.

---

## 11. Strong Migrations (Gem)

The `strong_migrations` gem catches unsafe migrations before they run (adding an index without `CONCURRENTLY`, removing a column without `ignored_columns`, changing a column type, renaming a table/column, etc.). Configure `start_after` and `target_postgresql_version`; wrap a known-safe operation in `safety_assured { ... }`.

---

## 12. Migration Checklist

| Check | Action |
|-------|--------|
| Adding index on large table? | `algorithm: :concurrently` + `disable_ddl_transaction!` |
| Removing a column? | Add `ignored_columns` first, deploy, then drop |
| Renaming column/table? | 3-step: add new, backfill, remove old |
| Adding NOT NULL to existing column? | Unvalidated check constraint, then validate |
| Data backfill needed? | Separate rake task or maintenance_tasks |
| Foreign key added? | Specify `on_delete` explicitly |
| New boolean column? | `null: false, default:` (avoid three-state boolean) |
| New money column? | `decimal`, never `float` |
| Using raw SQL? | Provide both `up` and `down`, or `reversible` block |
