# Rails database & migrations — worked examples

Companion reference to the `rails-database` rule; loaded on demand.

---

## 1. Migration Fundamentals

```ruby
# GOOD — auto-reversible with change
class AddStatusToOrders < ActiveRecord::Migration[8.0]
  def change
    add_column :orders, :status, :string, null: false, default: 'pending'
    add_index :orders, :status
  end
end

# GOOD — when change can't auto-reverse
class MigrateStatusToEnum < ActiveRecord::Migration[8.0]
  def up
    execute <<-SQL
      ALTER TABLE orders ALTER COLUMN status TYPE integer
      USING CASE status
        WHEN 'pending' THEN 0
        WHEN 'active' THEN 1
        WHEN 'archived' THEN 2
      END
    SQL
  end

  def down
    execute <<-SQL
      ALTER TABLE orders ALTER COLUMN status TYPE varchar
      USING CASE status
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'active'
        WHEN 2 THEN 'archived'
      END
    SQL
  end
end

# GOOD — reversible block inside change (hybrid)
class ChangeOrderStatusDefault < ActiveRecord::Migration[8.0]
  def change
    reversible do |dir|
      dir.up   { change_column_default :orders, :status, from: 'new', to: 'pending' }
      dir.down { change_column_default :orders, :status, from: 'pending', to: 'new' }
    end
  end
end
```

**Why `change`:** Rails auto-reverses `add_column`, `create_table`, `add_index`, `add_reference`, etc. You never forget to write the `down` method. Use `up`/`down` only for raw SQL or non-reversible operations.

---

## 2. Zero-Downtime Migrations

### Renaming a Column (3-step process)

```ruby
# Step 1: Add new column, deploy, write to BOTH columns
class AddFullNameToUsers < ActiveRecord::Migration[8.0]
  def change
    add_column :users, :full_name, :string
  end
end

# Step 2: Backfill data, deploy, switch reads to new column
class BackfillFullName < ActiveRecord::Migration[8.0]
  def up
    User.in_batches.update_all('full_name = name')
  end

  def down; end
end

# Step 3: Remove old column (after step 1 + 2 are live)
class RemoveNameFromUsers < ActiveRecord::Migration[8.0]
  def change
    remove_column :users, :name, :string
  end
end
```

**Why 3 steps:** Renaming in one step locks the table and breaks running app instances that reference the old column name.

### Adding Indexes Without Locking (PostgreSQL)

```ruby
# GOOD — concurrent index creation
class AddIndexToOrdersEmail < ActiveRecord::Migration[8.0]
  disable_ddl_transaction!

  def change
    add_index :orders, :email, algorithm: :concurrently
  end
end

# BAD — locks the table for writes during index creation
class AddIndexToOrdersEmail < ActiveRecord::Migration[8.0]
  def change
    add_index :orders, :email
  end
end
```

**Why `disable_ddl_transaction!`:** `CONCURRENTLY` cannot run inside a transaction. Without it, `add_index` locks the table for writes on large tables. SQLite note: concurrent indexing is not available, but tables are typically small.

### Adding a Column with Default

```ruby
# SAFE in PostgreSQL 11+ — no table rewrite
add_column :orders, :priority, :integer, default: 0, null: false

# For older PostgreSQL or adding NOT NULL to existing column:
add_column :orders, :priority, :integer            # Step 1: nullable
Order.in_batches.update_all(priority: 0)           # Step 2: backfill
change_column_null :orders, :priority, false        # Step 3: constraint
change_column_default :orders, :priority, 0
```

### Removing a Column Safely

```ruby
# Step 1: Ignore column in model (deploy first)
class Order < ApplicationRecord
  self.ignored_columns += ['legacy_field']
end

# Step 2: Remove column in migration (deploy after step 1 is live)
class RemoveLegacyFieldFromOrders < ActiveRecord::Migration[8.0]
  def change
    remove_column :orders, :legacy_field, :string
  end
end
```

**Why `ignored_columns`:** Active Record caches column info at boot. If a running instance references a removed column, it crashes.

### Adding NOT NULL to Existing Column (PostgreSQL)

```ruby
# GOOD — two-step, avoids long table lock
class AddNotNullConstraint < ActiveRecord::Migration[8.0]
  def change
    add_check_constraint :orders, 'status IS NOT NULL',
                         name: 'orders_status_not_null', validate: false
  end
end

class ValidateNotNullConstraint < ActiveRecord::Migration[8.0]
  def change
    validate_check_constraint :orders, name: 'orders_status_not_null'
    change_column_null :orders, :status, false
    remove_check_constraint :orders, name: 'orders_status_not_null'
  end
end

# BAD — locks table while scanning every row
change_column_null :orders, :status, false
```

---

## 3. Data Migrations

