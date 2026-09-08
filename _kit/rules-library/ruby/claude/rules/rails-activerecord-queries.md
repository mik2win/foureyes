---
paths:
  - "app/models/**/*.rb"
  - "app/queries/**/*.rb"
---

# ActiveRecord Query Optimization

Based on Rails Guides (Active Record Query Interface).

> Worked examples live in the `rails-reference` skill (`references/queries.md`).

---

## 1. N+1 Prevention: includes vs preload vs eager_load

- N+1 = loading a collection (1 query) then touching an association per record (N queries). Eager-load to collapse it to 2 queries.

| Method | SQL Strategy | Use When |
|--------|-------------|----------|
| `includes` | Decides automatically (separate queries OR LEFT JOIN) | Default choice — Rails picks optimal strategy |
| `preload` | Always separate queries (`SELECT * FROM comments WHERE post_id IN (1,2,3)`) | Large result sets, no WHERE on association |
| `eager_load` | Always LEFT OUTER JOIN | Need to filter/order by association columns |

Decision tree:

- **Default:** `includes` — let Rails decide.
- **Filtering/ordering by association columns:** `eager_load`, or `includes` with `references`.
- **Large dataset, no filtering on association:** `preload`.
- **Need to avoid a JOIN:** `preload`.
- **Unbounded association: neither.** Eager-loading an association that grows without limit is the worst of the two diffs — it trades N small queries for one that pulls the whole history into memory. Bound the association where it is declared (a `has_many` scope with a limit or a date window, or a separate paginated query), not after the rows are loaded.

- Nest (`includes(comments: :author)`) and list multiple associations in one call.
- String SQL conditions on an included association need `.references(:comments)` to force the JOIN; hash conditions (`where(comments: { ... })`) auto-detect.

---

## 2. load_async (Rails 7+)

- Dispatch independent queries with `.load_async`; each runs on a background thread and blocks only when first accessed. Three 50ms queries finish in ~50ms instead of ~150ms.
- Don't chain `.to_a`/iterate eagerly between them — that forces sequential execution.
- Async queries use a separate internal pool; size `pool:` in `database.yml` accordingly.

---

## 3. Efficient Existence and Counting Checks

| Need | GOOD | BAD | Why |
|------|------|-----|-----|
| Record exists? | `users.exists?` | `users.present?` | `present?` loads ALL records |
| Any records? | `users.exists?` | `users.any?` | `any?` loads records if already loaded |
| Count | `users.count` | `users.length` | `length` loads all, `count` does SQL COUNT |
| Size (cached) | `users.size` | `users.count` | `size` uses counter_cache or loaded? check |
| Single column | `users.pluck(:email)` | `users.map(&:email)` | `map` instantiates AR objects |
| Single value | `users.pick(:email)` | `users.pluck(:email).first` | `pick` adds LIMIT 1 |
| All IDs | `users.ids` | `users.pluck(:id)` | `ids` is semantic alias |

- `pluck` returns plain arrays (reports, exports); `select(:id, :name)` returns AR objects carrying only those columns.

---

## 4. Batch Processing

- Never load an entire table into memory — batch it. `User.all.each` is the anti-pattern.

| Method | Yields | Use For |
|--------|--------|---------|
| `find_each` | One record at a time | Processing records individually |
| `find_in_batches` | Array of records (batch) | When you need batch context |
| `in_batches` | ActiveRecord::Relation | Bulk updates (`update_all`, `delete_all`) |

- Batch methods force ORDER BY primary key — a custom `order` is silently ignored.
- Scope and range batches with `where(...)`, `start:`, and `finish:`.

---

## 5. Query Objects

- Extract a query object when a query spans 3+ parameterized conditions, joins multiple tables, or is reused in multiple places. Keep simple 1-2 condition queries as model scopes.

| Signal | Action |
|--------|--------|
| 3+ conditions with parameters | Extract to query object |
| Same query logic in multiple places | Extract to query object |
| Joins across multiple tables | Extract to query object |
| Simple 1-2 condition query | Keep as scope on model |

---

## 6. SQL Safety

