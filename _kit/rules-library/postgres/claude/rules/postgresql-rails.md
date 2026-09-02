---
paths:
  - "db/migrate/**/*.rb"
  - "config/database.yml"
  - "app/models/**/*.rb"
---

# PostgreSQL for Ruby on Rails

Based on Rails Guides (Active Record and PostgreSQL) and the PostgreSQL Documentation.

> Worked examples live in the `postgres-reference` skill (`references/rails.md`).

For migration fundamentals, basic indexes, constraints, and transactions, see `rails-database.md`.
For N+1 prevention and query optimization basics, see `rails-activerecord-queries.md`.
For universal PostgreSQL best practices (language-agnostic), see `postgresql-universal.md`.

---

## 1. Connection Management & Pooling

### Rails Pool Sizing

- Pool must be at least as large as the number of threads that can concurrently use the DB. **Formula:** `pool >= max_threads_per_process`. With Puma: `pool = RAILS_MAX_THREADS`. If Solid Queue workers share the process, add their threads.
- Production `database.yml` hardening: pull credentials from `ENV` (never hardcoded), set `connect_timeout` (fail fast on outage), `checkout_timeout`, `reaping_frequency`, `sslmode: require`, `statement_timeout`, `lock_timeout`, and `idle_in_transaction_session_timeout`.
- Footguns: oversized `pool` (e.g. 100) wastes DB connections (multiplied by app instances); `sslmode: disable` in prod; missing `connect_timeout`/`statement_timeout`.

### PgBouncer Integration

- With PgBouncer transaction pooling, set `prepared_statements: false` and `advisory_locks: false` (neither works under transaction pooling); point `host`/`port` at PgBouncer (default `6432`).

| PgBouncer Mode | prepared_statements | advisory_locks | SET commands | Best For |
|----------------|-------------------|---------------|-------------|----------|
| Session | Yes | Yes | Yes | Low concurrency, full PG features |
| Transaction | **No** | **No** | **No** | High concurrency web apps (default choice) |
| Statement | **No** | **No** | **No** | Simple read-only workloads |

**Why:** 10 Puma workers × 5 threads × 3 app servers = 150 connections. PgBouncer multiplexes these through 20-30 actual DB connections, slashing PostgreSQL memory usage.

### Connection Health

- Health/repair via `connection.active?`, `connection.reconnect!`; inspect the pool with `connection_pool.stat`.

---

## 2. Multi-Database Setup (Rails 8)

### Primary + Read Replica

- Declare `primary` and `primary_replica` (`replica: true`) in `database.yml`; wire `connects_to database: { writing:, reading: }` in `ApplicationRecord`.
- Enable automatic role switching via `config.active_record.database_selector` / `database_resolver` / `database_resolver_context`.
- **How it works:** after a write, Rails waits `delay` seconds before routing reads to the replica (lets replication catch up). GET → replica; POST/PUT/PATCH/DELETE → primary.
- Reads default to primary inside a request unless wrapped — wrap heavy read-only analytics explicitly with `connected_to(role: :reading)`.

### Separate Databases for Solid Stack

- Give each Solid component its own DB entry with a distinct `database:` and `migrations_paths:` when its volume warrants it.

| Component | Separate DB When | Same DB When |
|-----------|-----------------|-------------|
| Solid Queue | >1000 jobs/minute, avoid lock contention | Low job volume, simple setup |
| Solid Cache | Large cache (>1GB), high read rate | Small cache, few reads |
| Solid Cable | Many WebSocket connections, fast polling | Few connections |

---

## 3. Advanced Query Patterns

### Window Functions

- A window function in the SELECT alias can't be filtered in the same query's WHERE — wrap it in a subquery via `.from`. Use `find_by_sql` for raw ranking forms.

### CTEs

- Recursive CTEs (`WITH RECURSIVE`) handle tree/graph walks (track depth + path) via `find_by_sql`. Non-recursive CTEs (`WITH x AS (...)`) are fine for readable multi-step aggregation.

### NOT EXISTS vs NOT IN

- Never use `NOT IN` with a subquery — it returns ZERO rows if any subquery value is NULL. Use `NOT EXISTS` or a `left_joins(...).where(...: { id: nil })` anti-join instead.
- **Why NOT IN fails:** `NOT IN (1, 2, NULL)` becomes `x != 1 AND x != 2 AND x != NULL`; `x != NULL` is UNKNOWN, so the whole expression is UNKNOWN → no rows.

### MERGE (PG 15+) & Upsert

- Use `MERGE` for complex conditional upserts (PG 15+). Prefer `ON CONFLICT` (`upsert` / `upsert_all`) for simple cases.

---

