# Observability

Two distinct things share this name in the kit. Keep them separate:

1. **Your code's observability** — structured logging, no-secrets/PII, correlation IDs, actionable metrics, health signals. Encoded as always-on + per-stack rules:
   - `rules/_generic/observability.md` (language-neutral, always on)
   - `_kit/rules-library/python/claude/rules/python-observability.md`
   - `_kit/rules-library/ruby/claude/rules/ruby-observability.md`
   - `_kit/rules-library/rails/claude/rules/observability.md`
2. **Claude Code's own telemetry** — usage/cost/process analytics of the development work itself, via OpenTelemetry. Opt-in, off by default. Covered below.

---

## Claude Code telemetry (OpenTelemetry)

Claude Code can export its own usage as OTEL **metrics** and **logs/events** — sessions, lines of code, commits/PRs, token usage, cost, tool-permission decisions, active time. This is the "analytics of the development process" view: how the team actually uses the agent.

> Opt-in only. Nothing is exported until you set `CLAUDE_CODE_ENABLE_TELEMETRY=1`.

Env-key names below are verified against the official docs:
<https://code.claude.com/docs/en/monitoring-usage>.

### Enable it

`settings.json` is plain JSON with **no comment support**, so the kit keeps this example here rather than as an inactive key in `settings.template.json`. To turn telemetry on, add an `"env"` block like the one below to your `.claude/settings.json` (merge with any existing `env`), point the endpoint at your collector, and restart Claude Code:

```json
"env": {
  "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
  "OTEL_METRICS_EXPORTER": "otlp",
  "OTEL_LOGS_EXPORTER": "otlp",
  "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
  "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
  "OTEL_METRIC_EXPORT_INTERVAL": "60000",
  "OTEL_LOGS_EXPORT_INTERVAL": "5000"
}
```

Key reference:

| Variable | Purpose | Values |
|----------|---------|--------|
| `CLAUDE_CODE_ENABLE_TELEMETRY` | Master switch (required) | `1` |
| `OTEL_METRICS_EXPORTER` | Metrics backend | `otlp` · `prometheus` · `console` · `none` |
| `OTEL_LOGS_EXPORTER` | Logs/events backend | `otlp` · `console` · `none` |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | OTLP wire protocol | `grpc` · `http/protobuf` · `http/json` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Collector endpoint | e.g. `http://localhost:4317` (grpc) |
| `OTEL_EXPORTER_OTLP_HEADERS` | Auth headers (if needed) | e.g. `Authorization=Bearer <token>` |
| `OTEL_METRIC_EXPORT_INTERVAL` | Metrics flush interval (ms) | default `60000` |
| `OTEL_LOGS_EXPORT_INTERVAL` | Logs flush interval (ms) | default `5000` |

Cardinality/content toggles (optional): `OTEL_METRICS_INCLUDE_SESSION_ID` (default `true`), `OTEL_METRICS_INCLUDE_VERSION` (default `false`), `OTEL_METRICS_INCLUDE_ACCOUNT_UUID` (default `true`), `OTEL_LOG_USER_PROMPTS` (default off — prompt text is redacted unless set).

### Point it at a local collector

Minimal local stack: an **OpenTelemetry Collector** receiving OTLP, exporting metrics to **Prometheus**, visualized in **Grafana**. Sketch:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: 0.0.0.0:4317 }
      http: { endpoint: 0.0.0.0:4318 }
exporters:
  prometheus:        { endpoint: 0.0.0.0:8889 }   # scrape this from Prometheus
  debug:             { verbosity: detailed }       # logs/events to stdout while testing
service:
  pipelines:
    metrics: { receivers: [otlp], exporters: [prometheus] }
    logs:    { receivers: [otlp], exporters: [debug] }
```

Run the collector (`localhost:4317` for grpc / `:4318` for http), set `OTEL_EXPORTER_OTLP_ENDPOINT` to match, then point Prometheus at `:8889` and Grafana at Prometheus. To smoke-test without any infra, set both exporters to `console` and watch the metrics/events print to your terminal.

### What appears

Standard metrics (names per the docs):

| Metric | Meaning |
|--------|---------|
| `claude_code.session.count` | CLI sessions started |
| `claude_code.lines_of_code.count` | Lines added/removed |
| `claude_code.commit.count` / `claude_code.pull_request.count` | Commits / PRs created |
| `claude_code.token.usage` | Tokens consumed (input/output/cache) |
| `claude_code.cost.usage` | Estimated session cost (USD) |
| `claude_code.code_edit_tool.decision` | Edit-permission accept/reject decisions |
| `claude_code.active_time.total` | Active time (seconds) |

Plus log/event records for prompts, tool results, and API requests (content redacted by default). Use these to see usage, cost, and tool-usage patterns across the team.
