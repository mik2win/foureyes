---
paths:
  - "**/*agent*.rb"
  - "**/*llm*.rb"
  - "config/prompts/**/*"
---

# LLM Agent Best Practices

Principles for building reliable LLM-based agents in Ruby. Based on 12-Factor Agents, RubyLLM, AI Cookbook, Active Agent (Evil Martians), and production experience.

> Worked examples live in the `llm-agent-reference` skill (`references/llm-agent.md`).

---

## 1. Prompt Engineering

### Own Your Prompts

Store prompts as versioned files in a dedicated directory (e.g., `config/prompts/`) — never hardcode in Ruby classes.

- **System prompt** = role + methodology + reference data + output format (fixed per task)
- **User prompt** = ERB template with item-specific data (variable per request)
- Iterate prompts separately from application logic — prompt changes shouldn't require code changes

### Chain-of-Thought First

Always request a `reasoning` field **before** the answer field in the JSON schema. The model must think before deciding. When the answer comes first, the model commits and then rationalizes; reasoning-first arrives at a better answer.

- For **reasoning models** (QwQ, o1, etc.): let the model's internal CoT work; don't over-constrain the thinking process
- For **regular models** (GPT-4, Llama, etc.): explicitly request step-by-step analysis in the prompt

### Few-Shot Examples

Include 3-6 examples in the system prompt covering edge cases and decision boundaries.

- Select examples that demonstrate **discrimination rules** — cases where categories are easy to confuse
- **Quality over quantity** — too many examples (>8) can degrade performance ("few-shot dilemma")
- Periodically review examples against real results and rotate underperforming ones

### Discrimination Rules

Explicitly define decision boundaries for ambiguous cases in the system prompt. Each rule: **condition → correct answer** (with counter-example of the wrong answer). Update rules when new confusion patterns emerge from reports.

---

## 2. Context Window Management

### Token Budget

Plan your token budget explicitly:

- **System prompt** (fixed): role + reference data + examples + output format
- **User prompt** (variable): depends on input item size
- **Response reserve**: tokens reserved for model output (typically 2000-4000)
- **Max input** = model context limit − response reserve

Store limits in configuration, not code.

### Pre-flight Token Check

Always count tokens before sending to LLM. If overflow: summarize or truncate the input. Context overflow silently degrades quality — the model doesn't error, it just gives worse answers because it loses the end of the prompt.

### Data Cleaning

Strip markup, HTML, noise from input before sending to LLM. Saves 10-20% tokens without losing semantic content. Clean at the data entry point (once).

---

## 3. Structured Output

### JSON Schema

Define a strict schema for LLM responses (e.g. as a frozen Ruby constant). Always include `reasoning` before the answer.

### Parsing Strategy

LLMs sometimes wrap JSON in markdown or add extra text. Parse defensively:

1. Try extracting JSON from `` ```json...``` `` markdown blocks
2. Try extracting bare `{...}` from response text
3. On `JSON::ParserError` — 1 retry with a compact correction prompt ("Return valid JSON only")
4. On second failure — return error result, **don't crash the batch**

### Validation

Validate parsed response against expected schema before using it:
- Required fields present
- `score`/`answer` in allowed values
- `confidence` in valid range [0.0, 1.0]
- Category/classification values exist in reference data (catch hallucinated values)

---

## 4. Reliability and Error Handling

### Retry Strategy

| Error Type | Action | Why |
|-----------|--------|-----|
| 5xx, timeout, connection | Retry up to 3 times with exponential backoff | Transient server issues |
| 4xx (except 429) | Don't retry — log and return error | Request is invalid |
| 429 (rate limit) | Retry with backoff from `Retry-After` header | Temporary throttling |
| JSON parse error | 1 retry with correction prompt | Model formatting issue |

Use exponential backoff with jitter on retries.

### Batch Resilience

Error in one item must **never** stop the batch. Each `process(item)` catches exceptions and returns a result with error info.

### Progress Persistence

Save progress after each item to enable resume on crash. JSONL (one JSON per line) is ideal — append-only, easy to parse, no corruption on crash. Resume by skipping already-processed keys.

### Rate Limiting

Configurable concurrency to respect API limits (e.g. a semaphore around active requests). Start conservative, increase based on observed behavior.

---

## 5. Quality Assurance

### Confidence Score

