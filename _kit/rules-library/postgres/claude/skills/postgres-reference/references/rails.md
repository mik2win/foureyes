# PostgreSQL with Rails — worked examples

Companion reference to the `postgresql-rails` rule; loaded on demand.

---

## 1. Connection Management & Pooling

### Rails Pool Sizing

The pool must be at least as large as the number of threads that can concurrently use the database. **Formula:** `pool >= max_threads_per_process`. With Puma: `pool = RAILS_MAX_THREADS`. If Solid Queue workers run in the same process, add their threads.

```yaml
# production database.yml — required hardening
production:
  adapter: postgresql
  encoding: unicode
  pool: <%= ENV.fetch('RAILS_MAX_THREADS', 5) %>
  host: <%= ENV['DATABASE_HOST'] %>
  username: <%= ENV['DATABASE_USER'] %>
  password: <%= ENV['DATABASE_PASSWORD'] %>   # always ENV, never hardcoded
  connect_timeout: 2            # fail fast if DB unreachable (else hangs on outage)
  checkout_timeout: 5           # wait max 5s for connection from pool
  reaping_frequency: 10         # check for dead connections every 10s
  sslmode: require              # encrypt connections in production
  statement_timeout: '30s'      # kill runaway queries
  lock_timeout: '10s'           # don't wait > 10s for locks
  variables:
    idle_in_transaction_session_timeout: '30s'  # kill idle-in-transaction
```

Footguns: oversized `pool` (e.g. 100) wastes DB connections (multiplied by app instances); `sslmode: disable` in prod; missing `connect_timeout`/`statement_timeout`.

### PgBouncer Integration

```yaml
# database.yml with PgBouncer (transaction pooling)
production:
  host: <%= ENV['PGBOUNCER_HOST'] %>
  port: 6432                          # PgBouncer default port
  prepared_statements: false          # REQUIRED for transaction pooling
  advisory_locks: false               # advisory locks don't work with transaction pooling
  pool: <%= ENV.fetch('RAILS_MAX_THREADS', 5) %>
```

| PgBouncer Mode | prepared_statements | advisory_locks | SET commands | Best For |
|----------------|-------------------|---------------|-------------|----------|
| Session | Yes | Yes | Yes | Low concurrency, full PG features |
| Transaction | **No** | **No** | **No** | High concurrency web apps (default choice) |
| Statement | **No** | **No** | **No** | Simple read-only workloads |

**Why:** 10 Puma workers × 5 threads × 3 app servers = 150 connections. PgBouncer multiplexes these through 20-30 actual DB connections, slashing PostgreSQL memory usage.

### Connection Health

```ruby
ActiveRecord::Base.connection.active?      # health check
ActiveRecord::Base.connection.reconnect!   # reconnect stale connection
ActiveRecord::Base.connection_pool.stat
# => {size: 5, connections: 3, busy: 1, dead: 0, idle: 2, waiting: 0, checkout_timeout: 5}
```

---

## 2. Multi-Database Setup (Rails 8)

### Primary + Read Replica

```yaml
# config/database.yml
production:
  primary:         { <<: *default, host: primary-db.example.com }
  primary_replica: { <<: *default, host: replica-db.example.com, replica: true }
```

```ruby
# app/models/application_record.rb
class ApplicationRecord < ActiveRecord::Base
  primary_abstract_class
  connects_to database: { writing: :primary, reading: :primary_replica }
end

# config/application.rb — automatic role switching
config.active_record.database_selector = { delay: 2.seconds }
config.active_record.database_resolver =
  ActiveRecord::Middleware::DatabaseSelector::Resolver
config.active_record.database_resolver_context =
  ActiveRecord::Middleware::DatabaseSelector::Resolver::Session
```

**How it works:** After a write, Rails waits `delay` seconds before routing reads to the replica (lets replication catch up). GET → replica; POST/PUT/PATCH/DELETE → primary.

