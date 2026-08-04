---
description: Stack-agnostic resilience at external boundaries — timeouts, retry+backoff, error classification, circuit breaker, idempotency, bulkhead, degradation, health checks. Loaded on file read (code work).
paths:
  - "**/*"
---

# Resilience (generic)

Patterns for calls that cross a process boundary (network, DB, queue, third-party API). The
stack pack names the concrete client/library; these principles hold regardless.

## Timeouts

- **Every external call has an explicit timeout.** A call without one is an unbounded wait that
  can hang the whole caller.
- Set the budget by criticality: a user-facing critical path fails fast (small timeout, then
  retry/fallback); a background bulk fetch can wait longer.
- A timeout on a whole operation must be shorter than the caller's own deadline — never let an
  inner wait outlive the request that's waiting on it.

## Retry with backoff + jitter

- Retry **only** transient failures, with exponential backoff (`base · 2^attempt`, capped) and
  random jitter so many clients don't retry in lockstep (thundering herd).
- Cap attempts; on the last failure, raise — don't retry forever.
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

- After N consecutive failures to a dependency, **open** the circuit: fail fast for a cooldown
  instead of hammering a service that's down. Probe after the cooldown; close on success.
- Use for a **repeatedly failing dependency** (external API/service down). Don't circuit-break a
  single must-succeed operation — retry that instead.
- Emit the open/recover transitions once (edge-triggered) for alerting, not on every blocked call.

## Idempotency

- Make retried operations safe to repeat: same operation twice = same end state.
- For remote writes, send a **caller-generated idempotency/request key** (deterministic where
  possible) so a retried submit is deduplicated server-side rather than duplicated.
- For local state, prefer upsert/set over blind increment; guard accumulation with a processed-id
  set so a replay doesn't double-count.

```
# DON'T — replay doubles the total          # DO — idempotent on id
total += amount                              if id not in seen: total += amount; seen.add(id)
```

## Bulkhead / isolation

- Isolate independent units so one's failure can't sink the rest: run them concurrently and
  collect per-unit results/exceptions instead of aborting the batch on the first error.
- Bound concurrency to a shared resource (semaphore / pool size) so one caller can't exhaust
  connections or rate limit for everyone.

## Graceful degradation

- When a non-essential dependency fails, fall back to a simpler behavior rather than failing the
  whole request — and log that you degraded.
- Decide fail-open vs fail-closed deliberately: an optional enrichment fails open (proceed
  without it); a safety/authorization check fails closed. State which and why at the boundary.

## Health checks

- Expose a cheap liveness/readiness probe for each critical dependency; check before entering an
  expensive path rather than discovering the outage mid-operation.
- Keep the probe fast and side-effect-free, on its own short timeout.