```ruby
# GOOD — rake task for data backfill
namespace :one_off do
  desc 'Backfill order status from legacy field'
  task backfill_order_status: :environment do
    Order.where(status: nil).in_batches(of: 1000) do |batch|
      batch.update_all("status = CASE WHEN legacy_active THEN 1 ELSE 0 END")
    end
  end
end

# GOOD — maintenance_tasks gem (recommended for Rails 8)
module Maintenance
  class BackfillOrderStatusTask < MaintenanceTasks::Task
    def collection = Order.where(status: nil)
    def process(order) = order.update!(status: order.legacy_active ? 1 : 0)
    def count = Order.where(status: nil).count
  end
end

# BAD — data manipulation in schema migration
class AddStatusToOrders < ActiveRecord::Migration[8.0]
  def change
    add_column :orders, :status, :integer
    Order.find_each { |o| o.update!(status: compute_status(o)) }
  end
end
```

**Why separate:** The model class at migration time is the *current* class, not the class when the migration was written. Columns, validations, and callbacks may differ.

### Batching Large Updates

```ruby
# GOOD — in_batches + update_all (no callbacks, fastest)
Order.where(status: nil).in_batches(of: 1000) { |b| b.update_all(status: 'pending') }

# GOOD — find_each when you need model callbacks
Order.where(status: nil).find_each(batch_size: 500) { |o| o.update!(status: 'pending') }

# BAD — loads entire table / single UPDATE locking millions of rows
Order.where(status: nil).each { |o| o.update!(status: 'pending') }  # memory
Order.where(status: nil).update_all(status: 'pending')               # table lock
```

---

## 4. Indexes

```ruby
# Single column — for WHERE / ORDER BY
add_index :users, :email

# Composite — column ORDER matters! Leftmost column used for prefix queries
add_index :orders, [:user_id, :created_at]
# Used for: WHERE user_id = 1; WHERE user_id = 1 AND created_at > '...'
# NOT used for: WHERE created_at > '...' (no leftmost prefix)

# Unique — data integrity at DB level
add_index :users, :email, unique: true
add_index :memberships, [:user_id, :team_id], unique: true

# Partial — only index relevant rows (smaller, faster)
add_index :orders, :shipped_at, where: 'shipped_at IS NOT NULL', name: 'idx_orders_shipped'

# Expression — for computed queries (PostgreSQL)
add_index :users, 'lower(email)', unique: true, name: 'idx_users_lower_email'

# GIN — for JSONB and array columns (PostgreSQL)
add_index :products, :metadata, using: :gin
```

| Always Index | Consider Indexing | Skip Indexing |
|---|---|---|
| Foreign keys (`_id` columns) | Columns in frequent WHERE | Boolean columns (low cardinality) |
| Columns in UNIQUE constraints | Columns in ORDER BY | Tiny tables (<1000 rows) |
| Columns used in JOIN ON | Columns in GROUP BY | Columns rarely queried |
| Polymorphic type + id pairs | Columns used with LIKE prefix | Write-heavy columns with no reads |

**Why index foreign keys:** Rails does not auto-index FKs. Without an index, every `DELETE` on the parent triggers a sequential scan on the child table.

---

## 5. Foreign Keys

```ruby
# GOOD — add_reference adds column + index + FK in one call
add_reference :orders, :user, null: false, foreign_key: true

# GOOD — specify on_delete behavior explicitly
add_foreign_key :comments, :posts, on_delete: :cascade
add_foreign_key :orders, :users, on_delete: :nullify
add_foreign_key :payments, :orders, on_delete: :restrict

# BAD — column without foreign key (orphaned records possible)
add_column :orders, :user_id, :bigint
add_index :orders, :user_id
# Missing: add_foreign_key :orders, :users
```

| on_delete | Behavior | Use When |
|-----------|----------|----------|
| `:cascade` | Delete child records | Comments on a post, line items on an order |
| `:nullify` | Set FK to NULL | Optional relationship (user deletes account, keep orders) |
| `:restrict` | Prevent parent deletion | Financial records (never orphan payments) |
| (none) | Same as `:restrict` in PostgreSQL | Default — be explicit instead |

**Note:** Polymorphic associations (`commentable_type` + `commentable_id`) cannot have DB-level foreign keys. Prefer separate tables or STI when referential integrity matters.

---

## 6. Database Constraints

```ruby
# NOT NULL
add_column :users, :email, :string, null: false

# CHECK constraint (Rails 6.1+)
add_check_constraint :orders, 'total >= 0', name: 'orders_total_non_negative'
add_check_constraint :users, "role IN ('admin', 'member', 'guest')", name: 'users_valid_role'

# For large tables — add unvalidated, then validate separately
add_check_constraint :orders, 'total >= 0', name: 'check_total', validate: false
validate_check_constraint :orders, name: 'check_total'
```

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

