# PostgreSQL (universal) — worked examples

Companion reference to the `postgresql-universal` rule; loaded on demand.

---

## 1. Data Types — Choose Correctly

```sql
id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

---

## 2. Index Types

### B-tree (default)

```sql
CREATE INDEX idx_orders_user_date ON orders (user_id, created_at DESC);
-- Used:     WHERE user_id=1; WHERE user_id=1 AND created_at>...; WHERE user_id=1 ORDER BY created_at DESC
-- NOT used: WHERE created_at>...  (leftmost column absent)

-- Covering index → index-only scan (PG 11+) only for pages the visibility map marks all-visible; check Heap Fetches
CREATE INDEX idx_orders_covering ON orders (user_id) INCLUDE (status, total);
```

### GIN — multi-value types (arrays, JSONB, full-text `tsvector`)

```sql
CREATE INDEX idx_products_metadata ON products USING GIN (metadata);
-- Supports @> '{"color":"red"}', ? 'color', ?| ARRAY['color','size']

CREATE INDEX ... USING GIN (metadata jsonb_path_ops);  -- smaller; only @> (no key-existence ?)
CREATE INDEX idx_articles_tags ON articles USING GIN (tags);          -- @>, &&
CREATE INDEX idx_articles_search ON articles USING GIN (search_vector); -- @@
```

### GiST — ranges, geometry, full-text with ranking

```sql
CREATE INDEX idx_bookings_dates ON bookings USING GIST (dates);        -- && range overlap
CREATE INDEX idx_locations_coords ON locations USING GIST (coordinates); -- <@ containment
CREATE INDEX idx_articles_search_gist ON articles USING GIST (search_vector); -- supports ts_rank ordering
```

### BRIN — very large, naturally ordered tables

```sql
CREATE INDEX idx_events_created_brin ON events USING BRIN (created_at);
-- Gate first: SELECT correlation, n_distinct FROM pg_stats WHERE tablename='events' AND attname='created_at';  -- both must hold
-- pages_per_range (default 128): measure how many pages one query's range spans; mutated table → USING BRIN (created_at timestamptz_minmax_multi_ops)
```

### Partial & Expression Indexes

```sql
-- Partial: index only relevant rows (smaller, faster) — e.g. soft-delete / active subset
CREATE INDEX idx_users_active ON users (email) WHERE deleted_at IS NULL;

-- Expression: case-insensitive search + uniqueness
CREATE UNIQUE INDEX idx_users_email_lower ON users (LOWER(email));
-- Expression: date truncation
CREATE INDEX idx_orders_month ON orders (DATE_TRUNC('month', created_at));
```

### Index Maintenance

```sql
-- Unused indexes (idx_scan = 0)
SELECT relname AS table, indexrelname AS index, idx_scan,
       pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexrelname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;

REINDEX INDEX CONCURRENTLY idx_orders_status;  -- non-locking rebuild (PG 12+)
REINDEX TABLE CONCURRENTLY orders;
```

---

## 4. Window Functions

```sql
-- Top N per group (most common pattern)
SELECT * FROM (
  SELECT orders.*, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY total DESC) AS rn
  FROM orders
) ranked WHERE rn <= 3;
```

### Frame Clauses

```sql
-- Moving average over last 7 rows
AVG(daily_revenue) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
```

---

## 5. CTEs & Recursive Queries

### WITH RECURSIVE

```sql
WITH RECURSIVE org_tree AS (
  SELECT id, name, manager_id, 1 AS depth, ARRAY[id] AS path
  FROM employees WHERE manager_id IS NULL
  UNION ALL
  SELECT e.id, e.name, e.manager_id, ot.depth + 1, ot.path || e.id
  FROM employees e JOIN org_tree ot ON e.manager_id = ot.id
)
SELECT * FROM org_tree ORDER BY path;
```

### Writeable CTEs

```sql
-- Chain DML: insert returning, feed another insert
WITH new_user AS (
  INSERT INTO users (email) VALUES ('alice@example.com') RETURNING id
)
INSERT INTO user_settings (user_id, theme) SELECT id, 'default' FROM new_user;

