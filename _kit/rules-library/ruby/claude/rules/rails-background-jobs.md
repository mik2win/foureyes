---
paths:
  - "app/jobs/**/*.rb"
  - "app/mailers/**/*.rb"
---

# Rails Background Jobs & ActionMailer

Based on Rails Guides (Active Job, Action Mailer), Sidekiq Best Practices, Solid Queue documentation.

> Worked examples live in the `rails-reference` skill (`references/background-jobs.md`).

---

## 1. ActiveJob Interface

- `perform_later` enqueues for async execution (default); `perform_now` runs inline (tests or from another job).
- Configure with `set(...)`: `wait:`, `wait_until:`, `queue:`, priority.

### Queue Naming

| Queue | Purpose | Example Jobs |
|-------|---------|-------------|
| `default` | Standard operations | `OrderProcessingJob` |
| `critical` | Must run immediately | `PasswordResetJob`, `PaymentJob` |
| `mailers` | All email delivery | ActionMailer `deliver_later` |
| `low` | Batch work, cleanup | `CleanupJob`, `ReportGenerationJob` |

### Argument Serialization

- Pass only **primitives** and **GlobalID-capable objects** (ActiveRecord models). Supported: `String`, `Integer`, `Float`, `BigDecimal`, `NilClass`, `TrueClass`, `FalseClass`, `Symbol`, `Date`, `Time`, `Hash`/`Array` (with supported values), `ActiveRecord::Base` (via GlobalID).
- Prefer passing an **ID and re-fetching** with `find_by` in the job (guard for `nil`). GlobalID auto-serialization is acceptable — rescue `ActiveJob::DeserializationError` for deleted records.
- Never pass `order.attributes` (stale data) or `order.to_json` (no type safety).
- **Why only IDs/primitives:** a job may run minutes later; the object may have changed or been deleted. Re-fetching guarantees fresh data.

---

## 2. Solid Queue (Rails 8 Default)

Database-backed queue. No Redis dependency.

- Configure workers/dispatchers in `config/queue.yml` (per-queue threads/processes/polling); scale critical queues with more threads.
- Schedule recurring jobs in `config/recurring.yml` (class + schedule) — not via cron outside the app.
- Enforce single-flight work with `limits_concurrency to: 1, key: ->(...) { ... }`.

**Why Solid Queue over Sidekiq:** No Redis dependency. Database-backed (transactional reliability). Default in Rails 8. Use Sidekiq only if you need >10,000 jobs/minute or its specific features (batches, rate limiting).

| Feature | Solid Queue | Sidekiq |
|---------|-------------|---------|
| Backend | Database (PostgreSQL/SQLite) | Redis |
| Recurring jobs | Built-in (`recurring.yml`) | Requires sidekiq-cron |
| Throughput | Thousands/min | Millions/min |
| Transactional enqueue | Yes (same DB) | No (Redis is separate) |

---

## 3. Job Continuations (Large Batch Processing)

- Rails 8.1+: use native Active Job Continuations — `include ActiveJob::Continuable` and split the work into `step` blocks with built-in cursors, so a restart resumes from the last completed step. On ≤8.0, hand-roll it: process a bounded `limit`, then `self.class.perform_later(..., cursor: batch.last.id)` to continue. Never iterate an unbounded set in one job.
- Guard the chain with `limits_concurrency` so duplicates don't overlap.
- **Why:** each chunk is a separate job (bounded memory/time); failed chunks retry independently; the queue stays responsive between chunks.

---

## 4. Idempotency

Every job MUST be safe to run multiple times (retries, worker restarts, duplicate enqueuing).

- Always guard against already-processed state (status flag, timestamp, unique constraint).
- Use `find_by` (not `find`) to handle deleted records gracefully.
- Wrap critical sections with database constraints (unique index on idempotency key); rescue `ActiveRecord::RecordNotUnique` as "already done".
- Keep jobs focused: one job = one task.

---

## 5. Error Handling in Jobs

