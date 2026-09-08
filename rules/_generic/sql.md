---
description: Engine-independent SQL and schema rules — index ownership and write tax, reading a plan (access vs filter predicates), predicates that hide an index, the optional-filter anti-pattern, keyset pagination, query loops as a correctness bug, read-check-then-write races, natural keys, schemaless columns. The stack pack carries the engine's specifics. Narrow `paths:` to this project's DB directories at /bootstrap.
paths:
  - "**/*.sql"
  - "**/migrations/**"      # Django, Alembic, SQLAlchemy, Laravel database/migrations
  - "**/migrate/**"         # Rails db/migrate
  - "**/db/**"              # Rails db/; Laravel database/ is the next line
  - "**/database/**"        # Laravel database/{migrations,seeders,factories}
  - "**/alembic/**"
  - "**/schema.rb"
  - "**/structure.sql"
  - "**/models/**"          # ORM models: Django models.py, Rails app/models, SQLAlchemy
  - "**/models.py"
  - "**/repositor*/**"
  - "**/queries/**"
---

# SQL (generic)

- **An index is owned by a query and taxes every write.** PK/UNIQUE indexes are the model; any
  other index exists for a named query. A plan that adds or reshapes a query names its index —
  or why none — and the latency budget the write cost buys; extend an existing index first.
- **"The index is used" proves nothing.** Per WHERE condition: access (narrows the scanned
  range) or filter (checked on entries already reached)? Only access scales, and the plan node
  hides it — walk the index columns against the DDL: equalities, one inequality, then filters.
- **A function, cast or arithmetic on the column hides its index.** Convert the search term,
  never the column; watch implicit casts and ORM-injected `lower()` — or index the expression.
- **`(col = :p OR :p IS NULL)` forces a full scan** — the plan must fit the case where every
  filter is off. Build WHERE from the conditions actually supplied, keeping bind parameters.
- **Paginate by keyset, never OFFSET**: filter on the last row's key with a row comparison,
  `(sort_col, id) < (?, ?)`; the ORDER BY ends in a unique column and the index matches it.
- **A loop of queries is a correctness bug before a performance bug**: each query sees its own
  snapshot, so concurrent writes make the loop silently wrong. One query, or one transaction.
- **Read-check-then-write is a race, not a check.** Snapshot isolation does not detect write
  skew: two transactions pass the same check and both write. Name the fix — UNIQUE/exclusion
  constraint, SERIALIZABLE + retry, or `FOR UPDATE`; an absence invariant cannot be row-locked.
- **A generated primary key guards nothing**: name the natural key and enforce it (NOT NULL +
  UNIQUE) or say why duplicates are fine. DEFAULT is not a constraint; no EAV tables.
- **A schemaless column moves the schema into code.** Point at the one module that owns the
  parse, CHECK the invariants that matter, name the migration: dual-read or a version field.