-- Archive + delete atomically
WITH archived AS (
  DELETE FROM orders WHERE status='cancelled' AND created_at < NOW()-INTERVAL '1 year' RETURNING *
)
INSERT INTO orders_archive SELECT * FROM archived;
```

---

## 6. Transaction Isolation

```sql
-- SERIALIZABLE (SSI) detects read/write dependency cycles with predicate locks, and the PLAN sets their granularity:
-- Seq Scan          → predicate lock on the WHOLE table: every concurrent writer conflicts, even on rows the filter rejects
-- B-tree Index Scan → the tuples read plus the leaf pages visited (the read range, not only the values seen)
-- SP-GiST / BRIN    → the entire index; escalation: max_pred_locks_per_page → page lock, max_pred_locks_per_relation → relation lock
BEGIN ISOLATION LEVEL SERIALIZABLE READ ONLY DEFERRABLE;  -- reports: waits for a safe snapshot, then takes no predicate locks and never aborts
```

- `could not serialize access` rising after a release → `EXPLAIN (ANALYZE, BUFFERS)` the reads of the aborting transaction first; a Seq Scan means a dropped or unused index is the suspect before load growth. A READ COMMITTED transaction takes no predicate locks, so SERIALIZABLE peers cannot see a cycle through it — the guarantee degrades silently (rule §6).
- Row locks never escalate: the number of locked rows is not a cost. `FOR SHARE` from application code is — compatible modes skip the queue and starve a waiting `UPDATE` (rule §6).

---
## 7. VACUUM & Maintenance

### Autovacuum Tuning

```sql
ALTER TABLE events SET (
  autovacuum_vacuum_scale_factor = 0.01,   -- 1% instead of 20%
  autovacuum_vacuum_threshold = 1000,
  autovacuum_analyze_scale_factor = 0.005
);
-- High-write: scale_factor=0 + fixed threshold, autovacuum_vacuum_cost_delay=2 (default 2ms PG12+)
```

```sql
-- Autovacuum / dead-tuple status
SELECT relname, n_dead_tup, n_live_tup,
       ROUND(100.0*n_dead_tup/NULLIF(n_live_tup,0),1) AS dead_pct,
       last_vacuum, last_autovacuum, last_analyze
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 20;
```

---

## 8. Connection Management

```sql
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
SET idle_in_transaction_session_timeout = '30s';  -- prevent connection leak

-- Kill long idle-in-transaction connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE state = 'idle in transaction' AND state_change < NOW() - INTERVAL '5 minutes';
```

---

## 9. Security

### Authentication (pg_hba.conf — most specific rules first)

```
# TYPE  DATABASE  USER       ADDRESS       METHOD
local   all       postgres                 peer            # OS user = PG user
host    myapp     app_user   10.0.0.0/8    scram-sha-256
host    all       all        0.0.0.0/0     reject          # deny everything else
```

### Role-Based Access Control

```sql
CREATE ROLE app_user LOGIN PASSWORD '...';
GRANT CONNECT ON DATABASE myapp TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
-- Read-only reporting role: GRANT SELECT only (+ default privileges).
```

### Row-Level Security (multi-tenant)

```sql
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders FORCE ROW LEVEL SECURITY;  -- applies even to table owner
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.current_tenant_id')::BIGINT);
SET app.current_tenant_id = '42';  -- set before queries
```

---

## 10. Backup & Recovery

### Logical (pg_dump)

```bash
pg_dump -Fd -j 4 -f mydb.dir mydb           # directory format: the only one that supports parallel -j
pg_dump -Fc -f mydb.dump mydb               # custom format: compressed, selective (no parallel)
pg_restore -j 4 -d mydb_restored mydb.dump  # parallel restore
pg_dump -Fc -t users -t orders -f part.dump mydb   # specific tables
pg_dump -Fc --schema-only -f schema.dump mydb
pg_dumpall -f cluster.sql                    # cluster-wide: roles, tablespaces
```

### Physical (pg_basebackup) — required for PITR

```bash
pg_basebackup -D /backup/base -Ft -z -P
pg_basebackup --incremental=/backup/base/backup_manifest -D /backup/incr -Ft -z  # PG 17+
```

### WAL Archiving & PITR

```ini
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'pgbackrest --stanza=mydb archive-push %p'   # or: cp %p /archive/%f
```

---

## 11. Monitoring & Observability

### pg_stat_statements

```sql
-- Slowest by mean time (use ORDER BY total_exec_time for most time-consuming overall)
SELECT LEFT(query,80) AS query, calls,
       ROUND(mean_exec_time::NUMERIC,2) AS avg_ms,
       ROUND(total_exec_time::NUMERIC,2) AS total_ms, rows
FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
SELECT pg_stat_statements_reset();
```

### pg_stat_activity

```sql
-- Currently running queries
SELECT pid, usename, state, NOW()-query_start AS duration, LEFT(query,100)
FROM pg_stat_activity WHERE state='active' AND pid != pg_backend_pid()
ORDER BY duration DESC;

