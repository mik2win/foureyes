# Services

Name by **what the object IS** (noun), not what it does (verb):

```ruby
# GOOD names
OrderFulfiller
PricingCalculator
RegistrationApprover

# BAD names
FulfillOrder
CalculatePricing
```

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

**Pattern 2 — multiple public methods** when the service acts as a facade:

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
    # shared logic
  end
end
```

Organize with modules when appropriate: `Reports::ExportService`, `Orders::FulfillmentService`.

**Dependency rule:** Domain services should not depend on framework specifics. Keep business logic independent so it can be tested and reused without Rails.
