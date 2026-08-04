# PostgreSQL — Claude Instructions

## Behaviour Rules

### Think, Then Propose
Before implementing, briefly describe what you're going to do and why. One short paragraph is enough. Start coding only after.

### Simplicity First
Small team (1-3 developers). Always choose the simpler approach. Readable SQL beats clever SQL. YAGNI — don't build for hypothetical futures.

---

## Critical Conventions

- **Data types:** TEXT not VARCHAR, TIMESTAMPTZ not TIMESTAMP, NUMERIC not FLOAT for money, IDENTITY not SERIAL
- **Indexes:** B-tree (default), GIN (arrays/JSONB/FTS), GiST (ranges/geometry), BRIN (large ordered tables)
- **EXPLAIN:** Always `EXPLAIN (ANALYZE, BUFFERS)` before optimizing
- **Transactions:** READ COMMITTED default. SERIALIZABLE with retry logic.
- **Security:** scram-sha-256 auth, minimal role privileges, RLS for multi-tenant, SSL in production

---

## Rules (auto-loaded by file path)

Rules are loaded automatically when you work with matching files.

| When you edit... | Rules loaded |
|---|---|
| `db/migrate/`, `db/schema.rb`, `*.sql` | postgresql-universal |
| `db/migrate/`, `config/database.yml`, `app/models/` | postgresql-rails |

---

## Available Skills

| Skill | Description |
|---|---|
| `/pg-checklist` | PostgreSQL production checklist |
| `/postgres-reference` | On-demand worked SQL/DDL examples for postgresql-universal + postgresql-rails |

> The `postgresql-universal` / `postgresql-rails` rules are the lean always-apply versions;
> their worked examples live in the `postgres-reference` skill (loaded on demand).

---

## Prohibited Actions

- Do NOT run migrations automatically — show the file, let the developer run it
- Do NOT execute destructive SQL (DROP, TRUNCATE, DELETE without WHERE) without confirmation
- Do NOT commit database credentials or connection strings to version control
- Do NOT modify production database configuration without asking first
