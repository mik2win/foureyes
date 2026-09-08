# Observability

Product observability: what your code emits so that a question asked during an incident already has an answer in the data. The always-loaded short form is `rules/_generic/observability.md` (structured logs, no secrets/PII, correlation ids, actionable metrics, health signals), and the stack packs name the concrete tooling — `_kit/rules-library/python/claude/rules/python-observability.md`, `_kit/rules-library/ruby/claude/rules/ruby-observability.md`, `_kit/rules-library/rails/claude/rules/observability.md`. This page is the shape those rules assume.

Order of work: choose the failure modes you intend to catch first, then the signals that catch them. The reverse order produces metrics nobody acts on.

## The wide event

Emit **one wide, structured event per unit of work** — a request, a job, a queue message, a scheduled run. One row, many attributes, queryable by any of them. Three narrow log lines joined after the fact answer the question you already knew to ask; one wide event answers the one you did not.

"Log the context that makes the line actionable" is zero guidance. This is the checklist — walk it before calling instrumentation done, and drop only the rows your system genuinely has no answer for:

| Group | Attributes | What it unblocks |
|---|---|---|
| Identity | service · environment · owning team | which of four similarly named services this actually is |
| Version | build id · commit sha · deploy trigger · deploy age | "did the deploy do this" answered in one filter |
| Configuration | every feature-flag value evaluated for this unit | a flag-scoped comparison at any exposure |
| Platform | runtime · framework · datastore versions | an upgrade told apart from a code change |
| Request | matched route · parsed route params · user-agent parsed at emit, not regexed later | grouping that survives a URL-scheme change |
| Timing | per-stage `*.duration_ms` on the event itself | the slow stage without a join across child spans |
| Downstream | call counts and cumulative duration per dependency | an N+1 or a retry storm visible without opening a trace |
| Actor | user id · type · org/tenant · account age | "only new tenants" and "only one org" as filters |
| Budget | rate-limit remaining · cache hit/miss · process uptime | throttling and cold starts told apart from bugs |
| Outcome | status · a stable literal error code on every failure that crosses a boundary | error classes counted without parsing messages |

Cardinality runs the other way here than it does for metrics: metric labels stay low-cardinality, the event does not. Ids — build, commit, trace, user, tenant, query hash — are the whole reason the event is worth keeping; never move one off the event to protect a metric.

Timings you will actually query belong as attributes on the wide event, not only as child spans. The cross-request question ("which stage got slower after the release?") otherwise needs a join over child spans that nobody writes mid-incident, and the small duplication is the price of an answer.

One name per attribute, defined once in a telemetry constants module or a checked-in attribute schema, each with a one-line human-readable description. Two failures come from skipping this. An agent reading `slow_request` with no description will explain the latency *by* the attribute rather than skipping it, and will not flag the doubt. An agent writing instrumentation will invent a third spelling of a name that already exists, and add a counter for a property that is already a span attribute. Point instrumentation work at that module, and validate what is actually emitted against the schema before calling it done — read a real event, not the diff.

## Span shaping

A span earns its place when the work is both **interesting** — variable latency, can fail, crosses a process or network boundary — and **aggregable**: something you would ask about across many requests, not read once. Getters, loop iterations, pure-CPU validation, and orchestration that only calls already-instrumented code get attributes on the parent instead. A trace with a hundred 2 ms spans is a signal to roll them up, not a sign of thorough instrumentation.

Draw span boundaries on domain seams, not on the org chart. Traces drift toward team structure on their own, and the trace shaped by who owns what is the one that fails you when the question crosses team lines.

## Event-based SLIs

An SLI classifies **every event** as one of three outcomes: good, bad, or not eligible. Two filters make it reproducible:

- **Eligibility — which events count at all.** Name the route and method, restrict to root spans, and exclude synthetic traffic and health probes by user agent. Child spans of outgoing calls carry their own status codes and will corrupt any rate computed over them. Probes are fast and always succeed; left in the denominator they dilute the bad fraction until a real regression cannot clear the threshold.
- **Success — what makes an eligible event good.** Status alone is not enough: an event that returns 200 after 2.5 seconds is a failure. State the duration bound inside the criterion, not beside it.

Prefer this to time-based windows. A five-minute bucket goes bad on one slow request, which produces both false alarms and misses; per-event classification produces neither. When a model drafts the expression, the filter it silently drops is the root-span one — check for that specifically.

An alert built on an SLI still has to earn its place: it must be a reliable indicator that user experience is degraded, and a responder must have a systematic way to act on it. Fail either and delete it. Anything the system already heals — autoscale, failover, a circuit breaker — is a business-hours investigation, never a page.

## Signals for an LLM feature

The defaults above quietly invert when the feature calls a model, and an agent instrumenting one will apply them anyway unless the project says otherwise:

- **The unit of success is the task, not the call.** A fast, well-formed, wrong answer is not a success, and a failed tool-call span inside a task that finished correctly is not an incident. Classify at the task boundary.
- **Feedback signals are first-class attributes**, not a separate analytics pipeline: thumbs up/down, retry, edit-after-accept, abandonment — on the same event as the model name, the prompt version, and the token counts.
- **Do not store cost.** Store model, prompt version, and input/output token counts, and derive cost at query time. Rate cards change; a stored cost is wrong the day the price moves and cannot be recomputed.
- **Large inputs and outputs go in by reference** — an id into the system of record, not the text on the event. The event stays queryable and the payload stays somewhere it can be redacted.
- **Upstream provider timeouts and refusals want an SLO, not a threshold alert.** They are routine at a low rate and an incident at a high one, and only an error budget tells those apart.

---

Claude Code's own usage telemetry — OpenTelemetry export of sessions, tokens, cost and tool decisions — is a different subject and is not covered here; see <https://code.claude.com/docs/en/monitoring-usage>.