## 4. Full-Text Search

- Add a `GENERATED ALWAYS AS (...) STORED` `tsvector` column (use `setweight` to rank fields) plus a GIN index on it.
- Query with `@@ plainto_tsquery(...)`; rank with `ts_rank`; highlight with `ts_headline`.
- The `pg_search` gem wraps this with `pg_search_scope` (supports `tsvector_column`, `prefix:`, `associated_against:`).

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

- Operators: `@>` containment (uses GIN), `?` key existence, `->>` nested text value, `->`/`->>` chains with casts for typed comparisons.
- **Index gotcha:** GIN supports `@>`, NOT `->>` equality. Rewrite `metadata ->> 'color' = 'red'` as `metadata @> '{"color":"red"}'` to use the GIN index (or add an expression B-tree index).

### GIN Index Strategies

| GIN Variant | Size | Supports | Use When |
|-------------|------|----------|----------|
| `USING GIN (col)` | Larger | `@>`, `?`, `?|`, `?&` | Need key existence checks |
| `USING GIN (col jsonb_path_ops)` | ~30% smaller | `@>` only | Only containment queries |
| Expression B-tree | Smallest | `=`, `<`, `>` on one key | Always query one specific key |

### Atomic Updates

- Avoid read-modify-write (`find` → mutate hash → `save!`) — concurrent requests overwrite each other. Update in SQL with `jsonb_set`, the `||` merge operator, or the `-` remove-key operator.

### JSONB vs Normalized Tables

- Use JSONB for semi-structured, rarely-queried data (settings, preferences, integration configs, webhook payloads). Never store core relational data (FKs, financial data) in JSONB — you lose joins, uniqueness, referential integrity. `store_accessor` gives Rails getters/setters for known keys.

| Use JSONB | Use Normalized Tables |
|-----------|----------------------|
| Schema varies per record | Schema is consistent |
| Written once, read by containment | Frequently joined/aggregated |
| External API payloads, configs | Core domain entities |
| Fewer than 5 keys queried frequently | Relationships between entities |
| No need for FK or uniqueness | Need FK, UNIQUE, referential integrity |

---

## 6. Array Columns

- Declare with `array: true, default: [], null: false`; index with GIN. Query with `@>` (contains ALL), `&&` (contains ANY), `= ANY(...)` (single value). Mutate with `array_append` / `array_remove`; aggregate with `array_agg`; expand with `CROSS JOIN unnest(...)`.

| Use Array | Use Join Table |
|-----------|---------------|
| <20 values per record | Unbounded values |
| Simple strings/ints | Values are domain entities with own attributes |
| Only need containment queries | Need COUNT, GROUP BY, individual updates |
| No efficient "all items with tag X" at scale | Frequent reverse lookups |
| Tags, labels, simple flags | Categories, permissions, many-to-many |

---

## 7. Range Types & Exclusion Constraints

- A range column + exclusion constraint enforces non-overlap atomically at the DB level. Two separate `start_date`/`end_date` columns can't use an exclusion constraint, forcing app-level overlap checks (race condition) and manual `start < end` validation. Ranges also auto-validate `lower < upper`.
- Enable `btree_gist`, define the constraint as `EXCLUDE USING GIST (scope_col WITH =, range_col WITH &&)`, and add a GiST index on the range column. Query with `@>` (contains), `&&` (overlaps), `<@` (within).

| Type | Contains | Example |
|------|----------|---------|
| `daterange` | Dates | Room bookings, event schedules |
| `tstzrange` | Timestamptz | Shift schedules, precise time slots |
| `int4range` / `int8range` | Integers | Version ranges, age brackets |
| `numrange` | Numeric | Price ranges, measurement tolerances |

---

## 8. Generated Columns

- Generated columns (PG 12+) keep derived data always in sync without callbacks. Callbacks (`before_validation`) drift out of sync when records are touched via `update_all`, raw SQL, console, or rake tasks. Index them as needed.
- **Limitations:** Can only reference columns in the same table; cannot call volatile functions (e.g. `NOW()`); write `STORED` explicitly — PG 18 adds VIRTUAL (computed on read) and makes it the *default*, and virtual generated columns cannot be indexed. Common use beyond derived text: generated `tsvector` for search (see §4).

---

## 9. Database Views & Scenic

- Back a complex aggregation with a Scenic view (`db/views/*.sql` + `create_view`) and a read-only model (`self.primary_key`, `def readonly? = true`).

### Materialized Views

- Use `create_view ..., materialized: true` for expensive, staleness-tolerant computation; a **unique index is REQUIRED for concurrent refresh**. Refresh on a schedule with `Scenic.database.refresh_materialized_view(..., concurrently: true)`.

