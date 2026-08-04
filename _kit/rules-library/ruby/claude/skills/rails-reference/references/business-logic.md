# Rails business logic (services/forms/policies) — worked examples

Companion reference to the `rails-business-logic` rule; loaded on demand.

---

## 1. When to Extract (Decision Guide)

### Where Logic Should Live

Data logic in the model, orchestration (multi-model coordination, side effects, external calls) in a service. Never put orchestration in a model (god model) or controller (fat controller).

```ruby
# GOOD — data logic in model
class Order < ApplicationRecord
  def total = items.sum(:amount)
end

# GOOD — orchestration in service
class OrderFulfiller
  def initialize(order) = @order = order

  def call
    ActiveRecord::Base.transaction do
      @order.update!(status: :fulfilled)
      @order.items.each { |item| InventoryManager.new(item).decrement! }
    end
    OrderMailer.with(order: @order).fulfilled.deliver_later
  end
end
```

---

## 2. Service Objects in Rails Context

### Transactions & Error Propagation

Wrap multi-model writes in `ActiveRecord::Base.transaction`. Return meaningful results on failure (e.g. the invalid record, which carries its errors).

```ruby
class OrderCreator
  def initialize(user) = @user = user

  def call(params)
    ActiveRecord::Base.transaction do
      order = @user.orders.create!(params)
      order.items.each { |item| InventoryManager.new(item).reserve! }
      order
    end
  rescue ActiveRecord::RecordInvalid => e
    e.record  # invalid record, has errors attached
  end
end

# Controller — clean delegation
def create
  @order = OrderCreator.new(current_user).call(order_params)
  if @order.persisted?
    redirect_to @order, notice: t('.created')
  else
    render :new, status: :unprocessable_entity
  end
end
```

### Module Organization

Group related services under a namespace mirroring the domain. Avoid flat, verbose `XxxService` names.

```ruby
# app/services/orders/creator.rb, orders/fulfiller.rb
module Orders
  class Creator;   def call(params); end; end
  class Fulfiller; def call;         end; end
end

Orders::Creator.new(current_user).call(order_params)  # reads naturally
```

### Dependency Injection

Pass collaborators in (see `ruby-oop.md` section 2). Common injectables in Rails: mailers, job classes, external clients.

```ruby
class OrderFulfiller
  def initialize(order, notifier: OrderMailer, tracker: AnalyticsTracker)
    @order, @notifier, @tracker = order, notifier, tracker
  end

  def call
    ActiveRecord::Base.transaction { @order.update!(status: :fulfilled) }
    @notifier.with(order: @order).fulfilled.deliver_later
    @tracker.track('order_fulfilled', order_id: @order.id)
  end
end

# Tests — swap dependencies
OrderFulfiller.new(order, notifier: FakeMailer, tracker: NullTracker).call
```

---

## 3. Form Objects

Use when a form spans multiple models, needs cross-model validation, or when `accepts_nested_attributes_for` creates tight coupling.

```ruby
# app/forms/registration_form.rb
class RegistrationForm
  include ActiveModel::Model
  include ActiveModel::Attributes

  attribute :name, :string
  attribute :email, :string
  attribute :company_name, :string
  attribute :plan, :string, default: 'free'

  validates :name, :email, :company_name, presence: true
  validates :email, format: { with: URI::MailTo::EMAIL_REGEXP }
  validates :plan, inclusion: { in: %w[free pro enterprise] }

  def save
    return false unless valid?

    ActiveRecord::Base.transaction do
      company = Company.create!(name: company_name)
      User.create!(name:, email:, company:, plan:)
    end
  rescue ActiveRecord::RecordInvalid => e
    errors.merge!(e.record.errors)  # surface model errors on the form
    false
  end
end
```

Controller treats it like a model: `RegistrationForm.new(params)`, `if @form.save`, `form_with model: @form`.

**Why:** replaces `accepts_nested_attributes_for` (tight coupling); single place for cross-model validation; works with `form_with model: @form`; testable as a PORO.