- `retry_on` transient errors with backoff; `discard_on` non-retryable errors. Custom `discard_on` blocks can record failure + report to `Rails.error`.
- After reporting inside `perform`, **re-`raise`** — `retry_on` only fires when the job raises. Swallowing the error kills retries.
- Wait strategies: fixed (`wait: 5.seconds`), `wait: :polynomially_longer`, or a lambda `->(executions) { ... }`.

| Error Type | Action | Example |
|-----------|--------|---------|
| Transient (network, timeout) | `retry_on` with backoff | `Net::OpenTimeout` |
| Deadlock | `retry_on` with short wait | `ActiveRecord::Deadlocked` |
| Record gone | `discard_on` | `ActiveJob::DeserializationError` |
| Business error | Report + discard | Custom domain errors |
| Bug | Let it fail (fix code) | `NoMethodError` |

---

## 6. ApplicationJob Base Class

- Centralize error handling in `ApplicationJob`, not per-job: base `retry_on ActiveRecord::Deadlocked` and `discard_on ActiveJob::DeserializationError`.
- Add a **dead letter queue**: `retry_on StandardError` with a final block that persists a `FailedJob` record and reports to `Rails.error` once retries are exhausted.

---

## 7. ActionMailer

### Mailer Rules

- One mailer per domain concept (`OrderMailer`, `UserMailer`, `AdminMailer`).
- Always `deliver_later` in production — never `deliver_now` in controllers (it blocks the request 100ms-5s). `deliver_now` is OK only inside jobs (already async).
- Use **parameterized** mailers (`with(order: order)`) over positional args — adding a parameter doesn't break callers, `params` is self-documenting, and it enables `before_action` on params.
- Provide both HTML and text templates (spam filters penalize HTML-only).
- Use `url` helpers (not `path`) in email views — emails need full URLs.
- Eager-load everything in the mailer method (`includes`) — never lazy-load in views (N+1 in email).
- I18n subjects: `t('.subject', ...)` auto-scopes to `mailer.action.subject`.

---

## 8. Mailer Previews

- Add `ActionMailer::Preview` classes under `test/mailers/previews/`; build the mail via `with(...)`, using existing or factory-built records. View at `/rails/mailers/<mailer>/<action>`.

---

## 9. Interceptors and Observers

- **Interceptor** (`delivering_email`) rewrites outgoing mail before send — e.g. redirect all staging mail to a safe inbox; register conditionally (`if Rails.env.staging?`).
- **Observer** (`delivered_email`) runs after send — e.g. audit-log every email.

---

## 10. Testing Jobs

- Assert enqueue with `have_enqueued_job(...).with(...).on_queue(...)`.
- Test behavior with `perform_now`: happy path, missing record (no error), and already-processed (idempotency — no state change).

---

## 11. Testing Mailers

- Build via `described_class.with(...).action`; assert `to`, `subject`, and `body.encoded` contents.
- In integration, assert `have_enqueued_mail(Mailer, :action).with(params:, args:)`.

---

## 12. Common Anti-Patterns

- **Long-running jobs** — don't `find_each { generate_report(...) }` in one job; fan out into per-record jobs (`perform_later(record.id)`).
- **Side effects in transactions** — never enqueue inside a transaction (job may run before commit). Enqueue **after** the block, or use an `after_commit` callback.
- **Passing too much data** — don't put a large hash/payload in the queue; store it and pass a reference (id).

---

## 13. Production Checklist

| Check | Action |
|-------|--------|
| Every job is idempotent? | Guard against already-processed state |
| Arguments are serializable? | Only primitives, hashes, arrays, AR models |
| `retry_on` for transient errors? | Network timeouts, deadlocks with backoff |
| `discard_on` for non-retryable errors? | `DeserializationError`, invalid format |
| Jobs enqueued outside transactions? | Use `after_commit` or enqueue after block |
| Long jobs split into chunks? | No single job should run >5 minutes |
| Mailers use `deliver_later`? | Never `deliver_now` in controllers |
| Mailers use parameterized style? | `with(order: order)` not positional args |
| Both HTML and text templates? | Spam filters penalize HTML-only emails |
| Queue workers configured per priority? | Critical queue gets more threads |
| Monitoring for failed jobs? | Dead letter queue or error reporting |
| Recurring jobs in `recurring.yml`? | Not scheduled via cron outside the app |
