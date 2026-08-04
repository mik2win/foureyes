---
paths:
  - "**/*.rb"
---

# Ruby / Rails Observability

Observability wiring for Ruby services and Rails apps. Logger mechanics and structured-message
form live in the `ruby-idioms` skill (§Structured logging → `references/logging.md`) and
`rails-security.md` (tagged
logging, levels, no SQL noise);
the cross-stack discipline is in `rules/_generic/observability.md`. This adds the Rails glue.

---

## 1. Request logging

- Use **lograge** to collapse Rails' multi-line request logs into one structured event per
  request (controller, action, status, duration, params digest). Raw multi-line logs are
  unsearchable once aggregated.
- Emit app events as `key=value` so they parse:
  `Rails.logger.info("order.created order_id=#{o.id} user_id=#{u.id} total=#{o.total}")` —
  not a prose sentence. On Rails 8.1+ prefer the structured event reporter:
  `Rails.event.notify("order.created", order_id: o.id)`.

## 2. Tagged / correlation context

- `config.log_tags = [:request_id, :remote_ip]` so every line is attributable; tag service
  blocks with `Rails.logger.tagged("PaymentService") { ... }`.
- Propagate the request id into background jobs (pass it in the args or via `Current`
  attributes) so async work stays correlated with the request that enqueued it.

## 3. Error reporting

- Report handled-but-notable errors through the **Rails error reporter** —
  `Rails.error.report(e, handled: true, context: {...})` / `Rails.error.handle { ... }` — the
  single integration point a backend (Sentry / Honeybadger / etc.) subscribes to at boot.
  Don't scatter vendor SDK calls through the code.
- Background jobs and rake tasks must report failures (reporter + re-raise / non-zero exit),
  never rescue-and-continue silently.

## 4. Secrets / PII

- Keep `config.filter_parameters` covering passwords, tokens, secrets, and card/PII fields — it
  redacts request logs at the source. Never interpolate a raw credential into a log message.

## 5. Health & metrics

- Expose a readiness endpoint that checks real dependencies (DB, cache, queue), distinct from a
  liveness ping. If exporting metrics (Yabeda / StatsD / OTEL), keep a few RED/USE signals with
  low-cardinality tags — no record ids in tag values.
