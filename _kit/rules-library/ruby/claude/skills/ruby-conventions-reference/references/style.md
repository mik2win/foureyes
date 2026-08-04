# Ruby style — worked examples

Companion reference to the `ruby-style` rule; loaded on demand.

---

## 1. Self-Documenting Code

```ruby
# BAD — long method with comments explaining intent
def process_order(order)
  # Check if order is valid
  return unless order.items.any?
  return if order.total <= 0

  # Calculate discount
  discount = if order.total > 100
               order.total * 0.1
             elsif order.total > 50
               order.total * 0.05
             else
               0
             end

  # Apply discount and save
  order.total -= discount
  order.status = :processed
  order.save!
  # Send notification
  Mailer.order_processed(order).deliver_later
end

# GOOD — small methods with clear names
def process_order(order)
  return unless order.processable?

  order.apply_discount
  order.mark_processed!
  notify_order_processed(order)
end
```

---

## 2. Naming Conventions

```ruby
# GOOD
def user_signed_in?
def calculate_total_amount
class OrderProcessor
VALID_STATUSES = %w[active inactive].freeze

# BAD
def userSignedIn        # camelCase
def calc                # abbreviated, unclear
class order_processor   # snake_case for class
Valid_Statuses = [...]  # not SCREAMING_SNAKE_CASE
```

### Symbol vs String

Use **symbols** for identifiers, hash keys, enum-like values. Use **strings** for display text, user content, external data.

```ruby
# GOOD — symbols for internal keys and identifiers
status = :active
config = { timeout: 30, retries: 3 }
validates :name, presence: true

# GOOD — strings for content and display
greeting = 'Hello, World!'
error_message = "Invalid value: #{value}"

# BAD — strings as internal identifiers (wasteful, less readable)
status = 'active'
config = { 'timeout' => 30 }
```

---

## 3. String Handling

```ruby
# frozen_string_literal: true

# GOOD
name = 'static string'
greeting = "Hello, #{name}!"

message = <<~TEXT
  Dear #{name},

  Your order has been shipped.
TEXT

# Mutable string when frozen_string_literal is true
buffer = +''
buffer << 'chunk1'
buffer << 'chunk2'

# BAD
name = "static string"        # double quotes without interpolation
message = "Line 1\n" +        # concatenation for multiline
          "Line 2\n" +
          "Line 3\n"
```

---

## 4. Control Flow — Idiomatic Ruby

### Guard Clauses

Return early to reduce nesting. The main logic should be at the top indentation level.

```ruby
# GOOD — guard clauses
def process(order)
  return unless order
  return if order.completed?

  order.process!
end

# BAD — nested conditionals
def process(order)
  if order
    unless order.completed?
      order.process!
    end
  end
end
```

### unless / until

Use `unless` instead of `if !`, `until` instead of `while !`. Reads as English. **Never** combine `unless` with `else` — use `if/else` instead.

```ruby
# GOOD
raise ArgumentError, 'Name required' unless name
retry until response.success?

# BAD
raise ArgumentError, 'Name required' if !name
retry while !response.success?

# BAD — unless with else is confusing
unless user.admin?
  deny_access
else
  grant_access
end

# GOOD — use if/else when you need else
if user.admin?
  grant_access
else
  deny_access
end
```

### Modifier Forms

Use modifier `if`/`unless` for single-line statements. Reads naturally.

```ruby
# GOOD
log_warning(message) if verbose?
return if items.empty?
raise AuthError unless current_user

# BAD — full block for trivial one-liner
if verbose?
  log_warning(message)
end
```

### Iteration

Use `each`, not `for`. The `for` keyword leaks variables into the outer scope.

```ruby
# GOOD
items.each { |item| process(item) }

# BAD — for leaks `item` into outer scope
for item in items
  process(item)
end
```

### Ternary

Use ternary **only** for simple value assignment. Never nest ternaries.

```ruby
# GOOD — simple assignment
status = order.paid? ? :confirmed : :pending

# BAD — complex logic in ternary
message = user.admin? ? (user.active? ? 'Welcome admin' : 'Inactive admin') : 'Access denied'

# GOOD — use if/elsif for complex branching
message = if user.admin? && user.active?
            'Welcome admin'
          elsif user.admin?
            'Inactive admin'
          else
            'Access denied'
          end
```

---

## 5. Method Arguments

### Keyword Arguments for 2+ Parameters

Keyword arguments make call sites self-documenting. Use positional for 0-1 required args.

```ruby
# GOOD — keyword args: clear at call site
def send_email(to:, subject:, body:, cc: nil)
  # ...
end
send_email(to: user.email, subject: 'Welcome', body: template)

# BAD — positional args: meaning unclear at call site
def send_email(to, subject, body, cc = nil)
  # ...
end
send_email(user.email, 'Welcome', template)  # what's what?

# GOOD — single required positional arg is fine
def find(id)
  # ...
end
```

### Never Use Options Hash

Options hashes were Ruby 1.x/2.x patterns before keyword arguments existed. Use keyword args instead.

```ruby
# BAD — old-style options hash
def create_user(attrs = {})
  name = attrs[:name]
  email = attrs[:email]
end

# GOOD — keyword arguments
def create_user(name:, email:, role: :member)
  # ...
end
```

---

## 6. Method Visibility