### Multi-Step Wizard

One form object per step (each a normal `ActiveModel::Model` PORO with its own attributes/validations). Controller validates the step, merges its data into the session, then advances:

```ruby
def submit_step_one
  @form = Onboarding::StepOneForm.new(step_one_params)
  if @form.valid?
    session[:onboarding] = (session[:onboarding] || {}).merge(step_one_params.to_h)
    redirect_to onboarding_step_two_path
  else
    render :step_one, status: :unprocessable_entity
  end
end
```

---

## 4. Result Objects

Return structured results from services. Don't raise exceptions for expected business failures, and don't return bare booleans that lose error context.

```ruby
Result = Data.define(:success?, :value, :error)  # Ruby 3.2+

class PaymentProcessor
  def call(order)
    charge = gateway.charge(order.total)
    order.update!(payment_id: charge.id, paid_at: Time.current)
    Result.new(success?: true, value: order, error: nil)
  rescue PaymentGateway::CardDeclined => e
    Result.new(success?: false, value: nil, error: e.message)
  rescue PaymentGateway::NetworkError => e
    Rails.error.report(e)
    Result.new(success?: false, value: nil, error: 'Payment service unavailable')
  end

  private

  def gateway = @gateway ||= PaymentGateway.new
end

# Controller — clear branching
result = PaymentProcessor.new.call(@order)
result.success? ? redirect_to(result.value) : (flash.now[:alert] = result.error)
```

**Anti-patterns:** raising `PaymentError` for an expected declined card (exceptions as flow control), and returning bare `false` (caller has no idea why it failed).

**Why:** explicit success/failure without exceptions for expected outcomes; carries error context (messages, codes); pattern-matchable with `case/in` (Ruby 3.0+); composable across services.

---

## 5. Presenters / Decorators

Extract view-specific logic from models and helpers. Use `SimpleDelegator` for transparent wrapping (all model methods remain available).

```ruby
# app/presenters/order_presenter.rb
class OrderPresenter < SimpleDelegator
  def status_badge
    case status.to_sym
    when :pending   then { text: 'Pending',   css: 'bg-yellow-100 text-yellow-800' }
    when :shipped   then { text: 'Shipped',   css: 'bg-blue-100 text-blue-800' }
    when :delivered then { text: 'Delivered', css: 'bg-green-100 text-green-800' }
    end
  end

  def formatted_total  = "$#{format('%.2f', total)}"
  def created_at_label = created_at.strftime('%b %d, %Y')
end

# Controller: @order = OrderPresenter.new(Order.find(params[:id]))
```

Keep display logic (e.g. `avatar_url`, `display_name`) out of the model — it's a view concern leaking in.

---

## 6. Value Objects

Immutable, identified by their attributes (not an ID). Use `Data.define` (Ruby 3.2+) for concise, frozen value objects.

```ruby
# app/values/money.rb
Money = Data.define(:amount, :currency) do
  def initialize(amount:, currency: 'USD')
    super(amount: BigDecimal(amount.to_s), currency:)
  end

  def +(other)
    raise ArgumentError, 'Currency mismatch' unless currency == other.currency
    Money.new(amount: amount + other.amount, currency:)
  end

  def to_s = "#{currency} #{format('%.2f', amount)}"
end

Money.new(amount: 29.99) + Money.new(amount: 2.40)  # => Money(amount: 32.39, ...)
```

### Custom ActiveRecord Attribute Type

Bridge value objects to columns: `cast` (input → VO), `serialize` (VO → DB), `deserialize` (DB → VO).

```ruby
# app/types/money_type.rb
class MoneyType < ActiveRecord::Type::Value
  def cast(value)
    case value
    when Money   then value
    when Hash    then Money.new(**value.symbolize_keys)
    when Numeric then Money.new(amount: value)
    end
  end

  def serialize(value)   = value&.amount&.to_f
  def deserialize(value) = Money.new(amount: value) if value
end

ActiveRecord::Type.register(:money, MoneyType)

class Order < ApplicationRecord
  attribute :total, :money
end
```

