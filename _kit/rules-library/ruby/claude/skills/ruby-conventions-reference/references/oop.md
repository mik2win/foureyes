# Ruby OOP — worked examples

Companion reference to the `ruby-oop` rule; loaded on demand.

---

## 1. Single Responsibility (SRP)

```ruby
# BAD — Order knows too much
class Order
  def calculate_total = ...
  def send_confirmation_email = ...
  def generate_invoice_pdf = ...
end

# GOOD — each concern in the right place
class Order
  def total = ...                  # belongs to the entity
end
class OrderConfirmation
  def send(order) = ...            # notification logic
end
class InvoiceGenerator
  def call(order) = ...            # PDF generation
end
```

---

## 2. Dependency Injection

**Why:** Hardcoded dependencies create invisible coupling. You can't test, swap, or configure them independently.

```ruby
# BAD — hardcoded dependency
class ReportGenerator
  def call
    data = DataSource.fetch  # can't test without real DataSource
  end
end

# GOOD — injectable
class ReportGenerator
  def initialize(data_source)
    @data_source = data_source
  end

  def call
    data = @data_source.fetch
  end
end

# In production:
ReportGenerator.new(PostgresDataSource.new)

# In tests:
ReportGenerator.new(instance_double(DataSource, fetch: test_data))
```

---

## 3. Tell, Don't Ask

**Why:** When you ask an object for its state and act on it externally, you duplicate knowledge about how that state works. When the state changes, every caller must update.

```ruby
# BAD — asking and deciding externally
if order.status == 'pending'
  order.status = 'completed'
  order.completed_at = Time.now
  order.save
end

# GOOD — telling the object what to do
order.complete!

# Inside Order:
def complete!
  self.status = 'completed'
  self.completed_at = Time.now
  save
end
```

```ruby
# BAD — extracting and formatting externally
"#{defect.category} / #{defect.subcategory}"

# GOOD — the object knows how to present itself
defect.full_category  # => "Code Defect / Logic Error"
```

---

## 4. Law of Demeter

**Why:** Long chains couple you to the internal structure of distant objects. If any intermediate structure changes, your code breaks.

```ruby
# BAD — reaching through multiple objects
customer.orders.last.line_items.first.product.name

# GOOD — delegate or encapsulate
customer.last_ordered_product_name

# In the model:
class Customer
  def last_ordered_product_name
    orders.last&.primary_product_name
  end
end
```

One dot per statement is a guideline, not a hard rule. Chaining on the same type (e.g. `array.select.map`) is fine. The goal is to avoid coupling to internal structure of distant objects.

---

## 5. Duck Typing

**Why:** Type checking (`.is_a?`) creates rigid coupling and violates Open/Closed. Adding a new type means modifying every `is_a?` check.

```ruby
# BAD — type checking
def process(entity)
  if entity.is_a?(Order)
    entity.fulfill
  elsif entity.is_a?(Refund)
    entity.execute
  end
end

# GOOD — shared interface (duck type)
def process(processable)
  processable.process  # any object that responds to #process
end

# Even better — define the contract explicitly
module Processable
  def process
    raise NotImplementedError
  end
end
```

---

## 6. Managing Dependency Direction

```ruby
# BAD — stable class depends on volatile class
class Logger                    # used everywhere (stable)
  def log(message)
    SlackNotifier.new.send(msg) # depends on specific volatile service
  end
end

# GOOD — volatile depends on stable
class SlackNotifier             # volatile, changes often
  def initialize(logger)
    @logger = logger            # depends on stable Logger
  end
end
```

---

## 8. Open/Closed Principle (SOLID)

```ruby
# GOOD — open for extension via strategy
class Formatter
  def initialize(strategy)
    @strategy = strategy
  end

  def format(data)
    @strategy.call(data)
  end
end

# Add new format without modifying Formatter:
json_formatter = ->(data) { data.to_json }
csv_formatter  = ->(data) { data.map(&:to_csv).join("\n") }
html_formatter = ->(data) { SlimRenderer.new.render(data) }
```

---

## 9. Name Things by What They ARE

```ruby
ReportGenerator    # GOOD — noun, describes what it is
GenerateReport     # BAD — verb phrase, describes what it does
reporter           # BAD — vague
```

---

## 10. Composition over Inheritance

```ruby
# GOOD — composition via module
module Trackable
  def track_changes
    # ...
  end
end

class Order
  include Trackable
end

# BAD — inheritance for code reuse
class Order < TrackableEntity  # deep hierarchy, tight coupling
end

# OK — inheritance when "is-a" is clear and shallow
class JiraApiError < StandardError; end
class LlmApiError < StandardError; end
```

