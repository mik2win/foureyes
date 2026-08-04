---
name: postgres-reference
description: >-
  Worked SQL/DDL examples for PostgreSQL conventions — data types, indexing (B-tree/GIN/
  GiST/BRIN), constraints, queries, EXPLAIN, JSON/arrays, and Rails-specific patterns.
  CONSULT when writing migrations, schema, or SQL and you need the idiomatic example or an
  index/constraint pattern. Reference loaded on demand — the always-apply rules live in the
  `postgresql-universal` and `postgresql-rails` rules.
allowed-tools:
  - Read
  - Grep
  - Glob
---

# PostgreSQL — worked examples

Companion to the `postgresql-universal` and `postgresql-rails` rules. Read the reference file
(in this skill's folder) for what you need:

- **Universal** — types, indexes, constraints, queries, EXPLAIN, JSON/arrays → `references/universal.md`
- **Rails-specific** — migrations, schema, ActiveRecord ↔ Postgres patterns → `references/rails.md`
