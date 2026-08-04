---
paths:
  - "**/*.py"
---

# Python Observability

Logging *configuration* and observability wiring. The level / lazy-arg / secret discipline
lives in `python-design.md` §8 (Logging Discipline) and the generic
`rules/_generic/observability.md` — this is the Python-specific setup.

---

## 1. Logger setup

- `logger = logging.getLogger(__name__)` per module — never the root logger, and never
  `print()` for diagnostics (`print` is CLI/REPL output only).
- Configure handlers/formatters once, at the entry point (composition root). Libraries and
  domain modules only `getLogger` and emit — they never call `basicConfig` or add handlers.
- `logging.config.dictConfig(...)` for non-trivial setup; set levels per logger, not globally.

## 2. Structured / JSON logs

- For anything aggregated, emit JSON via `structlog` (or `python-json-logger` on stdlib).
  Bind context once — `structlog.contextvars.bind_contextvars(...)` / `logger.bind(...)` — so
  request id / user / job ride every line without re-passing.
- Keep the stdlib `logging` API surface even under `structlog`, so levels and handlers compose.

## 3. Exceptions

- Inside an `except` block log with `logger.exception("...")` (or `exc_info=True`) so the
  traceback is captured — `logger.error(str(e))` throws the stack away.
- Log-and-rethrow XOR handle (see `python-design.md` §7). Don't re-log the same error at every
  level as it unwinds.

## 4. Correlation context

- Propagate a request/correlation id with `contextvars.ContextVar` (async-safe, no leakage
  across tasks) and inject it via a `logging.Filter` or structlog processor — don't thread it
  through every signature.

## 5. Metrics & health

- If exporting metrics, do it at the I/O edge with the OpenTelemetry / Prometheus client — the
  domain stays pure (it returns values; the shell records them). Keep label cardinality low.
- Services expose liveness/readiness; `asyncio` / worker loops log start, per-batch counts, and
  failures as ERROR.
