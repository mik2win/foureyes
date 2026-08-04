---
name: pg-checklist
description: >-
  Run a PostgreSQL production-readiness checklist against the current schema, database
  config, and connection settings, reporting pass/fail with remediation.
  TRIGGER when the user wants to vet Postgres for production, audit
  schema/indexes/constraints/connection-pool/backup settings, or asks "is the database
  production-ready". Do NOT trigger for general code review (use code-review) or
  query-level tuning (use performance-audit).
context: fork
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# PostgreSQL Production Checklist Skill

You are a senior database engineer specializing in PostgreSQL and Rails. Run a comprehensive production readiness checklist against the project's schema, configuration, and connection settings.

## 1. Gather Project Context

Read the following files (skip any that do not exist):

- `db/schema.rb` or `db/structure.sql` — schema definitions
- `config/database.yml` — database configuration
- `config/puma.rb` — thread/worker configuration (for pool sizing)
- `config/initializers/` — any database-related initializers
- `Gemfile` — database-related gems (pg, pgbouncer, pg_search, etc.)
- `db/migrate/` — recent migration files

## 2. Run the Checklist

Evaluate each item below and mark as **Pass**, **Fail**, or **N/A**.

### Schema Design
- [ ] All foreign keys have corresponding database indexes
- [ ] `bigint` (IDENTITY/BIGSERIAL) used over `integer` (SERIAL) for primary keys
- [ ] `text` used instead of `varchar(n)` (PostgreSQL treats them identically; `text` avoids arbitrary limits)
- [ ] `timestamptz` used instead of `timestamp` (Rails `datetime` maps to `timestamp without time zone` by default)
- [ ] `citext` used for case-insensitive text fields (emails, usernames) instead of `lower()` indexes
- [ ] UUID primary keys where appropriate (distributed systems, public-facing IDs)
- [ ] No unnecessary `null: true` on columns that should always have values

### Indexes
- [ ] Every foreign key column is indexed
- [ ] Columns used in `WHERE`, `ORDER BY`, and `GROUP BY` are indexed
- [ ] Polymorphic associations have composite index on `[type, id]`
- [ ] Unique validations backed by unique database indexes
- [ ] No redundant indexes (e.g., index on `[a]` when `[a, b]` composite index exists)
- [ ] Partial indexes used where applicable (e.g., `where: "deleted_at IS NULL"`)
- [ ] GIN/GiST indexes for JSONB, array, or full-text search columns

### Constraints
- [ ] `NOT NULL` constraints on all required columns
- [ ] `CHECK` constraints for enum-like values (or PostgreSQL enums)
- [ ] Unique constraints where business rules require uniqueness
- [ ] Foreign key constraints defined at database level (not just Rails associations)
- [ ] `DEFAULT` values set for columns that have sensible defaults

### Connection Pool
- [ ] Pool size in `database.yml` matches Puma thread count (`threads * workers`)
- [ ] PgBouncer configured for production (or justified reason for direct connections)
- [ ] `prepared_statements: false` set when using PgBouncer in transaction mode
- [ ] Connection timeout configured (`connect_timeout`, `statement_timeout`)
- [ ] `idle_timeout` and `reaping_frequency` set for connection cleanup
- [ ] Advisory lock configuration for Solid Queue / GoodJob if applicable

### Migrations
- [ ] All migrations are reversible (`change` method or `up`/`down` pair)
- [ ] No data manipulation in schema migrations (use data migrations or rake tasks)
- [ ] `add_index` uses `algorithm: :concurrently` for large tables (with `disable_ddl_transaction!`)
- [ ] `add_column` with `default` uses database-level default (Rails 5+) instead of backfill
- [ ] `remove_column` preceded by `ignored_columns` in the model
- [ ] `add_reference` includes `index: true` (or `index: { algorithm: :concurrently }`)
- [ ] Strong migrations gem (`strong_migrations`) installed and configured

### Monitoring
- [ ] `pg_stat_statements` extension enabled for query analysis
- [ ] `query_log_tags` configured (Rails 7+) to tag queries with controller/action
- [ ] `auto_explain` configured for slow queries (threshold set appropriately)
- [ ] Database metrics exported (connections, cache hit ratio, table bloat, replication lag)
- [ ] Slow query logging enabled (`log_min_duration_statement`)
- [ ] Lock monitoring in place for deadlock detection

### Backup & Recovery
- [ ] WAL archiving configured for continuous backup
- [ ] Point-in-Time Recovery (PITR) tested and documented
- [ ] Backup restoration tested on a schedule
- [ ] Logical backups (`pg_dump`) for individual table recovery
- [ ] Replication configured (streaming or logical) for HA
- [ ] RTO and RPO defined and validated

### Security
- [ ] `scram-sha-256` authentication (not `md5` or `trust`)
- [ ] SSL/TLS required for all connections (`sslmode=verify-full` or `require`)
- [ ] Minimal role privileges (app user is not superuser; separate migration user)
- [ ] Row-Level Security (RLS) for multi-tenant applications
- [ ] `search_path` set explicitly to prevent schema injection
- [ ] Database user password rotated on a schedule
- [ ] `pg_hba.conf` restricts access by IP/subnet

## 3. Output the Report

Use this exact structure:

```
# PostgreSQL Production Checklist Report

## Environment
- Schema source: `db/schema.rb` | `db/structure.sql`
- Database config: `config/database.yml`
- Pool/threads: <pool size> / <puma threads>

## Checklist Results

| #  | Category        | Item                                      | Status |
|----|-----------------|-------------------------------------------|--------|
| 1  | Schema          | Foreign keys have indexes                 | Pass   |
| 2  | Schema          | IDENTITY over SERIAL                      | Fail   |
| 3  | Schema          | TEXT over VARCHAR                          | Pass   |
| ...| ...             | ...                                       | ...    |

## Failed Items — Remediation

### [Fail] #2 — IDENTITY over SERIAL
**Current:** `id :serial` in multiple tables
**Fix:** For new tables, use `create_table :name, id: :bigint`. For existing tables, this is a major migration — plan carefully.
**Priority:** Low (existing tables), High (new tables)

### [Fail] #N — <item>
**Current:** <what was found>
**Fix:** <specific remediation steps>
**Priority:** Critical / High / Medium / Low

---

## Summary

- **Passed:** X / Y items
- **Failed:** Z items
- **N/A:** W items

## Priority Ranking

1. <most critical fix>
2. <next fix>
...
```

### Rules

- Read actual project files to determine pass/fail; do not guess.
- Mark items as **N/A** when the check does not apply (e.g., RLS for single-tenant apps).
- For items that cannot be verified from code alone (e.g., backup testing), mark as **N/A** with a note.
- Provide specific, actionable remediation for every failed item.
- Do NOT auto-fix any issues. This is a checklist audit, not a migration generator.
- Do NOT run database commands or modify any files.