```ruby
# Address — another value object
Address = Data.define(:street, :city, :state, :zip, :country) do
  def initialize(street:, city:, state:, zip:, country: 'US') = super
  def one_line = "#{street}, #{city}, #{state} #{zip}"
end
```

---

## 7. Policy Objects

Encapsulate authorization rules. Keep controllers and models free of permission checks.

```ruby
# app/policies/application_policy.rb
class ApplicationPolicy
  attr_reader :user, :record
  def initialize(user, record) = (@user, @record = user, record)

  def index?   = false
  def show?    = false
  def create?  = false
  def update?  = false
  def destroy? = false
end

# app/policies/order_policy.rb
class OrderPolicy < ApplicationPolicy
  def show?    = owner? || user.admin?
  def update?  = owner? && record.editable?
  def cancel?  = owner? && record.cancellable?
  def destroy? = user.admin?

  private

  def owner? = record.user_id == user.id
end
```

### Controller Integration

```ruby
# app/controllers/concerns/authorization.rb
module Authorization
  extend ActiveSupport::Concern

  class NotAuthorizedError < StandardError; end

  included { rescue_from NotAuthorizedError, with: :deny_access }

  def authorize!(record, action = "#{action_name}?")
    policy = "#{record.class}Policy".constantize.new(current_user, record)
    raise NotAuthorizedError unless policy.public_send(action)
  end

  private

  def deny_access
    respond_to do |format|
      format.html { redirect_to root_path, alert: t('not_authorized') }
      format.json { head :forbidden }
    end
  end
end

# Controller: authorize!(@order) or authorize!(@order, :cancel?)
```

**Why:** authorization in one place per model; testable in isolation; easy to audit ("who can do what?"); composable with scopes for collection filtering.

---

## 8. Current Attributes

Thread-safe, request-scoped global state for cross-cutting concerns.

```ruby
# app/models/current.rb
class Current < ActiveSupport::CurrentAttributes
  attribute :user, :request_id, :ip_address

  resets { Time.zone = nil }

  def user=(user)
    super
    Time.zone = user&.time_zone
  end
end

# ApplicationController before_action sets Current.user / request_id / ip_address.
# Read anywhere: Current.user, Current.request_id
```

`Current` is for cross-cutting context, not business inputs. An audit concern reading `Current.user&.id` in `before_create`/`before_update` is fine. A service reading `Current.user` internally is a hidden dependency that's hard to test — pass `fulfilled_by:` in instead.

---

## 9. Domain Events with ActiveSupport::Notifications

Decouple core actions from side effects. The action publishes an event; subscribers react independently.

```ruby
# In service — publish
class OrderFulfiller
  def call
    ActiveRecord::Base.transaction do
      @order.update!(status: :fulfilled, fulfilled_at: Time.current)
    end
    ActiveSupport::Notifications.instrument('order.fulfilled', order: @order)
  end
end

# config/initializers/event_subscribers.rb — each concern independent
ActiveSupport::Notifications.subscribe('order.fulfilled') do |event|
  OrderMailer.with(order: event.payload[:order]).fulfilled.deliver_later
end
ActiveSupport::Notifications.subscribe('order.fulfilled') do |event|
  AnalyticsTracker.track('order_fulfilled', order_id: event.payload[:order].id)
end
```

Subscribers can be added/removed/modified without touching the publisher; the service stays focused on its primary responsibility.

Core logic that must succeed-or-roll-back together (e.g. `Order.create!` + `InventoryManager#reserve!`) belongs in a transaction with direct calls, not events.

---

## 10. Query Objects

Extract complex queries that span 3+ conditions, involve multiple joins, or appear in multiple places. See `rails-activerecord-queries.md` section 5 for fundamentals.

```ruby
# app/queries/overdue_orders_query.rb
class OverdueOrdersQuery
  def initialize(scope = Order.all) = @scope = scope

  def call(grace_period: 30.days)
    @scope
      .where(status: :placed)
      .where(placed_at: ...grace_period.ago)
      .where(paid_at: nil)
      .includes(:customer)
      .order(placed_at: :asc)
  end
end

# Composable with scopes
OverdueOrdersQuery.new.call
OverdueOrdersQuery.new(company.orders).call(grace_period: 14.days)
```

