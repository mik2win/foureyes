# Model structure order

Follow this order inside every model file:

```ruby
class Record < ApplicationRecord
  # 1. extend / include
  include Trackable

  # 2. Constants
  STATUSES = %w[active inactive].freeze

  # 3. Attribute overrides
  attribute :kind, :string, default: 'default'

  # 4. Enums (always with explicit integer values)
  enum :status, { draft: 0, active: 1, archived: 2 }

  # 5. Associations
  belongs_to :user
  has_many :items, dependent: :destroy

  # 6. Delegations
  delegate :name, to: :user, prefix: true

  # 7. Validations
  validates :title, presence: true

  # 8. Scopes
  scope :active, -> { where(status: :active) }
  scope :by_title, -> { order(:title) }

  # 9. Callbacks (use sparingly — see below)
  after_commit :recalculate, on: :update

  # 10. Class methods
  def self.search(query)
    where('title ILIKE ?', "%#{query}%")
  end

  # 11. Instance methods
  def total_amount
    items.sum(:amount)
  end
end
```

### Enums — explicit integer values

```ruby
# GOOD — positional syntax (the keyword form was removed in Rails 8)
enum :status, { draft: 0, active: 1, archived: 2 }
enum :kind, { standard: 0, premium: 1 }

# BAD — order-dependent, fragile
enum :status, %i[draft active archived]
```