```ruby
# Manual role switching when auto-routing isn't enough
ActiveRecord::Base.connected_to(role: :reading) do
  @reports = Order.where(status: :paid).group(:month).sum(:total)
end
# Reads default to primary inside a request unless wrapped — wrap heavy read-only analytics explicitly.
```

### Separate Databases for Solid Stack

```yaml
production:
  primary:  { <<: *default, database: myapp_production }
  queue:    { <<: *default, database: myapp_queue,  migrations_paths: db/queue_migrate }
  cache:    { <<: *default, database: myapp_cache,  migrations_paths: db/cache_migrate }
  cable:    { <<: *default, database: myapp_cable,  migrations_paths: db/cable_migrate }
```

| Component | Separate DB When | Same DB When |
|-----------|-----------------|-------------|
| Solid Queue | >1000 jobs/minute, avoid lock contention | Low job volume, simple setup |
| Solid Cache | Large cache (>1GB), high read rate | Small cache, few reads |
| Solid Cable | Many WebSocket connections, fast polling | Few connections |

---

## 3. Advanced Query Patterns

### Window Functions

A window function in the SELECT alias can't be filtered in the same query's WHERE — wrap it in a subquery via `.from`:

```ruby
# Latest order per user (filter on window result via subquery)
Order.from(
  Order.select('orders.*',
    "ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn"),
  :orders
).where(rn: 1)

# Raw SQL form for ranking
User.find_by_sql(<<~SQL.squish)
  SELECT users.*, ROW_NUMBER() OVER (ORDER BY order_count DESC) AS rank
  FROM users
  JOIN (SELECT user_id, COUNT(*) AS order_count FROM orders
        WHERE status = 'paid' GROUP BY user_id) counts ON users.id = counts.user_id
  LIMIT 100
SQL
```

### CTEs

```ruby
# Recursive CTE for a category tree (tracks depth + path)
Category.find_by_sql(<<~SQL.squish)
  WITH RECURSIVE category_tree AS (
    SELECT id, name, parent_id, 0 AS depth, ARRAY[id] AS path
    FROM categories WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, c.name, c.parent_id, ct.depth + 1, ct.path || c.id
    FROM categories c JOIN category_tree ct ON c.parent_id = ct.id
  )
  SELECT * FROM category_tree ORDER BY path
SQL
```

Non-recursive CTEs (`WITH x AS (...)`) are fine for readable multi-step aggregation via `find_by_sql`.

### NOT EXISTS vs NOT IN

```ruby
# WRONG — NOT IN with subquery returns ZERO rows if any subquery value is NULL
User.where.not(id: Order.select(:user_id))

# Right — NULL-safe alternatives
User.where("NOT EXISTS (SELECT 1 FROM orders WHERE orders.user_id = users.id)")
User.left_joins(:orders).where(orders: { id: nil })
```

**Why NOT IN fails:** `NOT IN (1, 2, NULL)` becomes `x != 1 AND x != 2 AND x != NULL`; `x != NULL` is UNKNOWN, so the whole expression is UNKNOWN → no rows.

### MERGE (PG 15+) & Upsert

```ruby
# MERGE for complex conditional upsert (PG 15+)
ActiveRecord::Base.connection.execute(<<~SQL)
  MERGE INTO product_inventory AS target
  USING (VALUES (1, 50), (2, 30)) AS source(product_id, quantity)
  ON target.product_id = source.product_id
  WHEN MATCHED THEN UPDATE SET quantity = target.quantity + source.quantity, updated_at = NOW()
  WHEN NOT MATCHED THEN INSERT (product_id, quantity, created_at, updated_at)
    VALUES (source.product_id, source.quantity, NOW(), NOW())
SQL

# Prefer ON CONFLICT (upsert/upsert_all) for simple cases
Order.upsert_all(records, unique_by: :external_id)
```

---

## 4. Full-Text Search

### Migration: generated tsvector + GIN index