- Parameterize always — `where('email = ?', x)` or hash conditions `where(email: x)`. Never interpolate user input into a SQL string.
- Escape LIKE input with `sanitize_sql_like` — bare `%`/`_` are wildcards (`%` matches everything).
- Use Arel for complex predicates instead of raw strings.
- Allowlist any user-controlled `ORDER BY` column — never pass `params[:sort]` straight into `order`.

---

## 7. Efficient Updates and Inserts

- Bulk-write with one statement: `update_all`, `upsert_all` (insert-or-update), `insert_all` (skips dupes), `delete_all`. Avoid looping `update` over a relation.

| Method | Callbacks | Validations | SQL Queries | Use When |
|--------|-----------|-------------|-------------|----------|
| `update` | Yes | Yes | 1 per record | Need callbacks/validations |
| `update_all` | No | No | 1 total | Bulk data changes |
| `upsert_all` | No | No | 1 total | Insert-or-update in bulk |

- `*_all` methods bypass callbacks and validations — only use when that's acceptable.

---

## 8. EXPLAIN and Query Analysis

- Profile with `.explain` (plan) or `.explain(:analyze)` (real timing) on slow queries.

| Red Flag | Meaning | Fix |
|----------|---------|-----|
| `Seq Scan` on large table | No index being used | Add appropriate index |
| `Nested Loop` with high rows | N+1 at SQL level | Use joins or includes |
| High `cost` | Expensive operation | Check indexes, simplify query |
| `Sort` without index | Sorting in memory | Add index on ORDER column |

- Index columns used in WHERE/JOIN/ORDER. Know the variants: single, composite, partial (`where:`), covering (`include:`).
- Composite index order matters — most selective column first; a leading-column prefix is usable, a trailing column alone is not.

---

## 9. Locking

| Type | Mechanism | Use When |
|------|-----------|----------|
| Optimistic | `lock_version` column, raises `StaleObjectError` on conflict | Low contention, user-facing forms |
| Pessimistic | `SELECT ... FOR UPDATE` (`lock`/`with_lock`) | High contention, inventory/money |

- `with_lock { ... }` is shorthand for transaction + row lock + reload.

---

## 10. Scopes and Composition

- Define composable scopes (`published`, `recent`, `by_author`) and chain them.
- A conditional scope still returns a relation when the condition is false, so it stays chainable. A class method with a trailing `if` returns `nil` and breaks the chain — prefer a scope.

---

## 11. Common Anti-Patterns

- **N+1 in serializers** — use a `counter_cache` column, or preload the count via `left_joins` + grouped `select`.
- **Querying inside loops** — preload once (e.g. `group_by(&:user_id)`), then iterate the in-memory hash.
- **Caching a relation instead of data** — call `.to_a` before caching; a cached `Relation` is just a query builder and re-fires on access.

---

## 12. strict_loading (Rails 6.1+)

- Raises on lazy access of an unloaded association — turns silent N+1 into a loud error and forces declaring associations upfront.
- Enable per-query (`.strict_loading`), per-model (`self.strict_loading_by_default = true`), or per-association (`strict_loading: true`).
- Configure env behaviour: default-on in development, `action_on_strict_loading_violation = :log` in production.

---

## 13. PostgreSQL-Specific Queries

- `DISTINCT ON (col)` with matching `order` — latest record per group in one query.
- `INNER JOIN LATERAL (...)` — top N rows per group.

---

## 14. Query Performance Checklist

| Check | How |
|-------|-----|
| N+1 queries? | Enable `strict_loading` or check logs for repeated queries |
| Missing index? | Run `EXPLAIN ANALYZE` on slow queries |
| Loading unnecessary columns? | Use `select` or `pluck` instead of `SELECT *` |
| Loading unnecessary records? | Use `exists?`, `count`, `limit` |
| Updating one by one? | Use `update_all`, `upsert_all` for bulk |
| Query inside a loop? | Preload data before the loop |
| Caching a relation? | Call `.to_a` before caching |
| User input in raw SQL? | Use parameterized queries or hash conditions |
| Large table without batching? | Use `find_each` / `in_batches` |

Tools: `bullet` (N+1 + unused eager loading in dev), `prosopite` (N+1 in any Ruby code), `pg_stat_statements` (slow-query tracking), `rack-mini-profiler` (query count/timing in browser), `explain(:analyze)` (built-in plan analysis).