Aggregations work the same way — `group`/`select` for stats:

```ruby
class SalesSummaryQuery
  def initialize(scope = Order.all) = @scope = scope

  def call(period:)
    @scope.where(status: :paid).where(paid_at: period)
      .group("DATE_TRUNC('day', paid_at)")
      .select("DATE_TRUNC('day', paid_at) AS day",
              'SUM(total_cents) AS revenue', 'COUNT(*) AS order_count')
      .order('day')
  end
end
```

---

## 11. Interactors (Multi-Step Orchestration)

When a business operation has 3+ steps that must succeed or fail together, each complex enough to be its own service, use a single orchestrator.

```ruby
# app/interactors/place_order.rb
class PlaceOrder
  def initialize(user:, cart:, payment_method:)
    @user, @cart, @payment_method = user, cart, payment_method
  end

  def call
    ActiveRecord::Base.transaction do
      order = create_order
      reserve_inventory(order)
      charge_payment(order)
      order.update!(status: :placed, placed_at: Time.current)
      order
    end
  rescue InventoryError => e
    Result.new(success?: false, value: nil, error: "Item unavailable: #{e.message}")
  rescue PaymentError => e
    Result.new(success?: false, value: nil, error: "Payment failed: #{e.message}")
  end

  private

  def create_order
    @user.orders.create!(items: @cart.items.map { |i| { product_id: i.product_id, quantity: i.quantity } })
  end

  def reserve_inventory(order) = order.items.each { |i| InventoryManager.new(i).reserve! }
  def charge_payment(order)    = PaymentProcessor.new(gateway: PaymentGateway.new).call(order:, payment_method: @payment_method)
end
```

**Why a single orchestrator over chained services:** the transaction boundary is explicit, error handling is centralized, and the controller calls one object.

---

## 12. Callbacks vs Services (Decision Guide)

```ruby
# GOOD — callback for model's own data
class Order < ApplicationRecord
  before_validation :set_reference, on: :create

  private

  def set_reference = self.reference ||= "ORD-#{SecureRandom.alphanumeric(8).upcase}"
end
```

**Anti-pattern:** stacking side effects in callbacks (`after_commit :send_confirmation`, `:track_analytics`, `:notify_warehouse`...) — hidden, hard to test, hard to skip, and they fire even in tests/seeds/console. Put those in a service instead.

---

## 13. Testing Business Logic Objects

```ruby
# Service — assert state change + side effect
RSpec.describe OrderFulfiller do
  let(:order) { create(:order, status: :placed) }

  it 'fulfills and emails' do
    expect { described_class.new(order).call }
      .to have_enqueued_mail(OrderMailer, :fulfilled)
    expect(order.reload.status).to eq('fulfilled')
  end
end

# Policy — boolean per role, owner vs non-owner
RSpec.describe OrderPolicy do
  subject(:policy) { described_class.new(user, order) }
  let(:order) { create(:order, user: owner) }
  let(:owner) { create(:user) }

  context('as owner')     { let(:user) { owner };         it { expect(policy.update?).to be true  } }
  context('as non-owner') { let(:user) { create(:user) }; it { expect(policy.show?).to be false } }
end
```

---

## 14. Summary: Where Does It Go?

```
Reads/writes one model's own columns          → Model method
Shared by 2+ unrelated models                 → Concern (trait) or Service (orchestration)
Coordinates 2+ models in a transaction        → Service Object
Form touches multiple models                  → Form Object
View/display formatting                        → Presenter (model-specific) or Helper (stateless one-liner)
Decides who can do what                         → Policy Object
Concept with no ID, equality by value          → Value Object
Complex reusable query                          → Query Object (or scope if simple)
Side effect (email, analytics, webhook)        → Domain Event subscriber or background job
```
