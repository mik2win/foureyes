---
paths:
  - "**/*.py"
---

# Data: pandas / numpy / datetime

Applies to code using pandas/numpy and to datetime-heavy code. Correctness footguns and conventions only.

---

## 1. pandas

- **Vectorize.** No `iterrows`/`itertuples`/row-wise `.apply(axis=1)` loops — use column ops, `np.where`, `.groupby().transform(...)`.
- **`.to_numpy(dtype=...)` over `.values`** — explicit dtype, no object-array surprise.
- **`.iloc`** = positional (loops, integer slices); **`.loc`** = label-based (dates, column names).
- Watch **dtype/memory**: `astype("category")` for low-cardinality string columns; downcast wide int/float columns; `del` large intermediates inside long loops.

### Chained assignment (footgun)

Under pandas 3.0 Copy-on-Write (always on; `SettingWithCopyWarning` is gone), chained
assignment **consistently never works** — it raises a `ChainedAssignmentError` warning and the
write is lost. Assign through a single `.loc`/`.at`.

```python
# WRONG — chained indexing, the write never reaches df (ChainedAssignmentError)
df[df["price"] > 100]["flag"] = 1
df["price"][0] = 100

# RIGHT — single indexer
df.loc[df["price"] > 100, "flag"] = 1
df.loc[0, "price"] = 100
df.at[0, "price"] = 100          # fastest for one cell
```

Under CoW every indexing result behaves as an independent copy — defensive `.copy()` calls are
no longer needed. The new footgun is the reverse: editing `sub = df[mask]` silently does **not**
propagate to `df`; write through `df.loc[mask, ...]` when you mean to update the parent.

---

## 2. numpy

- **NaN tests:** `np.isnan(x)` — never `x == np.nan` (always False).
- **Slicing returns a view** (shared memory); mutating it mutates the original. `.copy()` for independence. Fancy indexing (`arr[[1,2,3]]`) returns a copy.
- **Broadcasting (footgun):** mismatched ndim silently expands instead of erroring.

```python
a = np.array([1, 2, 3])        # (3,)
b = np.array([[1], [2], [3]])  # (3, 1)
a + b                          # (3, 3) — almost never intended
a + b.flatten()                # (3,)  — fix: align shapes first
```

- In-place ops keep the original dtype: `int_arr += 0.5` truncates. Use `arr = arr + 0.5` to promote to float.

---

## 3. datetime / timezone

- **Always tz-aware UTC.** Never naive `datetime.now()` — use `datetime.now(UTC)`. Mixing naive and aware raises `TypeError: can't subtract offset-naive and offset-aware datetimes`.
- **Reading from storage:** parse, then attach UTC if the stored value is naive (common: ISO strings stored without offset).

```python
from datetime import UTC, datetime

dt = datetime.fromisoformat(row["ts"])
if dt.tzinfo is None:
    dt = dt.replace(tzinfo=UTC)      # storage convention: naive == UTC
age = datetime.now(UTC) - dt         # both aware → OK
```

- **Both operands must be tz-aware before arithmetic/comparison.** Normalize at boundaries:

```python
def ensure_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
```

- `date` has no timezone — `date.fromisoformat(...)` and `date` arithmetic need no fix.

---

## 4. Cache keys & invalidation

- **Deterministic, explicit separator.** Build `f"{a}|{b}|{c}"` — not dict stringification, and not `_` (ambiguous: `report_2024_v1` could split many ways).
- **Hash complex configs:** `hashlib.sha256(json.dumps(cfg, sort_keys=True).encode())` — `sort_keys` makes it order-independent.
- Hierarchical prefixes (`ns:entity:variant`) enable prefix invalidation. Bound growth with TTL or `@lru_cache(maxsize=N)`; guard async check-and-set with a lock.
- **Pick the invalidation strategy by trigger:**

| Strategy | Trigger | Use case |
|----------|---------|----------|
| TTL | time elapsed | external/API data that goes stale |
| Version bump | config reload, schema change | derived/computed caches |
| Explicit | a known domain event | state the event owner invalidates |
| LRU (`maxsize`) | size limit | bounded memory |
| Version segment in the file name | schema change of a file cache | on-disk caches (old files simply ignored) |

- **Evict by recreation cost, not by size.** Cheap to rebuild (a re-download, seconds of recompute) → evict freely. Expensive or unrecoverable (hours of compute, a source that no longer serves the old window) → no automatic policy at all, only an explicit event. Size says what is *worth* evicting; recreation cost says what is *safe* to evict — an LRU or TTL bounded by size evicts whatever is coldest, and the expensive tier is usually the coldest.
- A TTL switched on over an existing corpus wipes the whole backlog on its first pass — introduce it with a cutoff date, as a brake on growth rather than a one-off reclaim.
- **Always expose `clear_cache()`** so tests and shutdown can reset state.

---

## 5. SQLite (brief)

- **WAL + sane PRAGMAs** for concurrent access: `journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout`. Run `ANALYZE` after bulk inserts.
- **Parameterized SQL only** — never f-string user/dynamic values into SQL.

```python
# NEVER: f"SELECT * FROM t WHERE name = '{user_input}'"
await db.execute("SELECT * FROM t WHERE name = ?", (user_input,))
```

- Explicit columns over `SELECT *` (covering-index friendly); avoid `WHERE func(col) = x` (kills index — use a range); match column types in predicates. Async commit/connection rules: see `python-async-concurrency.md`.
- **No N+1 queries in a loop** — one query with a JOIN / `IN (...)` instead of a per-row lookup.
- **Compound index order matters:** leftmost = most selective. Verify with `EXPLAIN QUERY PLAN` — "SCAN" means a full table scan.