```ruby
class AddSearchToArticles < ActiveRecord::Migration[8.0]
  def change
    execute <<~SQL
      ALTER TABLE articles ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
          setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
          setweight(to_tsvector('english', coalesce(body, '')), 'B')
        ) STORED;
    SQL
    add_index :articles, :search_vector, using: :gin
  end
end
```

### Model scope (with ranking / headline)

```ruby
class Article < ApplicationRecord
  scope :search, ->(query) {
    where("search_vector @@ plainto_tsquery('english', ?)", query)
      .order(Arel.sql(
        "ts_rank(search_vector, plainto_tsquery('english', #{connection.quote(query)})) DESC"))
  }

  scope :search_with_headline, ->(query) {
    search(query).select('articles.*', Arel.sql(
      "ts_headline('english', body, plainto_tsquery('english', #{connection.quote(query)}), " \
      "'StartSel=<mark>, StopSel=</mark>, MaxWords=35, MinWords=15') AS headline"))
  }
end
```

### pg_search Gem

```ruby
class Article < ApplicationRecord
  include PgSearch::Model
  pg_search_scope :search,
    against: { title: 'A', body: 'B' },
    using: { tsearch: { dictionary: 'english', tsvector_column: 'search_vector',
                        prefix: true } }   # prefix: partial word matching
  pg_search_scope :global_search,
    against: [:title, :body],
    associated_against: { author: [:name, :bio], tags: [:name] }
end
```

### Search Solution Decision Table

| Approach | Pros | Cons | Use When |
|----------|------|------|----------|
| `ILIKE '%query%'` | Simple, no setup | No ranking, slow on large tables, no stemming | <10k rows, substring match |
| pg_trgm + GIN | Fuzzy, typo tolerant | No semantic ranking, larger index | Autocomplete, typo-tolerant search |
| Built-in FTS (tsvector) | Ranking, stemming, fast, no external dep | Language-specific, no fuzzy | Main search for most apps |
| pg_search gem | Easy Rails integration, combines strategies | Gem dependency | Rails apps wanting FTS + trigram |
| Elasticsearch / Meilisearch | Fuzzy, facets, suggestions, real-time | External service, sync complexity | >1M docs, complex search UI |

---

## 5. JSONB Advanced Patterns

### Querying

```ruby
Product.where("metadata @> ?", { color: 'red' }.to_json)        # containment (uses GIN)
Product.where("metadata ? :key", key: 'color')                  # key existence
Product.where("metadata ->> 'color' = ?", 'red')               # nested text value
Product.where("(metadata -> 'dimensions' ->> 'width')::integer > ?", 100)
Product.where("metadata -> 'tags' ? :tag", tag: 'sale')         # array inside JSONB
```

**Index gotcha:** GIN supports the `@>` operator, NOT `->>` equality. Rewrite `metadata ->> 'color' = 'red'` as `metadata @> '{"color":"red"}'` to use the GIN index (or add an expression B-tree index, below).

### GIN Index Strategies

```ruby
add_index :products, :metadata, using: :gin                                   # all operators
add_index :products, :metadata, using: :gin, opclass: :jsonb_path_ops         # smaller, @> only
add_index :products, "(metadata ->> 'color')", name: 'idx_products_color'     # expression B-tree
```

| GIN Variant | Size | Supports | Use When |
|-------------|------|----------|----------|
| `USING GIN (col)` | Larger | `@>`, `?`, `?|`, `?&` | Need key existence checks |
| `USING GIN (col jsonb_path_ops)` | ~30% smaller | `@>` only | Only containment queries |
| Expression B-tree | Smallest | `=`, `<`, `>` on one key | Always query one specific key |

### Atomic Updates

Avoid read-modify-write (`find` → mutate hash → `save!`) — concurrent requests overwrite each other. Update in SQL:

```ruby
Product.where(id: 1).update_all("metadata = jsonb_set(metadata, '{color}', '\"blue\"')")
Product.where(id: 1).update_all("metadata = metadata || '{\"color\":\"blue\",\"sale\":true}'::jsonb")  # merge
Product.where(id: 1).update_all("metadata = metadata - 'deprecated_key'")  # remove key
```

### JSONB vs Normalized Tables

Use JSONB for semi-structured, rarely-queried data (settings, preferences, integration configs, webhook payloads). Never store core relational data (FKs, financial data) in JSONB — you lose joins, uniqueness, referential integrity. `store_accessor` gives Rails getters/setters for known keys:

```ruby
add_column :users, :preferences, :jsonb, default: {}, null: false
class User < ApplicationRecord
  store_accessor :preferences, :theme, :locale, :notifications_enabled
end
```

| Use JSONB | Use Normalized Tables |
|-----------|----------------------|
| Schema varies per record | Schema is consistent |
| Written once, read by containment | Frequently joined/aggregated |
| External API payloads, configs | Core domain entities |
| Fewer than 5 keys queried frequently | Relationships between entities |
| No need for FK or uniqueness | Need FK, UNIQUE, referential integrity |

---

## 6. Array Columns

```ruby
# Migration
add_column :articles, :tags, :string, array: true, default: [], null: false
add_index :articles, :tags, using: :gin

# Querying
Article.where("tags @> ARRAY[?]::varchar[]", ['ruby', 'rails'])   # contains ALL
Article.where("tags && ARRAY[?]::varchar[]", ['ruby', 'python'])  # contains ANY
Article.where("? = ANY(tags)", 'ruby')                            # single value

# Mutate
Article.where(id: 1).update_all("tags = array_append(tags, 'new_tag')")
Article.where(id: 1).update_all("tags = array_remove(tags, 'old_tag')")

# Aggregate / expand
User.joins(:articles)
    .select("users.*, array_agg(DISTINCT articles.category ORDER BY articles.category) AS categories")
    .group("users.id")
Article.joins("CROSS JOIN unnest(tags) AS tag").group("tag").order("count DESC")
       .pluck(Arel.sql("tag, COUNT(*) AS count"))   # unnest array to rows
```

| Use Array | Use Join Table |
|-----------|---------------|
| <20 values per record | Unbounded values |
| Simple strings/ints | Values are domain entities with own attributes |
| Only need containment queries | Need COUNT, GROUP BY, individual updates |
| No efficient "all items with tag X" at scale | Frequent reverse lookups |
| Tags, labels, simple flags | Categories, permissions, many-to-many |

---

## 7. Range Types & Exclusion Constraints

A range column + exclusion constraint enforces non-overlap atomically at the DB level. Two separate `start_date`/`end_date` columns can't use an exclusion constraint, forcing app-level overlap checks (race condition) and manual `start < end` validation. Ranges also auto-validate `lower < upper`.

```ruby
class CreateBookings < ActiveRecord::Migration[8.0]
  def change
    enable_extension 'btree_gist'
    create_table :bookings do |t|
      t.references :room, null: false, foreign_key: true
      t.daterange :dates, null: false
      t.references :user, null: false, foreign_key: true
      t.timestamps
    end
    reversible do |dir|
      dir.up do
        execute <<~SQL
          ALTER TABLE bookings ADD CONSTRAINT no_overlapping_bookings
          EXCLUDE USING GIST (room_id WITH =, dates WITH &&)
        SQL
      end
    end
    add_index :bookings, :dates, using: :gist
  end
end
```

```ruby
# Querying ranges
Booking.where("dates @> ?::date", Date.current)               # includes today
Booking.where("dates && daterange(?, ?)", check_in, check_out) # overlaps range
Booking.where("dates <@ daterange(?, ?)", start_date, end_date) # entirely within
```

| Type | Contains | Example |
|------|----------|---------|
| `daterange` | Dates | Room bookings, event schedules |
| `tstzrange` | Timestamptz | Shift schedules, precise time slots |
| `int4range` / `int8range` | Integers | Version ranges, age brackets |
| `numrange` | Numeric | Price ranges, measurement tolerances |

