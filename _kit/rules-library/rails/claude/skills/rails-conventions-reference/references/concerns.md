# Optional patterns — custom validators and concerns

> Use these only when the simpler approach (scope, model method, inline validation) is no
> longer sufficient. Do not introduce them preemptively.

### Custom Validators

For reusable validation logic that applies across multiple models:

```ruby
# app/validators/future_date_validator.rb
class FutureDateValidator < ActiveModel::EachValidator
  def validate_each(record, attribute, value)
    return if value.blank?

    if value <= Date.current
      record.errors.add(attribute, :must_be_in_future)
    end
  end
end

# Usage in model
validates :start_date, future_date: true
```

### Concerns — Focused Traits

Each concern should represent a single, cohesive behavior. If a concern grows beyond ~50 lines, consider whether it's doing too much.

```ruby
# GOOD — focused concern
module Archivable
  extend ActiveSupport::Concern

  included do
    scope :archived, -> { where.not(archived_at: nil) }
    scope :active, -> { where(archived_at: nil) }
  end

  def archive!
    update!(archived_at: Time.current)
  end

  def archived?
    archived_at.present?
  end
end

# BAD — dumping ground concern with unrelated methods
module Utilities
  # ... 200 lines of random helper methods
end
```
