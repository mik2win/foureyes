---
name: create-migration
description: >-
  Generate a Rails migration with zero-downtime patterns, correct PostgreSQL types, proper
  indexes, and foreign-key constraints.
  TRIGGER when the user wants to add/change a column, table, index, or constraint, or asks
  for a database migration. Writes the file and explains the deploy sequence — it does NOT
  run the migration.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Edit
---

# Create Migration Skill

You are a senior Ruby/Rails developer specializing in PostgreSQL. Generate migrations following project conventions defined in the `rails-database` rule.

## 1. Parse Arguments

Parse `$ARGUMENTS` to determine:

- **Migration name** (required): e.g., `AddStatusToOrders`, `CreatePayments`, `RemoveOldColumns`
- **Description** (optional): additional context about what the migration should do

If only a plain description is given (e.g., "add a status column to orders"), derive a proper migration name from it (`AddStatusToOrders`).

## 2. Read Existing Schema

Read `db/schema.rb` (or `db/structure.sql` if present) to understand:

- Existing tables and columns relevant to this migration
- Current index patterns used in the project
- Whether UUIDs are used as primary keys
- Whether `citext` or other PostgreSQL extensions are enabled
- The Rails migration version used (e.g., `[8.0]`)

Also check recent migrations in `db/migrate/` to match the project's migration style and version number.

## 3. Determine Zero-Downtime Pattern

Evaluate whether the migration requires a zero-downtime approach:

### Column Rename -- 3-step process (separate migrations)

Generate THREE separate migration files:

```ruby
# Step 1: Add new column
class AddFullNameToUsers < ActiveRecord::Migration[8.0]
  def change
    add_column :users, :full_name, :string
  end
end

# Step 2: Backfill data (separate deploy)
class BackfillFullName < ActiveRecord::Migration[8.0]
  def up
    User.in_batches.update_all('full_name = name')
  end

  def down; end
end

# Step 3: Remove old column (after step 2 is live)
class RemoveNameFromUsers < ActiveRecord::Migration[8.0]
  def change
    remove_column :users, :name, :string
  end
end
```

Warn the developer: "This requires 3 separate deploys. Deploy step 1 first, then step 2 after it is live, then step 3."

### Column Type Change

Generate separate migrations: add new column, backfill, swap reads, remove old.

### Adding NOT NULL to Existing Column -- 2-step process

```ruby
# Step 1: Add unvalidated check constraint
class AddNotNullConstraintToOrdersStatus < ActiveRecord::Migration[8.0]
  def change
    add_check_constraint :orders, 'status IS NOT NULL',
                         name: 'orders_status_not_null', validate: false
  end
end

# Step 2: Validate constraint and add formal NOT NULL
class ValidateNotNullOnOrdersStatus < ActiveRecord::Migration[8.0]
  def change
    validate_check_constraint :orders, name: 'orders_status_not_null'
    change_column_null :orders, :status, false
    remove_check_constraint :orders, name: 'orders_status_not_null'
  end
end
```

### Index on Large Table

```ruby
class AddIndexToOrdersEmail < ActiveRecord::Migration[8.0]
  disable_ddl_transaction!

  def change
    add_index :orders, :email, algorithm: :concurrently
  end
end
```

Always use `algorithm: :concurrently` + `disable_ddl_transaction!` for indexes on existing tables. The only exception is indexes inside `create_table` blocks (those are safe).

### Removing a Column

Warn the developer to add `self.ignored_columns += ['column_name']` to the model first, deploy, THEN run the removal migration.

## 4. Apply PostgreSQL Type Conventions

| Data | Use | Avoid |
|------|-----|-------|
| Short text | `:string` | -- |
| Long text | `:text` | `:string` with high limit |
| Money | `:decimal, precision: 12, scale: 2` | `:float` |
| Date + time | `:datetime` (maps to `timestamptz` in PG) | raw `timestamp` without tz |
| Boolean | `:boolean, null: false, default: false` | nullable booleans |
| JSON | `:jsonb, default: {}, null: false` | `:json` (not indexable) |
| Email | `:citext` (with `enable_extension 'citext'`) | `:string` (case-sensitive) |
| UUID PKs | `id: :uuid` (with `enable_extension 'pgcrypto'`) | -- |
| Enum | `:integer, default: 0, null: false` | PostgreSQL `CREATE TYPE` enum |
| Counter | `:integer, default: 0, null: false` | nullable counter |

### Column Naming Conventions

- Timestamps: `_at` suffix (`published_at`, `shipped_at`, `confirmed_at`)
- Booleans: no `is_` prefix (`active`, `visible`, `admin` -- generates `active?` predicate)
- Counters: `_count` suffix (`comments_count`, `orders_count`)

## 5. Add Appropriate Indexes

Apply these rules:

- **Foreign keys**: always indexed (Rails does NOT auto-index them)
- **Columns in WHERE clauses**: indexed
- **Columns in ORDER BY**: indexed
- **Unique constraints**: unique index
- **Partial indexes**: use `where:` for columns with many NULLs or common filter conditions
- **Composite indexes**: put the most selective column first; leftmost prefix rule applies
- **Expression indexes**: for computed queries (`lower(email)`)
- **GIN indexes**: for `jsonb` and array columns

```ruby
# Foreign key -- always indexed
add_reference :orders, :user, null: false, foreign_key: true

# Partial index
add_index :orders, :shipped_at, where: 'shipped_at IS NOT NULL', name: 'idx_orders_shipped'

# Composite -- column order matters
add_index :orders, [:user_id, :created_at]

# Unique
add_index :users, :email, unique: true

# GIN for jsonb
add_index :products, :metadata, using: :gin
```

## 6. Add Foreign Key Constraints

- Use `add_reference` with `foreign_key: true` for new FK columns (adds column + index + FK in one call)
- Specify `on_delete` behavior explicitly:

| on_delete | Use When |
|-----------|----------|
| `:cascade` | Child records should be deleted with parent (comments on a post) |
| `:nullify` | Optional relationship (user deletes account, keep orders) |
| `:restrict` | Prevent parent deletion (financial records) |

```ruby
add_reference :orders, :user, null: false, foreign_key: true
add_foreign_key :comments, :posts, on_delete: :cascade
add_foreign_key :payments, :orders, on_delete: :restrict
```

## 7. Generate the Migration File

### File naming

Use the format: `db/migrate/YYYYMMDDHHMMSS_migration_name.rb`

Generate a timestamp based on the current time. Use `Time.now.utc.strftime('%Y%m%d%H%M%S')` format.

### Structure

Use `change` method when possible (auto-reversible). Use `up`/`down` only for raw SQL or non-reversible operations. Use `reversible` block for hybrid cases.

```ruby
# frozen_string_literal: true

class AddStatusToOrders < ActiveRecord::Migration[8.0]
  def change
    add_column :orders, :status, :integer, default: 0, null: false
    add_index :orders, :status
    add_check_constraint :orders, 'status BETWEEN 0 AND 4', name: 'orders_valid_status'
  end
end
```

### One Logical Change Per Migration

Do not mix unrelated table changes. If the request involves multiple unrelated changes, generate separate migration files.

## 8. Post-Generation Rules

- **Never auto-run** the migration. Show the file and tell the developer to run `rails db:migrate` manually.
- If zero-downtime steps are needed, explain the deployment sequence clearly.
- If the migration adds a column that needs backfilling, recommend a separate rake task or `maintenance_tasks` task -- do NOT put data backfill logic in a schema migration.
- Add `add_check_constraint` for enum integer columns.
- If adding a boolean column, always include `null: false` and `default:`.
- Do NOT create test files unless explicitly asked.