---

## 8. Generated Columns

Generated columns (PG 12+) keep derived data always in sync without callbacks. Callbacks (`before_validation`) drift out of sync when records are touched via `update_all`, raw SQL, console, or rake tasks.

```ruby
execute <<~SQL
  ALTER TABLE users ADD COLUMN full_name TEXT
    GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED
SQL
add_index :users, :full_name
# Then: User.order(:full_name); User.where("full_name ILIKE ?", "%alice%")
```

**Limitations:** Can only reference columns in the same table; cannot call volatile functions (e.g. `NOW()`); write `STORED` explicitly — PG 18 adds VIRTUAL (computed on read) and makes it the *default*, and virtual generated columns cannot be indexed. Common use beyond derived text: generated `tsvector` for search (see §4).

---

## 9. Database Views & Scenic

```sql
-- db/views/user_stats_v01.sql
SELECT users.id AS user_id, users.email,
       COUNT(orders.id) AS orders_count,
       COALESCE(SUM(orders.total_cents), 0) AS total_spent_cents,
       MAX(orders.created_at) AS last_order_at
FROM users LEFT JOIN orders ON orders.user_id = users.id AND orders.status = 'paid'
GROUP BY users.id, users.email
```

```ruby
# Migration + read-only model
class CreateUserStats < ActiveRecord::Migration[8.0]
  def change; create_view :user_stats; end
end
class UserStat < ApplicationRecord
  self.primary_key = :user_id
  belongs_to :user
  def readonly? = true
end
```

### Materialized Views

```ruby
create_view :monthly_revenues, materialized: true
add_index :monthly_revenues, :month, unique: true   # unique index REQUIRED for concurrent refresh

# Refresh off a schedule (Solid Queue recurring job)
Scenic.database.refresh_materialized_view(:monthly_revenues, concurrently: true, cascade: false)
```

| Use | When |
|-----|------|
| Database view (scenic) | Complex aggregation/join used across app, needs SQL-level optimization |
| Materialized view | Expensive computation, can tolerate staleness (scheduled refresh) |
| Query object (`app/queries/`) | Complex query used in 2+ places, Ruby-level composition needed |
| Scope | Simple WHERE/ORDER/JOIN, single model, one-liner |

---

## 10. Table Partitioning

### Range Partitioning (Time-Series)

```ruby
class CreateEvents < ActiveRecord::Migration[8.0]
  def up
    execute <<~SQL
      CREATE TABLE events (
        id BIGINT GENERATED ALWAYS AS IDENTITY,
        event_type TEXT NOT NULL,
        payload JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (id, created_at)         -- partition key must be in PK
      ) PARTITION BY RANGE (created_at);

      CREATE TABLE events_2024_q1 PARTITION OF events
        FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
      -- ...q2/q3/q4 likewise
    SQL
    execute "CREATE INDEX ON events (event_type)"   # propagates to each partition
    execute "CREATE INDEX ON events (created_at)"
  end
  def down; drop_table :events; end
end
```

Models work transparently. Queries filtering on the partition key get partition pruning (skip irrelevant partitions): `Event.where(created_at: 1.month.ago..Time.current)`.

**Dropping old data:** `DROP TABLE events_2023_q1` is instant, lock-free, leaves no dead tuples — far better than `delete_all`, which scans row-by-row, creates dead tuples, and locks.

| Partition When | Don't Partition When |
|---------------|---------------------|
| Table > 10M rows | Table < 1M rows |
| Queries always filter by partition key | Queries don't filter by partition key |
| Need to DROP old data quickly | Data retention is indefinite |
| Time-series / event logs / audit trails | Core entity tables (users, orders) |
| Write-heavy, old data rarely accessed | Uniform access across all data |

---

## 11. Row-Level Security (Multi-Tenant)

