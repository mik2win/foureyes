# ActiveRecord

```ruby
# Prevent N+1 — always eager load associations used in views
Record.includes(:items, :user).all

# Use exists? for presence checks — single SQL query
record.items.exists?           # GOOD
record.items.present?          # BAD — loads all records

# Use pluck for arrays of a single attribute
User.pluck(:name)

# Use find_each for large datasets
Record.find_each(batch_size: 100) { |r| ... }

# Use transactions for atomic operations
ActiveRecord::Base.transaction do
  record.update!(status: :active)
  inventory.decrement!(:quantity)
end

# Use load_async for independent parallel queries (Rails 7+)
records = Record.all.load_async
stats   = Stat.current.load_async
```

### Callbacks

```ruby
# BAD — hidden side effect, hard to trace
after_save :notify_admin

# GOOD — explicit call in service
class OrderFulfiller
  def call
    order.update!(status: :fulfilled)
    Notifier.new(order).notify  # explicit, visible
  end
end
```

Acceptable callback use cases: setting default values, maintaining data consistency within the same model's scope.