```ruby
# Timestamps: _at suffix
:published_at, :archived_at, :shipped_at, :confirmed_at

# Booleans: no is_ prefix (Rails convention)
:active, :visible, :admin      # GOOD — generates active? predicate
:is_active, :is_visible        # BAD — redundant prefix

# Counters: _count suffix (for counter_cache)
:comments_count, :orders_count

# Money: decimal, NEVER float
add_column :orders, :total, :decimal, precision: 12, scale: 2

# Email: citext (case-insensitive, PostgreSQL)
enable_extension 'citext'
add_column :users, :email, :citext

# UUIDs as primary keys
create_table :api_tokens, id: :uuid do |t|
  t.references :user, null: false, foreign_key: true, type: :bigint
  t.string :token, null: false
  t.timestamps
end

# JSON columns (PostgreSQL jsonb)
add_column :settings, :preferences, :jsonb, default: {}, null: false
add_index :settings, :preferences, using: :gin

# Enum columns — integer with CHECK
add_column :orders, :status, :integer, default: 0, null: false
add_check_constraint :orders, 'status IN (0, 1, 2, 3)', name: 'orders_valid_status'
```

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

```ruby
# Model — Rails 7+ syntax, explicit integers
class Order < ApplicationRecord
  enum :status, { pending: 0, processing: 1, shipped: 2, delivered: 3, cancelled: 4 }
end

# Migration
class AddStatusToOrders < ActiveRecord::Migration[8.0]
  def change
    add_column :orders, :status, :integer, default: 0, null: false
    add_index :orders, :status
    add_check_constraint :orders, 'status BETWEEN 0 AND 4', name: 'orders_valid_status'
  end
end
```

```ruby
# GOOD — explicit integer mapping (safe against reordering)
enum :status, { pending: 0, processing: 1, shipped: 2 }
order.pending?  # predicate | order.shipped!  # update | Order.shipped  # scope

# BAD — array syntax (fragile, inserting between values shifts all after it)
enum :status, [:pending, :processing, :shipped]
```

**Why integer over PostgreSQL ENUM type:** Simpler to extend. PG `ALTER TYPE ... ADD VALUE` cannot run inside a transaction.

---

## 9. Transactions and Locking

```ruby
# GOOD — wrap related writes in a transaction
ActiveRecord::Base.transaction do
  order.update!(status: :completed)
  Payment.create!(order: order, amount: order.total)
  InventoryService.new(order).deduct!
end

# Optimistic locking — add lock_version column
add_column :orders, :lock_version, :integer, default: 0, null: false
# Raises ActiveRecord::StaleObjectError if another process updated first

# Pessimistic locking — SELECT ... FOR UPDATE
Order.transaction do
  order = Order.lock.find(42)
  order.update!(total: order.total + 50)
end

# Advisory locks (PostgreSQL) — application-level mutual exclusion
ActiveRecord::Base.connection.execute("SELECT pg_advisory_lock(12345)")
# ... critical section ...
ActiveRecord::Base.connection.execute("SELECT pg_advisory_unlock(12345)")
```

| Locking | Use When | Mechanism |
|---------|----------|-----------|
| Optimistic | Low contention, conflict is rare | `lock_version` column, raises on conflict |
| Pessimistic | High contention, must guarantee exclusive | `FOR UPDATE`, blocks others |
| Advisory | Application-level (cron, migrations) | `pg_advisory_lock`, lightweight |

---

## 10. Schema Management

### PostgreSQL-Specific Features

```ruby
# Extensions
enable_extension 'pgcrypto'    # gen_random_uuid()
enable_extension 'citext'      # case-insensitive text
enable_extension 'pg_trgm'     # trigram similarity for LIKE/ILIKE

# Materialized view (via scenic gem or raw SQL)
reversible do |dir|
  dir.up do
    execute <<-SQL
      CREATE MATERIALIZED VIEW monthly_revenue AS
      SELECT date_trunc('month', created_at) AS month,
             SUM(total) AS revenue, COUNT(*) AS order_count
      FROM orders WHERE status = 3 GROUP BY month WITH DATA
    SQL
  end
  dir.down { execute "DROP MATERIALIZED VIEW monthly_revenue" }
end
```

---

## 11. Strong Migrations (Gem)

```ruby
# Gemfile
gem 'strong_migrations'

# config/initializers/strong_migrations.rb
StrongMigrations.start_after = 20250101000000
StrongMigrations.target_postgresql_version = 16

# Catches: adding index without CONCURRENTLY, removing column without
# ignored_columns, changing column type, renaming table/column, etc.

# Override when you know it's safe
class AddIndex < ActiveRecord::Migration[8.0]
  disable_ddl_transaction!

  def change
    safety_assured { add_index :orders, :email, algorithm: :concurrently }
  end
end
```