-- Blocked queries (waiting on locks)
SELECT blocked.pid AS blocked_pid, blocked.query AS blocked_query,
       blocking.pid AS blocking_pid, blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_locks bl ON bl.pid=blocked.pid AND NOT bl.granted
JOIN pg_locks gl ON gl.locktype=bl.locktype
  AND gl.database IS NOT DISTINCT FROM bl.database
  AND gl.relation IS NOT DISTINCT FROM bl.relation
  AND gl.page IS NOT DISTINCT FROM bl.page
  AND gl.tuple IS NOT DISTINCT FROM bl.tuple
  AND gl.pid != bl.pid AND gl.granted
JOIN pg_stat_activity blocking ON blocking.pid=gl.pid;
```

### Table & Index Health

```sql
-- Tables with many seq scans (missing indexes?)
SELECT relname, seq_scan, idx_scan,
       ROUND(100.0*seq_scan/NULLIF(seq_scan+idx_scan,0),1) AS seq_pct, n_live_tup
FROM pg_stat_user_tables WHERE seq_scan>100 AND n_live_tup>10000 ORDER BY seq_scan DESC;

-- Unused indexes (skip _pkey / _unique)
SELECT relname AS table, indexrelname AS index, idx_scan,
       pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan=0 AND indexrelname NOT LIKE '%_pkey' AND indexrelname NOT LIKE '%_unique'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Log Configuration

```ini
log_min_duration_statement = 500    # log queries > 500ms
log_statement = 'ddl'
log_line_prefix = '%t [%p] %u@%d '
log_checkpoints = on
log_lock_waits = on
log_temp_files = 0                   # log all temp file usage
log_autovacuum_min_duration = 0

# auto_explain — automatic plan logging for slow queries
shared_preload_libraries = 'auto_explain, pg_stat_statements'
auto_explain.log_min_duration = '1s'
auto_explain.log_analyze = on
```

---

## 12. Replication

### Streaming (Physical)

```ini
# Primary postgresql.conf
wal_level = replica
max_wal_senders = 3
wal_keep_size = 1GB            # or use archive_command
# pg_hba.conf: host replication repl_user 10.0.0.0/8 scram-sha-256
```

```bash
pg_basebackup -h primary -D /data/standby -U repl_user -P -R  # -R writes standby.signal + primary_conninfo
```

### Logical (PG 10+)

```sql
CREATE PUBLICATION my_pub FOR TABLE users, orders;   -- or FOR ALL TABLES
CREATE SUBSCRIPTION my_sub
  CONNECTION 'host=primary dbname=mydb user=repl_user' PUBLICATION my_pub;
```

### Lag Monitoring & Failover

```sql
-- On primary
SELECT client_addr, state,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS replay_lag_bytes, reply_time
FROM pg_stat_replication;
-- On standby
SELECT EXTRACT(EPOCH FROM (NOW()-pg_last_xact_replay_timestamp())) AS lag_seconds;

SELECT pg_promote();  -- promote standby (PG 12+)
```

---

## 13. Schema Design Principles

### Constraints-First Design

```sql
CREATE TABLE orders (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  status TEXT NOT NULL DEFAULT 'pending',
  total_cents INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_orders_status CHECK (status IN ('pending','paid','shipped','cancelled')),
  CONSTRAINT chk_orders_total_positive CHECK (total_cents >= 0)
);
-- Truth as a plain view first, then the cache: drift is one EXCEPT away, and the cache is disabled by swapping a name
CREATE VIEW v_daily_totals AS SELECT ...;
CREATE MATERIALIZED VIEW mv_daily_totals AS SELECT * FROM v_daily_totals;
-- drift check: (SELECT * FROM v_daily_totals EXCEPT ALL SELECT * FROM mv_daily_totals) and the reverse both empty, COUNT(*) equal
```

---

## 14. Modern PostgreSQL (15/16/17/18) Features

### MERGE (PG 15+)

```sql
MERGE INTO product_inventory AS t USING incoming_shipment AS s ON t.product_id=s.product_id
WHEN MATCHED THEN UPDATE SET quantity = t.quantity + s.quantity, updated_at = NOW()
WHEN NOT MATCHED THEN INSERT (product_id, quantity, updated_at) VALUES (s.product_id, s.quantity, NOW());
```

### SQL/JSON Standard

```sql
SELECT jt.* FROM orders, JSON_TABLE(items, '$[*]' COLUMNS (
  product_id INTEGER PATH '$.product_id',
  quantity   INTEGER PATH '$.quantity',
  price      NUMERIC PATH '$.price')) AS jt;
```

### Generated Columns

```sql
full_name TEXT GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED
```
