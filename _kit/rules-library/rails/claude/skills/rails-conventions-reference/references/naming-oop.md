# Naming, Ruby usage, and OOP principles

## Naming and Ruby usage

```ruby
# GOOD
def user_signed_in?
def calculate_total_amount
class OrderProcessor

# BAD
def userSignedIn
def calc
class order_processor
```

```ruby
# GOOD
user&.profile&.avatar_url
Time.current
'static string'

# BAD
user && user.profile && user.profile.avatar_url
Time.now
```

## OOP principles (POODR, 99 Bottles, Clean Architecture)

### Single Responsibility (SRP)

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
```

### Dependency Injection

```ruby
# BAD
class ReportGenerator
  def call
    data = DataSource.fetch  # hardcoded
  end
end

# GOOD
class ReportGenerator
  def initialize(data_source)
    @data_source = data_source
  end
end
```

### Tell, Don't Ask

```ruby
# BAD — asking
if order.status == 'pending'
  order.status = 'completed'
  order.completed_at = Time.current
  order.save
end

# GOOD — telling
order.complete!
```

### Law of Demeter

```ruby
# BAD — train wreck
customer.orders.last.line_items.first.product.name

# GOOD — delegate
customer.last_ordered_product_name
```

One dot per statement is a guideline, not a hard rule. Chaining on the same type (e.g. `array.select.map`) is fine.

### Duck Typing

```ruby
# BAD — type checking
def process(entity)
  if entity.is_a?(Order)
    entity.fulfill
  elsif entity.is_a?(Refund)
    entity.execute
  end
end

# GOOD — shared interface
def process(processable)
  processable.process
end
```

### Open/Closed Principle

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
```

### Name things by what they ARE

```ruby
ReportGenerator    # GOOD — noun
GenerateReport     # BAD — verb phrase
```
