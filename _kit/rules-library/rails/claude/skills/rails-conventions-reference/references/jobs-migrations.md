# Background jobs and migrations

## Background Jobs (Sidekiq / ActiveJob)

```ruby
# Jobs must be idempotent — safe to retry on failure
class RecalculateJob < ApplicationJob
  queue_as :default

  def perform(record_id)
    record = Record.find_by(id: record_id)
    return unless record  # guard against deleted records

    RecalculateService.new(record).call
  end
end
```

## Migrations

```ruby
# Write reversible migrations
def change
  add_column :records, :status, :string, null: false, default: 'draft'
  add_index :records, :status
end

# Always add indexes for columns used in WHERE / JOIN / ORDER
add_index :items, [:record_id, :created_at]

# Use add_reference with foreign_key: true
add_reference :items, :record, null: false, foreign_key: true
```