```ruby
class OrderProcessor
  def initialize(order, notifier:)
    @order = order
    @notifier = notifier
  end

  # Public API
  def call
    validate!
    process_payment
    send_confirmation
  end

  private

  attr_reader :order, :notifier

  def validate!
    raise InvalidOrder unless order.valid?
  end

  def process_payment
    # ...
  end

  def send_confirmation
    notifier.call(order)
  end
end
```

```ruby
# BAD — private before each method (noisy)
class Foo
  def public_method; end

  private def helper1; end
  private def helper2; end
  private def helper3; end
end
```

---

## 7. Modern Ruby Features (3.2-3.4)

### Data.define — Immutable Value Objects (Ruby 3.2+)

`Data.define` creates frozen, immutable value objects. Use for data that has no identity and should never be mutated. Replaces `Struct` for frozen data.

```ruby
# GOOD — Data.define: immutable by default, keyword args
Point = Data.define(:x, :y)
p = Point.new(x: 1, y: 2)
p.frozen?                    # => true
p.with(y: 10)               # => Point(x: 1, y: 10) — new copy

# Custom methods and defaults
Defect = Data.define(:key, :summary, :category, :subcategory) do
  def full_category = "#{category} / #{subcategory}"

  def initialize(key:, summary:, category: nil, subcategory: nil)
    super
  end
end

# BAD — mutable Struct for data that should be frozen
Defect = Struct.new(:key, :summary, :category, :subcategory)
d = Defect.new('KEY-1', 'Bug', 'Code', 'Logic')
d.key = 'CHANGED'  # silently mutates — dangerous for value objects
```

### Pattern Matching (stable since Ruby 3.0)

Use `case/in` for destructuring complex data. Cleaner than nested `if`/`dig` chains.

```ruby
# GOOD — pattern matching with destructuring
case response
in { status: 200, body: { data: Array => items } }
  process_items(items)
in { status: 200, body: { data: nil } }
  handle_empty
in { status: (400..499) => code, body: { error: String => msg } }
  log_client_error(code, msg)
in { status: (500..) }
  retry_request
end

# Pin operator — match against existing variable
expected_key = 'PROJ-123'
case defect
in { key: ^expected_key }
  puts 'Found the target defect'
end

# BAD — nested conditionals for same logic
if response[:status] == 200
  if response.dig(:body, :data).is_a?(Array)
    process_items(response[:body][:data])
  elsif response.dig(:body, :data).nil?
    handle_empty
  end
elsif response[:status].between?(400, 499)
  log_client_error(response[:status], response.dig(:body, :error))
end
```

### Endless Methods (Ruby 3.0+)

Use for single-expression methods. Keep them short — if the expression wraps, use a regular method.

```ruby
# GOOD — concise accessors and simple computations
def full_name = "#{first_name} #{last_name}"
def active? = status == :active
def total = subtotal + tax

# BAD — complex logic in endless method
def process = validate! && calculate_discount && apply_tax && save! && notify
```

### `it` Block Parameter (Ruby 3.4)

Implicit block parameter for single-argument blocks. Cleaner than `_1`.

```ruby
# GOOD — Ruby 3.4
results.select { it.score == 2 }
defects.sort_by { it.key }
names.map { it.upcase }

# OK — Ruby 2.7+ numbered parameters (less readable)
results.select { _1.score == 2 }

# CLASSIC — explicit block parameter (always valid)
results.select { |r| r.score == 2 }
```

### filter_map (Ruby 2.7+)

Combines `select` + `map` in one pass. Returns non-nil results only.

```ruby
# GOOD — filter_map
emails = users.filter_map { |u| u.email if u.active? }

# BAD — select + map (two passes)
emails = users.select(&:active?).map(&:email)
```

### Other Useful Features

```ruby
# Set is built-in since Ruby 3.2 (no require needed)
valid_statuses = Set[:active, :pending, :completed]
valid_statuses.include?(:active)  # O(1)

# Integer#ceildiv (Ruby 3.2)
10.ceildiv(3)  # => 4 (ceiling division)

# Hash.new with capacity (Ruby 3.4) — pre-allocate for known sizes
cache = Hash.new(capacity: 1000)
```

---

## 8. Data.define vs Struct vs Plain Class

```ruby
# Data.define — value objects (config, results, parsed data)
ValidationResult = Data.define(:score, :confidence, :explanation, :error) do
  def success? = error.nil?
  def high_confidence? = confidence && confidence >= 0.8
end

# Struct — lightweight mutable objects (display scopes, internal transport)
ReportScope = Struct.new(:project, :date_range, :filters, keyword_init: true)

# Plain class — behavior-rich objects with state
class CategoryValidator
  def initialize(llm_client:, config:)
    @llm_client = llm_client
    @config = config
  end

  def call(defect)
    # complex validation logic with state
  end
end
```

---

## 9. Object Equality

```ruby
# GOOD — value object with proper equality
Token = Data.define(:type, :value) # Data.define gives == and eql? for free

# GOOD — plain class with custom equality
class Money
  include Comparable

  attr_reader :amount, :currency

  def initialize(amount, currency)
    @amount = amount
    @currency = currency
  end

  def ==(other)
    other.is_a?(Money) && amount == other.amount && currency == other.currency
  end
  alias eql? ==

  def hash
    [amount, currency].hash
  end

  def <=>(other)
    return nil unless other.is_a?(Money) && currency == other.currency

    amount <=> other.amount
  end
end
```