LLM self-reports confidence (0.0-1.0) in the JSON response. Use it for triage:
- **High confidence (>= 0.8):** result likely stable across runs
- **Low confidence (< 0.7):** candidate for re-validation or manual review
- Display in reports with color coding (green/yellow/red)

### Majority Voting (Selective)

For high-accuracy requirements: run N independent LLM calls, take majority vote. **Selective voting** (cost-efficient): first call with confidence check → if low → N-1 additional calls. Saves ~50% cost vs always voting, minimal accuracy loss.

### Stateless Processing

`process(item)` is a **pure function**: Input → Output.
- No shared state between items (12-Factor: Stateless Reducer)
- Each HTTP request to LLM is independent (no sessions, no chat history)
- Thread-safe by design — safe for concurrent execution

---

## 6. Concurrency

### Threads vs Fibers for I/O-bound LLM Work

LLM API calls are 99% I/O wait (5-60 seconds per call). Both approaches work:

| Approach | Library | Pros | Cons |
|----------|---------|------|------|
| **Threads** | `concurrent-ruby` | Simple, mature, well-understood | GVL (irrelevant for I/O), heavier than fibers |
| **Fibers** | `async` gem | Lightweight, scales to thousands | Requires compatible HTTP stack, newer ecosystem |

For most LLM agents, **threads are simpler and sufficient.** Use fibers when you need >50 concurrent requests. Prefer a `Concurrent::FixedThreadPool` for the thread-pool case.

### Thread Safety Rules

- Fields that are **read-only after `initialize`** → thread-safe by design (no locks needed)
- Unique values per call (e.g., `SecureRandom.uuid` for request IDs) → thread-safe
- **Shared mutable state** (counters, progress files) → protect with `Mutex`

---

## 7. Agentic Workflow Patterns

Five patterns for orchestrating LLM agents. Choose based on task structure.

- **Sequential (Prompt Chaining)** — pipeline where output of step N feeds into step N+1. Use when tasks have strict ordering dependencies.
- **Routing** — classify input, then route to a specialized handler. Use when different inputs need fundamentally different processing.
- **Parallel** — fan-out N independent calls, collect results. Use when analyses are independent of each other.
- **Fan-Out / Fan-In** — split task into parts → process each independently → synthesize. Like Parallel but with a merge step.
- **Evaluator-Optimizer Loop** — generate → evaluate → refine until quality threshold met. **Always set MAX_ROUNDS** to prevent infinite loops.

---

## 8. Tool-as-Class Pattern

When building agents that use tools, define each tool as a class with: description, parameters, and execute method.

### Security

**Treat ALL LLM-generated arguments as untrusted.** The LLM extracts arguments from natural language — they can be anything. Never `eval`/`system`/`send`/`Model.where` on LLM-supplied strings; validate and constrain every argument.

### Error Handling in Tools

- **Recoverable errors** (bad params, not found): return `{ error: "message" }` — the LLM can self-correct
- **Unrecoverable errors** (missing config, auth failure): raise exception — halt execution

---

## 9. Observability

### Logging

- Token count and usage % before each LLM call
- LLM response time for each item
- Progress: `[N/total] ITEM_KEY: result=X (elapsed)` after each processing step
- Batch summary: total time, throughput (items/min), success/error counts

### Monitoring Callbacks

Register `on_tool_call` / `on_tool_result` callbacks to log tool invocations and results for debugging.

### Reports

- **CSV** with all fields for data analysis
- **HTML** with visual indicators (score colors, confidence badges)
- **Progress file** (JSONL) for debugging and resume

---

## 10. Anti-Patterns to Avoid

1. **Don't batch multiple items in one LLM request** — model confuses results, one error loses entire batch
2. **Don't use high temperature for classification** — temperature=0 for deterministic results
3. **Don't retry on 4xx errors** — these indicate request problems, not transient failures
4. **Don't skip token counting** — context overflow silently degrades quality
5. **Don't hardcode prompts** — version them as files, iterate separately from code
6. **Don't trust LLM outputs blindly** — validate against reference taxonomy/schema
7. **Don't ignore confidence** — low confidence = unstable result, flag for review
8. **Don't give LLM unbounded iterations** — always set MAX_ROUNDS to prevent runaway costs
9. **Don't trust LLM-generated code/commands** — sandbox execution, validate inputs
10. **Don't use eval/system/send with LLM arguments** — treat all LLM outputs as untrusted user input
