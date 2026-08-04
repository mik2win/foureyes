---
paths:
  - "**/*.py"
---

# Async & Concurrency

asyncio (I/O-bound), process pools (CPU-bound), resilience at external boundaries. Two models — never mix within one module.

---

## 1. asyncio Core Rules

- **`asyncio.TaskGroup` (3.11+) for structured concurrency** — if one task raises, siblings are cancelled and errors surface as an `ExceptionGroup`. Default for new fan-out code.
- **`asyncio.timeout()` (3.11+) around every external call.** Network calls without a timeout are unbounded waits.
- **Never block the loop:** no `time.sleep`, no sync file/network/`requests` calls, no CPU crunching inside a coroutine. Use `await asyncio.sleep()`, and `await asyncio.to_thread(fn, ...)` to offload blocking sync work.
- **`asyncio.Lock`/`Semaphore` for coroutine coordination — never `threading.Lock`** in a coroutine (blocks the whole loop).
- Use `async with` for any connection/session/pool so cleanup runs even on cancellation.
- **One sync→async bridge:** `asyncio.run()` only at the entry point — never inside library or domain code.

### TaskGroup vs gather

| Need | Use |
|------|-----|
| Fail-fast: one failure aborts the rest | `TaskGroup` |
| Fault isolation: one failure must not stop siblings | `gather(*tasks, return_exceptions=True)` then inspect results |
| Fire independent awaitables, collect ordered results, fail-fast | `gather(*tasks)` (no `return_exceptions`) |

With `return_exceptions=True`, exceptions become return *values* — you MUST check `isinstance(r, Exception)`; nothing is raised for you.

---

## 2. Cancellation Must Propagate (footgun)

`CancelledError` is how tasks are stopped. Swallow it and the task becomes un-cancellable (zombie). It inherits from `BaseException` (3.8+), so a plain `except Exception` won't catch it — but a bare `except:` will.

```python
# WRONG — bare except (or older catch-all) swallows cancellation; task never dies
async def worker():
    while True:
        try:
            await do_cycle()
        except:           # also catches CancelledError, KeyboardInterrupt
            continue      # immortal coroutine

# RIGHT — re-raise after any cleanup; put it BEFORE except Exception
async def worker():
    while True:
        try:
            await do_cycle()
        except asyncio.CancelledError:
            await save_state()   # graceful cleanup allowed
            raise                # MUST re-raise so the task actually cancels
        except Exception:
            logger.error("cycle failed", exc_info=True)
            await asyncio.sleep(backoff)
```

Rule: an explicit `except asyncio.CancelledError: raise` always comes before any broad `except Exception`.

---

## 3. Async DB Commit (footgun)

aiosqlite (and many async DB drivers) do **not** auto-commit on context-manager exit. Forgetting the commit is silent data loss — the transaction rolls back.

```python
async with aiosqlite.connect(path) as db:
    await db.execute("INSERT INTO t VALUES (?)", (val,))
    await db.commit()        # REQUIRED — without it the write is discarded
```

- Use the connection as a context manager (avoids leaked connections / `ResourceWarning`).
- Iterate cursors with `async with db.execute(...) as cur:`.
- Batch writes with `executemany()`, not a per-row loop. See `python-data.md` for SQL safety + WAL.

---

## 4. Process Pools (CPU-bound)

