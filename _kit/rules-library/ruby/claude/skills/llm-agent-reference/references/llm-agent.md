# LLM agent practices — worked examples

Companion reference to the `llm-agent-practices` rule; loaded on demand.

---

## 1. Prompt Engineering

### Own Your Prompts

```ruby
# GOOD — prompt loaded from file, ERB-templated
class PromptBuilder
  def initialize(template_path:)
    @template = File.read(template_path)
  end

  def build(defect:)
    ERB.new(@template).result_with_hash(defect: defect)
  end
end

# BAD — prompt hardcoded in Ruby class
class Validator
  def prompt(defect)
    "You are a QA expert. Analyze this defect: #{defect.summary}..."  # buried in code
  end
end
```

### Chain-of-Thought First

Always request a `reasoning` field **before** the answer field in the JSON schema. The model must think before deciding.

**Why:** When the answer comes first, the model commits to it and then rationalizes. When reasoning comes first, the model works through the problem and arrives at a better answer.

```json
{
  "reasoning": "step-by-step analysis (FIRST — model thinks before answering)",
  "score": "0 | 1 | 2 (AFTER reasoning)",
  "confidence": "0.0-1.0",
  "explanation": "brief explanation"
}
```

### Discrimination Rules

Explicitly define decision boundaries for ambiguous cases in the system prompt.

```
Rule: If the defect was caused by a missing null check in code → "Code Defect / Logic Error"
      NOT "Testing / Insufficient Coverage" (even if tests didn't catch it)
```

Each rule: **condition → correct answer** (with counter-example of the wrong answer). Update rules when new confusion patterns emerge from reports.

---

## 2. Context Window Management

### Pre-flight Token Check

Always count tokens before sending to LLM. If overflow: summarize or truncate the input.

```ruby
# GOOD — check before sending
def validate(item)
  prompt = build_prompt(item)
  token_count = count_tokens(prompt)

  if token_count > max_input_tokens
    prompt = build_prompt(item, summarize: true)
    logger.warn("Token overflow for #{item.key}: #{token_count}, summarized")
  end

  llm_client.chat(prompt)
end
```

**Why:** Context overflow silently degrades quality — the model doesn't error, it just gives worse answers because it loses the end of the prompt.

### Data Cleaning

Strip markup, HTML, noise from input before sending to LLM. Saves 10-20% tokens without losing semantic content.

```ruby
# Clean at the data entry point (once)
module TextCleaner
  module_function

  def clean(text)
    text
      .then { strip_html(it) }
      .then { strip_wiki_markup(it) }
      .then { normalize_whitespace(it) }
  end
end
```

---

## 3. Structured Output

### JSON Schema

Define a strict schema for LLM responses. Always include `reasoning` before the answer.

```ruby
# GOOD — schema as a Ruby constant, easy to reference and validate
RESPONSE_SCHEMA = {
  type: 'object',
  required: %w[reasoning answer confidence],
  properties: {
    reasoning: { type: 'string', description: 'Step-by-step analysis' },
    answer: { type: 'string', description: 'The classification result' },
    confidence: { type: 'number', minimum: 0.0, maximum: 1.0 }
  }
}.freeze
```

### Parsing Strategy

LLMs sometimes wrap JSON in markdown or add extra text. Parse defensively:

1. Try extracting JSON from `` ```json...``` `` markdown blocks
2. Try extracting bare `{...}` from response text
3. On `JSON::ParserError` — 1 retry with a compact correction prompt ("Return valid JSON only")
4. On second failure — return error result, **don't crash the batch**

```ruby
# GOOD — defensive parsing
def parse_response(text)
  json_str = extract_json(text)
  data = JSON.parse(json_str, symbolize_names: true)
  validate_schema!(data)
  data
rescue JSON::ParserError
  nil  # caller handles retry or error result
end

def extract_json(text)
  # Try markdown block first
  if (match = text.match(/```json\s*\n?(.*?)\n?\s*```/m))
    return match[1]
  end
  # Try bare JSON object
  if (match = text.match(/\{.*\}/m))
    return match[0]
  end
  text
end
```

---

## 4. Reliability and Error Handling

### Retry Strategy

```ruby
# GOOD — retry with exponential backoff
def with_retries(max_attempts: 3)
  attempts = 0
  begin
    attempts += 1
    yield
  rescue Faraday::ServerError, Faraday::ConnectionFailed, Faraday::TimeoutError => e
    raise if attempts >= max_attempts

    sleep_time = 2**attempts + rand(0.0..1.0)  # jitter
    logger.warn("Retry #{attempts}/#{max_attempts} after #{e.class}: sleeping #{sleep_time.round(1)}s")
    sleep(sleep_time)
    retry
  end
end
```

### Batch Resilience

Error in one item must **never** stop the batch. Each `process(item)` catches exceptions and returns a result with error info.

```ruby
# GOOD — batch continues on per-item error
results = items.map do |item|
  validate(item)
rescue StandardError => e
  logger.error("#{item.key}: #{e.message}")
  Result.new(key: item.key, error: e.message)
end
```

### Progress Persistence

Save progress after each item to enable resume on crash. JSONL (one JSON per line) is ideal — append-only, easy to parse, no corruption on crash.

