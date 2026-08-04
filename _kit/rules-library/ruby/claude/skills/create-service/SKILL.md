---
name: create-service
description: >-
  Scaffold a service, form, policy, value, or query object following project patterns,
  structure, and naming.
  TRIGGER when the user wants to extract business logic into a service/command object or
  create a form/policy/value/query object. Does NOT modify existing app code beyond the new
  object.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Edit
---

# Create Service Object Skill

You are a senior Ruby/Rails developer. Generate a business logic object following project conventions defined in the `rails-business-logic` rule.

## 1. Parse Arguments

Parse `$ARGUMENTS` to determine:

- **Object name** (required): e.g., `OrderFulfiller`, `RegistrationForm`, `Orders::Creator`
- **`--type=` flag** (optional): `service` | `form` | `policy` | `value` | `query`. Default: `service`.

If the name contains `Form`, `Policy`, `Query`, or `Value` suffix and no `--type` is given, infer the type from the name.

## 2. Determine Target Directory and File Path

| Type | Directory | Example |
|------|-----------|---------|
| service | `app/services/` | `app/services/order_fulfiller.rb` |
| form | `app/forms/` | `app/forms/registration_form.rb` |
| policy | `app/policies/` | `app/policies/order_policy.rb` |
| value | `app/values/` | `app/values/money.rb` |
| query | `app/queries/` | `app/queries/overdue_orders_query.rb` |

For namespaced classes (e.g., `Orders::Creator`), create subdirectories: `app/services/orders/creator.rb`.

Convert CamelCase to snake_case for file names.

## 3. Check for Existing Patterns

Before generating, search the target directory for existing files to match the project's style:

- Check if there is a base class or shared module used by other objects of the same type.
- Match the style of existing objects (e.g., if services use `Result` objects, use them too).
- If an `ApplicationPolicy` base class exists, inherit from it for policy objects.

## 4. Generate the File

### Service Object

```ruby
# frozen_string_literal: true

class OrderFulfiller
  def initialize(order, notifier: OrderMailer)
    @order = order
    @notifier = notifier
  end

  def call
    ActiveRecord::Base.transaction do
      @order.update!(status: :fulfilled, fulfilled_at: Time.current)
    end

    @notifier.with(order: @order).fulfilled.deliver_later
    @order
  end
end
```

Key conventions:
- Named as a **noun** (not a verb): `OrderFulfiller`, not `FulfillOrder`
- Single `#call` method for simple services; multi-method facade for complex ones
- **Dependency injection** for collaborators (mailers, external clients, etc.)
- Wrap multi-model writes in `ActiveRecord::Base.transaction`
- Return a meaningful result: the record, a `Result` object, or similar
- Use `Time.current` / `Date.current`, never `Time.now`

For namespaced services:

```ruby
# frozen_string_literal: true

module Orders
  class Creator
    def initialize(user)
      @user = user
    end

    def call(params)
      ActiveRecord::Base.transaction do
        @user.orders.create!(params)
      end
    rescue ActiveRecord::RecordInvalid => e
      e.record
    end
  end
end
```

### Form Object

```ruby
# frozen_string_literal: true

class RegistrationForm
  include ActiveModel::Model
  include ActiveModel::Attributes

  attribute :name, :string
  attribute :email, :string
  attribute :company_name, :string

  validates :name, :email, :company_name, presence: true
  validates :email, format: { with: URI::MailTo::EMAIL_REGEXP }

  def save
    return false unless valid?

    ActiveRecord::Base.transaction do
      company = Company.create!(name: company_name)
      User.create!(name:, email:, company:)
    end
  rescue ActiveRecord::RecordInvalid => e
    errors.merge!(e.record.errors)
    false
  end
end
```

Key conventions:
- `include ActiveModel::Model` and `include ActiveModel::Attributes`
- Declare attributes with types
- Validations before `#save` / `#submit`
- `#save` returns `false` on failure (like ActiveRecord)
- Wrap multi-model writes in transaction
- Merge record errors on failure for user-friendly messages

### Policy Object

```ruby
# frozen_string_literal: true

class OrderPolicy < ApplicationPolicy
  def show?
    owner? || user.admin?
  end

  def update?
    owner? && record.editable?
  end

  def destroy?
    user.admin?
  end

  private

  def owner?
    record.user_id == user.id
  end
end
```

Key conventions:
- Inherit from `ApplicationPolicy` if it exists; otherwise create a standalone class with `attr_reader :user, :record` and an initializer
- Methods return **boolean** values
- Method names end with `?` and match controller actions: `show?`, `create?`, `update?`, `destroy?`
- Takes `user` and `record` in constructor
- Private helper methods for shared predicates (`owner?`, `admin?`)

### Value Object

```ruby
# frozen_string_literal: true

Money = Data.define(:amount, :currency) do
  def initialize(amount:, currency: 'USD')
    super(amount: BigDecimal(amount.to_s), currency:)
  end

  def +(other)
    raise ArgumentError, 'Currency mismatch' unless currency == other.currency

    Money.new(amount: amount + other.amount, currency:)
  end

  def to_s
    "#{currency} #{format('%.2f', amount)}"
  end
end
```

Key conventions:
- Use `Data.define` (Ruby 3.2+) -- immutable by default
- Equality is by value (built into `Data.define`)
- No setters, no mutation
- Override `initialize` for defaults or coercion
- Add domain-specific methods (arithmetic, formatting)

### Query Object

```ruby
# frozen_string_literal: true

class OverdueOrdersQuery
  def initialize(scope = Order.all)
    @scope = scope
  end

  def call(grace_period: 30.days)
    @scope
      .where(status: :placed)
      .where(placed_at: ...grace_period.ago)
      .where(paid_at: nil)
      .includes(:customer)
      .order(placed_at: :asc)
  end
end
```

Key conventions:
- Takes a relation (default `Model.all`), returns a relation
- Composable: `OverdueOrdersQuery.new(company.orders).call`
- Named with `Query` suffix
- Single `#call` method with keyword arguments for parameters
- Use `includes` / `preload` for eager loading when appropriate

## 5. Post-Generation

- Confirm the file was created and show its path.
- If a namespaced module directory was created, mention it.
- Do NOT create test files unless explicitly asked.
- Do NOT auto-run any commands.