RLS enforces tenant isolation at the database level — it cannot be bypassed by console, rake tasks, background jobs, or raw SQL. Application scoping (`Order.where(tenant_id:)`) must be remembered in every code path and is easy to forget.

```ruby
# Migration
execute <<~SQL
  ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
  ALTER TABLE orders FORCE ROW LEVEL SECURITY;   -- applies even to table owner
  CREATE POLICY tenant_isolation ON orders
    USING (tenant_id = current_setting('app.current_tenant_id')::bigint);
  CREATE POLICY tenant_insert ON orders FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::bigint);
SQL
```

```ruby
# Middleware sets the tenant per request; RESET in ensure to avoid leakage across pooled connections
class TenantMiddleware
  def initialize(app); @app = app; end
  def call(env)
    request = ActionDispatch::Request.new(env)
    tenant_id = resolve_tenant(request)
    if tenant_id
      ActiveRecord::Base.connection.execute(
        ActiveRecord::Base.sanitize_sql(["SET app.current_tenant_id = ?", tenant_id.to_s]))
    end
    @app.call(env)
  ensure
    ActiveRecord::Base.connection.execute("RESET app.current_tenant_id") rescue nil
  end
  private
  def resolve_tenant(request)
    request.subdomain.presence && Tenant.find_by(subdomain: request.subdomain)&.id
  end
end
# config/application.rb: config.middleware.use TenantMiddleware
```

**Important:** Index columns used in RLS policies for performance: `add_index :orders, :tenant_id`. Note RLS does not compose with PgBouncer transaction pooling using session-level `SET` — set the var per-transaction or use session pooling.

---

## 12. Performance Monitoring from Rails

### pg_stat_statements

Enable via `shared_preload_libraries = 'pg_stat_statements'` + `CREATE EXTENSION pg_stat_statements;`. Find slowest queries:

```ruby
ActiveRecord::Base.connection.execute(<<~SQL).to_a
  SELECT LEFT(query, 100) AS query, calls,
         ROUND(mean_exec_time::numeric, 2) AS avg_ms,
         ROUND(total_exec_time::numeric / 1000, 2) AS total_seconds, rows
  FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10
SQL
```

### PgHero

```ruby
gem 'pghero'
# config/routes.rb
authenticate :user, ->(user) { user.admin? } do
  mount PgHero::Engine, at: 'pghero'
end
```

Provides: slow queries, missing/unused index suggestions, connection stats, table/index sizes, replication lag, VACUUM/ANALYZE needs.

### EXPLAIN from Rails (7.1+)

```ruby
Order.where(status: :active).explain(:analyze, :buffers)   # EXPLAIN (ANALYZE, BUFFERS)
# Raw, for complex queries:
ActiveRecord::Base.connection.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT YAML) ...").to_a
```

### Query Log Tags (Rails 7+)

Trace slow queries back to the exact controller/action/job by tagging generated SQL.

```ruby
config.active_record.query_log_tags_enabled = true
config.active_record.query_log_tags = [
  :application, :controller, :action, :job,
  { request_id: ->(c) { c[:controller]&.request&.request_id },
    line: ->(c) { c[:source_location] } }
]
# => SELECT * FROM orders /* application:MyApp,controller:orders,action:index,request_id:abc-123 */
```

### auto_explain

```ini
# postgresql.conf — log execution plans for slow queries
shared_preload_libraries = 'auto_explain,pg_stat_statements'
auto_explain.log_min_duration = '1s'   # log plans for queries > 1s
auto_explain.log_analyze = on          # actual timing
auto_explain.log_buffers = on          # buffer usage
auto_explain.log_format = 'yaml'
```

---

## 13. Solid Stack & PostgreSQL

Solid Queue claims jobs with `FOR UPDATE SKIP LOCKED` — locked rows are skipped rather than waited on, giving zero contention between workers:

```sql
SELECT id FROM solid_queue_ready_executions
WHERE queue_name = 'default' ORDER BY priority ASC, id ASC
LIMIT 1 FOR UPDATE SKIP LOCKED;
```

