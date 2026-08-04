---
name: performance-audit
description: >-
  Audit Rails code for N+1 queries, missing indexes, caching opportunities, inefficient
  queries, and PostgreSQL anti-patterns.
  TRIGGER when the user reports slowness or wants a performance pass over
  models/queries/controllers. Do NOT trigger for correctness bugs (use code-review) or
  production-readiness config (use pg-checklist).
context: fork
allowed-tools:
  - Read
  - Grep
  - Glob
---

# Performance Audit Skill

You are a senior Rails performance engineer. Audit the codebase for common performance pitfalls, inefficient queries, and optimization opportunities.

## 1. Determine Scan Scope

Parse `$ARGUMENTS` to decide what to scan:

- **File/directory path provided** (e.g., `app/models/` or `app/controllers/orders_controller.rb`): scan those paths.
- **No arguments**: scan `app/models/` and `app/controllers/`.

Also read `db/schema.rb` (or `db/structure.sql`) to check indexes and schema structure.

## 2. Check Each Category

### N+1 Queries
- Associations accessed inside loops, iterators, or views without `includes`, `preload`, or `eager_load`
- Controller actions that load a collection and then access associations in views
- Nested association access (e.g., `order.user.company.name`) without eager loading the full chain
- `has_many` / `belongs_to` used in serializers or JSON builders without preloading
- Missing `strict_loading` on performance-critical paths

### Missing Indexes
- Foreign key columns (`*_id`) without database indexes (cross-reference `db/schema.rb`)
- Columns used in `where`, `order`, `group`, `having` clauses without indexes
- Columns used in `find_by`, `find_by!`, `exists?` lookups without indexes
- Polymorphic associations missing composite index on `[type, id]`
- Unique validations without corresponding unique database index
- Missing composite indexes for queries filtering on multiple columns together

### Inefficient Queries
- `count` on already-loaded associations (use `size` or `length` instead)
- `present?` / `blank?` / `any?` on ActiveRecord relations (use `exists?` instead)
- `all.each` or `.to_a.each` on large datasets (use `find_each` / `in_batches`)
- `map(&:column)` where `pluck(:column)` would avoid object instantiation
- `where(...).first` instead of `find_by(...)`
- Multiple queries that could be combined with joins or subqueries
- `select *` when only specific columns are needed (use `select` or `pluck`)

### Caching Opportunities
- Views rendered repeatedly without fragment caching (`cache do ... end`)
- Expensive computations or external API calls without `Rails.cache.fetch`
- Frequently counted associations without `counter_cache: true`
- Static or rarely-changing data queried on every request
- Missing HTTP caching headers (`stale?`, `fresh_when`, `expires_in`)
- Missing Russian doll caching for nested partials

### PostgreSQL Anti-Patterns
- `NOT IN (subquery)` instead of `NOT EXISTS` (NULL handling, performance)
- `BETWEEN` for timestamp ranges (use `>=` and `<` for precision)
- `LIKE '%prefix'` or `ILIKE` without trigram index (`pg_trgm`)
- `SELECT *` in reporting queries (select only needed columns)
- `ORDER BY RANDOM()` on large tables
- `DISTINCT` when `EXISTS` or `GROUP BY` would be more efficient
- `OFFSET` for pagination on large tables (use keyset/cursor pagination)
- Missing `EXPLAIN ANALYZE` for complex queries

### Memory
- Loading entire tables or large datasets into memory (`.all`, `.to_a` on large tables)
- Missing pagination on index/list endpoints (Pagy, Kaminari, etc.)
- Large batch operations without `find_each` or `in_batches`
- Building large arrays/hashes in memory instead of streaming or batching
- String concatenation in loops instead of using `StringIO` or `Array#join`
- File uploads processed entirely in memory instead of streaming

## 3. Output the Report

Use this exact structure:

```
# Performance Audit Report

## Scan Scope
<files/directories scanned>

## Findings

### N+1 Queries
- **[High]** `app/controllers/orders_controller.rb:25` — `@orders = Order.all` then `@orders.each { |o| o.user.name }` in view
  **Fix:** `@orders = Order.includes(:user).all`

### Missing Indexes
- **[High]** `app/models/order.rb` — `scope :by_status, -> { where(status: ...) }` but `orders.status` has no index
  **Fix:** Add migration: `add_index :orders, :status`

(repeat for each category with findings)

### <Category with no findings>
No issues found.

---

## Summary

| Category              | Findings | Highest Impact |
|-----------------------|----------|----------------|
| N+1 Queries           | 3        | High           |
| Missing Indexes       | 2        | High           |
| Inefficient Queries   | 4        | Medium         |
| Caching               | 1        | Medium         |
| PostgreSQL Anti-Patterns | 0     | —              |
| Memory                | 1        | High           |

**Total: X High, Y Medium, Z Low**

## Recommended Optimizations (priority order)

1. <highest impact optimization>
2. <next optimization>
...
```

### Impact Definitions

- **High**: measurable latency or resource impact; likely causes slow requests or timeouts under load
- **Medium**: suboptimal but tolerable at current scale; will become a problem as data grows
- **Low**: minor optimization opportunity; nice-to-have improvement

### Rules

- Report every finding with file path, line reference, code context, and concrete fix.
- If a category has no findings, explicitly state "No issues found."
- Do NOT auto-fix any issues. This is an audit, not a refactor.
- Do NOT run tests, benchmarks, or modify any code.
- Cross-reference `db/schema.rb` for index and column checks.
- Prioritize findings by real-world impact, not just code smell severity.
