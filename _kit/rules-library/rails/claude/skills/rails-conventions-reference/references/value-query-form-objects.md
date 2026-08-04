# Optional patterns — value, query, and form objects

> Use these only when the simpler approach (scope, model method, inline validation) is no
> longer sufficient. Do not introduce them preemptively.

### Value Objects

For concepts with equality by value, not identity. When a group of attributes always travels together and has behavior:

```ruby
# app/values/money.rb (or app/models/money.rb)
class Money
  attr_reader :amount, :currency

  def initialize(amount, currency = 'RUB')
    @amount = BigDecimal(amount.to_s)
    @currency = currency
  end

  def +(other)
    raise 'Currency mismatch' unless currency == other.currency
    Money.new(amount + other.amount, currency)
  end

  def ==(other)
    amount == other.amount && currency == other.currency
  end
end
```

### Query Objects

For complex queries that go beyond a single scope. When a query needs multiple parameters or joins:

```ruby
# app/queries/record_search_query.rb
class RecordSearchQuery
  def initialize(scope = Record.all)
    @scope = scope
  end

  def call(filters)
    scope = @scope
    scope = scope.where(status: filters[:status]) if filters[:status]
    scope = scope.where('title ILIKE ?', "%#{filters[:q]}%") if filters[:q]
    scope = scope.where(created_at: filters[:from]..filters[:to]) if filters[:from]
    scope
  end
end
```

### Form Objects

For forms that span multiple models or need complex validation:

```ruby
# app/forms/registration_form.rb
class RegistrationForm
  include ActiveModel::Model

  attr_accessor :name, :email, :company_name

  validates :name, :email, :company_name, presence: true

  def save
    return false unless valid?

    ActiveRecord::Base.transaction do
      company = Company.create!(name: company_name)
      User.create!(name: name, email: email, company: company)
    end
  end
end
```
