---
paths:
  - "**/*.rb"
---

# Rails Observability

Observability wiring for a Rails app. The cross-stack discipline (structured logs, no
secrets/PII, correlation ids, actionable metrics, health) is in
`rules/_generic/observability.md`; this is the Rails-specific glue.

- **Request logs:** use **lograge** for one structured event per request (controller, action,
  status, duration). Emit app events as `key=value`, not prose:
  `Rails.logger.info("order.created order_id=#{o.id} total=#{o.total}")`. On Rails 8.1+
  prefer the structured event reporter: `Rails.event.notify("order.created", order_id: o.id)`.
- **Correlation:** `config.log_tags = [:request_id]`; tag service blocks with
  `Rails.logger.tagged("Billing") { ... }`; propagate the request id into jobs you enqueue.
- **Errors:** report through the **Rails error reporter** (`Rails.error.report` /
  `Rails.error.handle`) — one subscription point a backend (Sentry / Honeybadger) hooks at
  boot, not vendor SDK calls scattered through the code. Jobs/rake tasks report failures,
  never rescue-and-continue silently.
- **Secrets/PII:** keep `config.filter_parameters` covering passwords/tokens/PII so request
  logs are redacted at the source.
- **Health:** a readiness endpoint checks real dependencies (DB, cache, queue), distinct from a
  liveness ping. Metrics (Yabeda / StatsD / OTEL): a few RED/USE signals, low-cardinality tags.
