---
description: Stack-agnostic observability — structured logs, no secrets/PII, correlation IDs, actionable metrics, health signals. Loaded on file read (code work).
paths:
  - "**/*"
---

# Observability (generic)

Language-neutral. Stack packs name the concrete tooling. Goal: a production issue is
diagnosable from the emitted signals alone, without attaching a debugger.

## Structured logs

- One event = one log line, key/value or JSON — not prose a human greps by eye.
- Consistent levels, one meaning each: DEBUG (diagnostics) · INFO (significant expected
  event) · WARN (recoverable / unusual, e.g. retry triggered, fallback used) · ERROR
  (needs attention) · CRITICAL/FATAL (system unusable — reserve it).
- Log the context that makes the line actionable (ids, counts, durations) — not "it failed".
- A log statement is code: nothing in tight loops — log at the boundaries (count before,
  summary after) or sample (every Nth iteration). No formatting work that still runs
  when the level is disabled.
- Log the impure and nothing more: clock reads, generated ids, I/O results, external responses,
  side effects — never the output of a deterministic function whose inputs are already logged.
- Put the call where the intent is captured (the handler that decided), not in the helper that
  computed: one line naming the business event beats three naming its steps.
- A logger is not a dependency of domain logic — wrap the impure boundary instead.
- Rate-limit/dedupe a warning that can repeat (same key within an interval) — a flood of
  one message hides everything else.
- Tune noisy third-party loggers down (WARN) — your signal is your own events.

## No secrets / PII

- Never log tokens, passwords, API keys, full card numbers, or auth headers — and avoid
  emails/names where they aren't needed. Redact at the source, not in a downstream pipeline.
- Treat request/response bodies as tainted: log a shape or an id, not the payload.
- Defers to the secret-handling rules in `rules/_generic/code.md`.

## Correlation / request IDs

- Generate (or accept at the edge) a request/correlation id and propagate it across every
  boundary — services, queues, jobs — so one request is traceable end to end.
- Carry it in the logging context (MDC / contextvars / tagged logger), not threaded by hand
  through every call.

## Error context

- Log the cause with context — message + relevant inputs + stack — never a bare "error
  occurred". Preserve the original cause when wrapping.
- Log-and-rethrow XOR handle; don't both log and swallow. See `rules/_generic/exception-patterns.md`.
- Log a failure once, at the boundary that owns it — not at every frame on the way up.

## Actionable metrics

- Prefer a few meaningful signals over vanity counters: for a request path the RED trio —
  Rate, Errors, Duration; for a resource, USE — Utilization, Saturation, Errors.
- Name metrics consistently (`noun.verb.unit`, e.g. `http.request.duration`) and keep label
  cardinality low — never put ids/emails in tag values.
- A metric exists to drive an alert or a decision. If no one would act on it, don't emit it.

## Health & readiness

- Long-running services expose liveness (am I up) and readiness (can I serve) separately;
  readiness reflects real dependencies (db, queue), not a hardcoded 200.
- A service logs its version and effective config summary at startup, and announces
  shutdown begin/end — restarts and config drift become visible in the logs.
- Jobs / workers report start and success/failure with a count — one that dies silently is
  invisible. Surface failures as ERROR plus a metric, not just a buried log line.