Use `ProcessPoolExecutor` for CPU-bound parallelism (`asyncio` gives you nothing for CPU work — it's single-threaded).

- **Worker functions must be top-level and picklable.** Closures, lambdas, and nested functions can't be pickled. (footgun below)
- **Always use the context manager** so the pool is shut down.
- **Pass simple, serializable args.** Large DataFrames are copied per worker (slow) — prefer a path/handle the worker loads itself.
- **No nested parallelism.** A pool inside another pool (or inside async tasks) risks deadlock / core oversubscription — force inner work to a single worker.

```python
# WRONG — nested function captures locals, cannot be pickled
def run(items):
    def worker(x):              # PicklingError at submit time
        return heavy(x)
    with ProcessPoolExecutor() as pool:
        return list(pool.map(worker, items))

# RIGHT — top-level worker
def _worker(x):                 # module-level, picklable
    return heavy(x)

def run(items):
    with ProcessPoolExecutor(max_workers=n) as pool:
        return list(pool.map(_worker, items))
```

`as_completed()` for progress as results finish; `map()` when output order must match input.

| Model | For | Notes |
|-------|-----|-------|
| `asyncio` | I/O-bound | one thread; never CPU-crunch in a coroutine |
| `ProcessPoolExecutor` | CPU-bound | true parallelism; pickling required |
| `to_thread` / `ThreadPoolExecutor` | blocking sync I/O from async | bridges into the loop without blocking it |

### Free-threading (experimental in 3.13; officially supported in 3.14, PEP 779)

- **CPU-bound + threads:** the free-threaded build lets threads run in parallel — benchmark it against `ProcessPoolExecutor` (no pickling/IPC cost, shared memory). Official 3.14 installers ship free-threaded binaries; toggle at runtime with `PYTHON_GIL=0/1` or `-X gil`. The default build still has the GIL.
- **I/O-bound + asyncio:** no benefit — the GIL was never your bottleneck. Don't switch.
- **Caveat:** a C extension without free-threading support re-enables the GIL process-wide; verify your hot-path deps before relying on it.
- **3.14+ third CPU-bound option:** `concurrent.futures.InterpreterPoolExecutor` (PEP 734 subinterpreters) — same-process parallelism without child processes; object sharing is limited and extension support still immature, so benchmark against `ProcessPoolExecutor`.

---

## 5. Resilience at Boundaries

- **Timeout every external call** (see §1). Pick values by criticality — fail fast on the critical path, be lenient for large background payloads.
- **Poll at the data's cadence** — derive the interval from how often the source actually changes; don't hammer a slow-moving source with an aggressive fixed interval.
- **Retry transient failures only**, with exponential backoff + jitter and a delay cap. Reset the failure counter on success.

```python
delay = min(base_delay * 2 ** attempt, max_delay)
await asyncio.sleep(delay + random.uniform(0, delay * 0.1))  # jitter avoids thundering herd
```

| Error class | Retry? | Examples |
|-------------|--------|----------|
| Transient | yes | timeout, rate limit, 503, "server busy" |
| Permanent | no | invalid params, auth failed, 400 |
| Unknown | once | unexpected errors |

- **Idempotency:** retried operations must not double-apply. Use a client-generated request/operation ID and guard side-effecting state with a processed-set / dedup key (`if id in seen: return`). Never `total += x` blindly on retry.
- **Circuit breaker:** stop calling a service after N consecutive failures; half-open after a reset timeout to probe recovery. Use for a repeatedly failing dependency — *not* for a single must-succeed operation (retry that instead).
- **Bulkhead:** cap concurrent calls with a `Semaphore`; isolate independent workers (one failure shouldn't sink the rest — see `gather(return_exceptions=True)`).
- **Graceful degradation:** on dependency failure, fall back to a simpler path (cached/rule-based/minimal-safety) rather than crashing.

---

## 6. Graceful Shutdown

On SIGTERM/SIGINT, signal an `asyncio.Event`, cancel tasks, then `await gather(*tasks, return_exceptions=True)` so each task's `CancelledError` handler can persist state before exit. Don't hard-kill mid-write.

---

## 7. Long-Running Loop Safety

A `while running: ... await asyncio.sleep(interval)` loop assumes the sleep actually pauses it. When it doesn't — a misconfigured zero/None interval, or a **mocked `asyncio.sleep` in tests** — the loop spins at CPU speed, allocating on every pass until OOM. `asyncio.sleep(0)` is *not* a safeguard; it's mocked away too.

- **Guard the loop with an elapsed-time check**, not just the sleep. Track `time.monotonic()` across iterations and bail out (or skip the body) after N consecutive passes that elapse in under a threshold — a real sleep can't return that fast, so sub-threshold means the sleep isn't sleeping.
- Extract the counter into one reusable guard rather than hand-rolling it per loop.

```python
import time

async def run_loop(interval: float, is_running) -> None:
    tight = 0
    last = time.monotonic()
    while is_running():
        await asyncio.sleep(interval)
        now = time.monotonic()
        if now - last < 1.0:                 # sleep returned implausibly fast
            tight += 1
            if tight > 100:
                logger.error("sleep not sleeping (mocked?) — exiting loop")
                return                        # don't spin forever
            last = now
            continue                          # skip the body this pass
        tight, last = 0, now                  # real elapsed time — reset
        ...                                   # actual work
```

The same hazard surfaces in tests as a hung/OOM-killed worker — see `python-testing.md` §7 for the test-side defenses (timeout marker, termination condition on the mocked sleep).