---

## 11. SOLID + DRY + YAGNI

```ruby
# BAD — DRY gone wrong: forcing unrelated things into shared abstraction
class UniversalProcessor
  def process(type, data)
    case type
    when :order then ...
    when :refund then ...
    when :report then ...  # these have nothing in common
    end
  end
end

# GOOD — separate classes, some duplication is OK
class OrderProcessor
  def call(order) = ...
end

class RefundProcessor
  def call(refund) = ...
end
```

---

## 12. Modules — Namespaces AND Mixins

### Modules as Namespaces

```ruby
# GOOD — namespace communicates structure
module JiraDefectValidator
  class Config; end
  class DefectFetcher; end
  class CategoryValidator; end
  class ReportGenerator; end
end

# BAD — flat namespace, names must be verbose to avoid collision
class JiraDefectValidatorConfig; end
class JiraDefectFetcher; end
```

### Modules as Mixins

Use `include` for instance methods, `extend` for class methods, `module_function` for utility functions.

```ruby
# include — adds instance methods
module Retryable
  def with_retries(max_attempts: 3)
    attempts = 0
    begin
      attempts += 1
      yield
    rescue StandardError => e
      retry if attempts < max_attempts
      raise
    end
  end
end

class LlmClient
  include Retryable

  def chat(prompt)
    with_retries { http_post(prompt) }
  end
end
```

```ruby
# module_function — callable both as module method and instance method
module TextCleaner
  module_function

  def strip_html(text)
    text.gsub(/<[^>]+>/, '')
  end

  def normalize_whitespace(text)
    text.gsub(/\s+/, ' ').strip
  end
end

# Call as module method
TextCleaner.strip_html(raw_text)

# Or include for instance use
class Defect
  include TextCleaner
  def clean_description = strip_html(description)
end
```

### Hook: self.included Pattern

Use `self.included` to add class methods when a module is included:

```ruby
module Cacheable
  def self.included(base)
    base.extend(ClassMethods)
  end

  module ClassMethods
    def cache_key_prefix(prefix)
      @cache_prefix = prefix
    end
  end

  def cache_key
    "#{self.class.instance_variable_get(:@cache_prefix)}/#{id}"
  end
end
```

---

## 13. Service Objects

**Pattern 1 — single `#call`** for focused, single-operation services:

```ruby
class OrderFulfiller
  def initialize(order)
    @order = order
  end

  def call
    # one clear operation
  end

  private

  attr_reader :order
end

OrderFulfiller.new(order).call
```

**Pattern 2 — multiple public methods** when a service acts as a facade over related operations:

```ruby
class PricingCalculator
  def initialize(items, discounts: [])
    @items = items
    @discounts = discounts
  end

  def subtotal   = calculate(with_discounts: false)
  def total      = calculate(with_discounts: true)
  def savings    = subtotal - total

  private

  attr_reader :items, :discounts

  def calculate(with_discounts:)
    # shared calculation logic
  end
end
```

---

## 14. Error Handling

### Custom Exception Hierarchies

```ruby
# GOOD — domain exception hierarchy
module MyApp
  class Error < StandardError; end

  class NotFoundError < Error; end
  class ValidationError < Error; end
  class ApiError < Error; end

  class ClientError < ApiError; end   # 4xx
  class ServerError < ApiError; end   # 5xx
end

# Specific rescue
rescue MyApp::NotFoundError => e
  log_error(e)

# Broad rescue for entire domain
rescue MyApp::Error => e
  handle_gracefully(e)
```

### Rescue Rules

```ruby
# GOOD — specific rescue with context
def fetch_issue(key)
  client.get("/issue/#{key}")
rescue Faraday::ResourceNotFound => e
  raise JiraApiError, "Issue #{key} not found: #{e.message}"
rescue Faraday::ServerError => e
  raise JiraApiError, "Jira server error: #{e.message}"
end

# BAD — bare rescue catches everything including NoMethodError, NameError
def fetch_issue(key)
  client.get("/issue/#{key}")
rescue => e  # catches coding errors too!
  nil
end
```

### Error Taxonomy: Recoverable vs Unrecoverable

```ruby
# Recoverable — return error result, batch continues
def validate(defect)
  result = llm_client.chat(build_prompt(defect))
  parse_result(result)
rescue LlmApiError => e
  ValidationResult.new(defect_key: defect.key, error: e.message)
end

# Unrecoverable — raise, stop everything
def initialize
  raise ConfigError, 'LLM_TOKEN is required' unless ENV['LLM_TOKEN']
end
```