```ruby
# Append result after each item
File.open('progress.jsonl', 'a') do |f|
  f.puts(result.to_json)
end

# Resume: skip already-processed items
processed_keys = File.exist?('progress.jsonl') ?
  File.foreach('progress.jsonl').map { JSON.parse(it)['key'] }.to_set :
  Set.new
remaining = items.reject { processed_keys.include?(it.key) }
```

### Rate Limiting

Configurable concurrency to respect API limits. Start conservative, increase based on observed behavior.

```ruby
# Semaphore pattern — limits concurrent requests
semaphore = Mutex.new
active_count = 0

threads.map do |item|
  Thread.new do
    semaphore.synchronize { active_count += 1 }
    begin
      validate(item)
    ensure
      semaphore.synchronize { active_count -= 1 }
    end
  end
end
```

---

## 5. Quality Assurance

### Majority Voting (Selective)

For high-accuracy requirements: run N independent LLM calls, take majority vote.

**Selective voting** (cost-efficient): first call with confidence check → if low → N-1 additional calls.

```ruby
# GOOD — selective voting
def validate_with_voting(item, min_confidence: 0.7, votes: 3)
  first_result = validate(item)
  return first_result if first_result.confidence >= min_confidence

  # Low confidence — get additional opinions
  additional = (votes - 1).times.map { validate(item) }
  all_results = [first_result] + additional
  majority_vote(all_results)
end
```

Saves ~50% cost vs always voting, minimal accuracy loss.

---

## 6. Concurrency

### Thread Pool Pattern

```ruby
require 'concurrent-ruby'

pool = Concurrent::FixedThreadPool.new(concurrency)
futures = defects.map do |defect|
  Concurrent::Future.execute(executor: pool) { validate(defect) }
end
results = futures.map(&:value)
pool.shutdown
pool.wait_for_termination
```

### Thread Safety Rules

```ruby
# GOOD — Mutex for shared mutable state
class ProgressTracker
  def initialize
    @mutex = Mutex.new
    @completed = 0
  end

  def increment
    @mutex.synchronize { @completed += 1 }
  end

  def completed
    @mutex.synchronize { @completed }
  end
end
```

---

## 7. Agentic Workflow Patterns

### Sequential (Prompt Chaining)

Pipeline where output of step N feeds into step N+1. Use when tasks have strict ordering dependencies.

```ruby
class ResearchWriterWorkflow
  def call(topic)
    research = ResearchAgent.new.ask(topic)
    draft = WriterAgent.new.ask(research)
    ReviewAgent.new.ask(draft)
  end
end
```

### Routing

Classify input, then route to a specialized handler. Use when different inputs need fundamentally different processing.

```ruby
class Router
  ROUTES = {
    code: CodeReviewAgent,
    data: DataValidationAgent,
    config: ConfigCheckAgent
  }.freeze

  def call(item)
    category = classify(item)
    agent = ROUTES.fetch(category)
    agent.new.call(item)
  end
end
```

### Parallel

Fan-out N independent calls, collect results. Use when analyses are independent of each other.

```ruby
def analyze(text)
  results = [SentimentAgent, SummaryAgent, KeywordAgent].map do |agent_class|
    Thread.new { agent_class.new.call(text) }
  end.map(&:value)

  { sentiment: results[0], summary: results[1], keywords: results[2] }
end
```

### Evaluator-Optimizer Loop

Generate → evaluate → refine until quality threshold met. **Always set MAX_ROUNDS** to prevent infinite loops.

```ruby
MAX_ROUNDS = 3

def generate_with_review(task)
  draft = DraftAgent.new.call(task)

  MAX_ROUNDS.times do
    review = CriticAgent.new.call(task: task, draft: draft)
    return draft if review.verdict == 'pass'

    draft = ReviseAgent.new.call(task: task, draft: draft, feedback: review.feedback)
  end

  draft  # return best effort after MAX_ROUNDS
end
```

---

## 8. Tool-as-Class Pattern

When building agents that use tools, define each tool as a class with: description, parameters, and execute method.

```ruby
class SearchTool
  DESCRIPTION = 'Search the knowledge base for relevant documents'

  def self.parameters
    {
      query: { type: 'string', description: 'Search query', required: true },
      limit: { type: 'integer', description: 'Max results', default: 5 }
    }
  end

  def execute(query:, limit: 5)
    results = knowledge_base.search(query, limit: limit)
    results.map { { title: it.title, excerpt: it.excerpt } }
  rescue SearchError => e
    { error: e.message }  # recoverable — LLM can retry or adjust
  end
end
```

### Security

**Treat ALL LLM-generated arguments as untrusted.** The LLM extracts arguments from natural language — they can be anything.

```ruby
# BAD — LLM-controlled code execution
def execute(code:)
  eval(code)            # arbitrary code execution
  system(code)          # shell injection
  send(code)            # arbitrary method call
  Model.where(code)     # SQL injection
end

# GOOD — validated, constrained inputs
def execute(query:, limit: 5)
  raise ArgumentError, 'limit must be 1-100' unless (1..100).cover?(limit)

  knowledge_base.search(sanitize(query), limit: limit)
end
```

---

## 9. Observability

### Monitoring Callbacks

```ruby
# Track tool calls and results for debugging
chat.on_tool_call { |tc| logger.info("Tool: #{tc.name}(#{tc.arguments})") }
chat.on_tool_result { |result| logger.debug("Result: #{result}") }
```
