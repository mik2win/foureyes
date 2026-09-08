---
description: Stack-agnostic resilience at external boundaries and blocking waits — timeouts, retry+backoff, error classification, circuit breaker, idempotency, bulkhead, back pressure, degradation, health checks. Loaded on file read (code work).
paths:
  - "**/*"
---

# Resilience (generic)

Patterns for calls that cross a process boundary (network, DB, queue, third-party API). The
stack pack names the concrete client/library; these principles hold regardless.

## Timeouts

- **Every blocking wait has an explicit bound** — not only the network hop: pool checkout, lock
  acquire, queue take, `future.get()`, thread join. An unbounded wait can hang the whole caller.
- Set the budget by criticality: a user-facing critical path fails fast (small timeout, then
  retry/fallback); a background bulk fetch can wait longer.
- Budget the chain, not one call: timeout × attempts + backoff, summed over every hop, must fit
  inside the caller's deadline — two waits each under your own timeout are not safe in series.
- **Don't chain blocking calls.** A component already serving a blocking request must not make
  another blocking call outward while handling it — the chain fails together and its latencies
  add. Past one synchronous hop, break the chain with a message or say why the coupled failure
  is acceptable; timeouts and breakers soften this shape, they do not fix it.

## Retry with backoff + jitter

- Retry **only** transient failures, with exponential backoff (`base · 2^attempt`, capped) and
  random jitter so many clients don't retry in lockstep (thundering herd).
- Cap attempts, and fit the whole loop inside the caller's remaining deadline: when it doesn't
  fit, return the failure now rather than hold the connection for a retry no one is waiting for.
- Never retry a non-idempotent operation blind (see Idempotency) — a "timed-out" write may have
  succeeded server-side.

## Error classification

Decide retry vs fail from the error class, not by retrying everything:

| Class | Retry? | Typical |
|---|---|---|
| Transient | yes | timeout, rate limit, 429/503, connection reset |
| Permanent | no | bad request/params, auth failure, 400/404, validation |
| Unknown | once | unexpected — retry a single time, then surface |

- Keep the transient set explicit and small; default unrecognized errors to non-retryable.

## Circuit breaker

- Open on **fault density**, not a consecutive count — a rate over a rolling window or a leaky
  bucket a timer drains: a dependency erroring on 40% of calls never fails N in a row, so a
  consecutive counter never opens. Fail fast for the cooldown, then probe; close on success.
- Keep the counter in-process; don't circuit-break a single must-succeed operation — retry that.
- Emit the open/recover transitions once (edge-triggered) for alerting, not on every blocked call.

## Idempotency

- Make retried operations safe to repeat: same operation twice = same end state.
- For remote writes, send a **caller-generated idempotency/request key** (deterministic where
  possible) so a retried submit is deduplicated server-side rather than duplicated.
- For local state, prefer upsert/set over blind increment; guard accumulation with a processed-id
  set — and bound that set (size cap or TTL), or you have traded a double-count for a leak.
- A retry hours later re-reads state that moved: pass the trigger-time value, don't re-decide.
- Compensation is not a rollback: read `docs/decision-craft.md` §11 before a multi-step flow.

```
# DON'T — replay doubles the total          # DO — idempotent on id, guard bounded
total += amount                              if id not in seen: total += amount; seen.add(id)
```

## Bulkhead / isolation

- Isolate independent units so one's failure can't sink the rest: run them concurrently and
  collect per-unit results/exceptions instead of aborting the batch on the first error.
- Bound concurrency *and* queue depth on a shared resource (semaphore, pool size, `maxsize`) so
  one caller can't exhaust connections or rate limit for everyone. Say what a full queue does —
  block the producer inside your process, refuse at a public entry point — and count the drops.

## Graceful degradation

- When a non-essential dependency fails, fall back to a simpler behavior rather than failing the
  whole request — and log that you degraded.
- Decide fail-open vs fail-closed deliberately: an optional enrichment fails open (proceed
  without it); a safety/authorization check fails closed. State which and why at the boundary.
- A stale cache is a designed degradation: allowed only once you write down which store is the
  source of truth, that the authoritative check still runs against it on the write path, and
  what the user sees when the two disagree.

## Health checks

- Expose a cheap liveness/readiness probe for each critical dependency; check before entering an
  expensive path rather than discovering the outage mid-operation.
- Keep the probe fast and side-effect-free, on its own short timeout.