| Use | When |
|-----|------|
| Database view (scenic) | Complex aggregation/join used across app, needs SQL-level optimization |
| Materialized view | Expensive computation, can tolerate staleness (scheduled refresh) |
| Query object (`app/queries/`) | Complex query used in 2+ places, Ruby-level composition needed |
| Scope | Simple WHERE/ORDER/JOIN, single model, one-liner |

---

## 10. Table Partitioning

- Range-partition time-series tables with `PARTITION BY RANGE (created_at)`; the partition key must be in the PK. Indexes created on the parent propagate to each partition.
- Models work transparently. Queries filtering on the partition key get partition pruning (skip irrelevant partitions).
- **Dropping old data:** `DROP TABLE events_2023_q1` is instant, lock-free, leaves no dead tuples — far better than `delete_all`, which scans row-by-row, creates dead tuples, and locks.

| Partition When | Don't Partition When |
|---------------|---------------------|
| Table > 10M rows | Table < 1M rows |
| Queries always filter by partition key | Queries don't filter by partition key |
| Need to DROP old data quickly | Data retention is indefinite |
| Time-series / event logs / audit trails | Core entity tables (users, orders) |
| Write-heavy, old data rarely accessed | Uniform access across all data |

---

## 11. Row-Level Security (Multi-Tenant)

- RLS enforces tenant isolation at the database level — it cannot be bypassed by console, rake tasks, background jobs, or raw SQL. Application scoping (`Order.where(tenant_id:)`) must be remembered in every code path and is easy to forget.
- Enable + `FORCE ROW LEVEL SECURITY` (applies even to the table owner) and define `USING` / `WITH CHECK` policies keyed on `current_setting('app.current_tenant_id')`.
- Set the tenant per request in middleware via `SET app.current_tenant_id`, and **`RESET` it in an `ensure` block** to avoid leakage across pooled connections; sanitize the value.
- **Important:** Index columns used in RLS policies for performance (`add_index :orders, :tenant_id`). RLS does not compose with PgBouncer transaction pooling using session-level `SET` — set the var per-transaction or use session pooling.

---

## 12. Performance Monitoring from Rails

- **pg_stat_statements** — enable via `shared_preload_libraries` + `CREATE EXTENSION`; query it (order by `mean_exec_time`) to find the slowest queries.
- **PgHero** — mount the engine behind an admin auth check; surfaces slow queries, missing/unused index suggestions, connection stats, table/index sizes, replication lag, VACUUM/ANALYZE needs.
- **EXPLAIN from Rails (7.1+)** — `relation.explain(:analyze, :buffers)`; raw `EXPLAIN (ANALYZE, BUFFERS, FORMAT YAML)` for complex queries.
- **Query Log Tags (Rails 7+)** — enable `query_log_tags_enabled` + `query_log_tags` to trace slow queries back to the exact controller/action/job via SQL comments.
- **auto_explain** — in `postgresql.conf`, log execution plans for slow queries (`log_min_duration`, `log_analyze`, `log_buffers`).

---

## 13. Solid Stack & PostgreSQL

- Solid Queue claims jobs with `FOR UPDATE SKIP LOCKED` — locked rows are skipped rather than waited on, giving zero contention between workers.
- Tune `polling_interval` / `batch_size` / `threads` / `processes` per queue priority in `config/queue.yml`; schedule recurring jobs in `config/recurring.yml`.
- Point Solid Queue at a dedicated queue database (`migrations_paths` + `connects_to`) when volume warrants.

| Separate DB When | Same DB OK When |
|-----------------|----------------|
| >1000 jobs/minute | <100 jobs/minute |
| Queue operations cause lock contention | Low write volume |
| Need independent monitoring | Simple deployment |
| Queue tables grow to millions of rows | Queue stays small |

---

## 14. Anti-Patterns & Production Checklist

### Rails-Specific PostgreSQL Anti-Patterns

- `.count` in a loop → N COUNT queries. Use `counter_cache`, or preload with a single grouped `.group(...).count`.
- `pluck`-then-WHERE loads IDs into Ruby and ships thousands back. Use a subquery (`where(... : Model.where(...).select(:id))`) so it stays in the DB.
- `update_all` on a huge table → one giant lock + WAL bloat. Batch with `in_batches`.
- Loading full JSONB to read one key → extract at SQL level with `pluck(Arel.sql("metadata ->> 'color'"))`.
- Rails-only attribute defaults don't apply to raw SQL/console/migrations — set DB-level defaults (`add_column ..., null: false, default: ...`).
- Always `EXPLAIN` new queries — an unanchored `ILIKE '%q%'` is a full table scan.

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