### Configuration

```yaml
# config/queue.yml — tune polling_interval per queue priority
production:
  dispatchers:
    - polling_interval: 1
      batch_size: 500
  workers:
    - { queues: "critical",       threads: 5, processes: 2, polling_interval: 0.1 }
    - { queues: "default,mailers", threads: 3, processes: 2, polling_interval: 0.5 }
    - { queues: "low",            threads: 2, processes: 1, polling_interval: 2 }

# config/recurring.yml
production:
  cleanup_sessions: { class: CleanupSessionsJob, schedule: every day at 3am }
```

### Dedicated Queue Database

```yaml
# config/database.yml
production:
  primary: { <<: *default, database: myapp_production }
  queue:   { <<: *default, database: myapp_queue, migrations_paths: db/queue_migrate }
```
```ruby
# config/solid_queue.yml
production:
  connects_to: { database: { writing: queue, reading: queue } }
```

| Separate DB When | Same DB OK When |
|-----------------|----------------|
| >1000 jobs/minute | <100 jobs/minute |
| Queue operations cause lock contention | Low write volume |
| Need independent monitoring | Simple deployment |
| Queue tables grow to millions of rows | Queue stays small |

---

## 14. Anti-Patterns & Production Checklist

### Rails-Specific PostgreSQL Anti-Patterns

```ruby
# .count in loop → N COUNT queries. Use counter_cache, or preload:
user_counts = Order.group(:user_id).count
users.each { |u| puts "#{u.name}: #{user_counts[u.id] || 0}" }

# pluck-then-WHERE loads IDs into Ruby and sends thousands back. Use a subquery:
Order.where(user_id: User.where(active: true).select(:id))   # stays in the DB

# update_all on a huge table → one giant lock + WAL bloat. Batch it:
Order.where(status: 'pending').in_batches(of: 5000) { |b| b.update_all(status: 'expired') }

# Loading full JSONB to read one key → extract at SQL level:
Product.pluck(Arel.sql("metadata ->> 'color'"))

# Rails-only attribute default doesn't apply to raw SQL/console/migrations.
# Set DB-level: add_column :orders, :status, :string, null: false, default: 'pending'

# Always EXPLAIN new queries — unanchored ILIKE '%q%' is a full table scan:
Order.where("description ILIKE ?", "%test%").explain(:analyze)
```

### Production Checklist

| Category | Check |
|----------|-------|
| **Connections** | Pool = Puma max_threads? |
| **Connections** | PgBouncer for >2 app instances? |
| **Connections** | connect_timeout and statement_timeout set? |
| **Connections** | SSL enabled (sslmode: require)? |
| **Connections** | Credentials in ENV, not hardcoded? |
| **Multi-DB** | Read replica for read-heavy apps? |
| **Multi-DB** | Separate DB for Solid Queue if high volume? |
| **Queries** | NOT EXISTS instead of NOT IN? |
| **Queries** | New queries checked with EXPLAIN ANALYZE? |
| **Queries** | Subqueries instead of pluck + where? |
| **Queries** | Batched updates for large datasets? |
| **Search** | FTS with generated tsvector + GIN index? |
| **JSONB** | GIN index on JSONB columns? |
| **JSONB** | Atomic updates (jsonb_set) not read-modify-write? |
| **Schema** | DB-level defaults, not just Rails defaults? |
| **Schema** | Generated columns instead of callbacks for derived data? |
| **Schema** | Exclusion constraints for non-overlapping ranges? |
| **Monitoring** | pg_stat_statements enabled? |
| **Monitoring** | PgHero or equivalent dashboard? |
| **Monitoring** | query_log_tags enabled for tracing? |
| **Monitoring** | auto_explain for slow queries? |
| **Partitioning** | Tables >10M rows evaluated for partitioning? |
| **RLS** | Multi-tenant isolation at DB level (not just app scoping)? |
</content>
</invoke>
