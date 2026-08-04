# Rails models — worked examples

Companion reference to the `rails-models` rule; loaded on demand.

---

## 1. Model File Structure

Follow a canonical ordering inside every model:

```ruby
class Order < ApplicationRecord
  # 1. extend / include
  include Archivable
  include Trackable

  # 2. Constants
  MAX_LINE_ITEMS = 50
  EXPEDITED_THRESHOLD = Money.new(500_00, :usd)

  # 3. Attribute overrides (store, serialize, attribute)
  attribute :metadata, :jsonb, default: -> { {} }
  store_accessor :settings, :notify_on_ship, :gift_wrap

  # 4. Enums — always explicit integers
  enum :status, { cart: 0, placed: 1, paid: 2, shipped: 3, delivered: 4, cancelled: 5 }
  enum :priority, { standard: 0, expedited: 1 }, prefix: true

  # 5. Associations
  belongs_to :customer
  belongs_to :coupon, optional: true
  has_many :line_items, dependent: :destroy, inverse_of: :order
  has_many :products, through: :line_items
  has_one :shipment, dependent: :destroy

  # 6. Delegations
  delegate :full_name, :email, to: :customer, prefix: true

  # 7. Validations
  validates :status, presence: true
  validates :total_cents, numericality: { greater_than_or_equal_to: 0 }
  validates :line_items, length: { maximum: MAX_LINE_ITEMS }

  # 8. Scopes
  scope :active, -> { where.not(status: :cancelled) }
  scope :recent, -> { order(created_at: :desc) }
  scope :placed_after, ->(date) { where(placed_at: date..) }

  # 9. Callbacks (sparingly)
  before_validation :set_slug, on: :create
  after_commit :enqueue_confirmation, on: :create

  # 10. Class methods
  def self.total_revenue
    paid.sum(:total_cents)
  end

  # 11. Instance methods
  def expedited?
    total_cents >= EXPEDITED_THRESHOLD.cents
  end

  private

  def set_slug
    self.slug ||= "ORD-#{SecureRandom.alphanumeric(8).upcase}"
  end

  def enqueue_confirmation
    OrderConfirmationJob.perform_later(id)
  end
end
```

**Why this order:** Declarations paint what the model IS (schema, relationships, constraints) before what it DOES (methods).

---

## 2. Associations

### inverse_of

Rails auto-detects `inverse_of` for simple pairs. You MUST specify it when auto-detection fails:

```ruby
# GOOD — MUST specify: through, foreign_key, polymorphic
has_many :authored_posts, class_name: 'Post',
                          foreign_key: :author_id,
                          inverse_of: :author

has_many :comments, as: :commentable, inverse_of: :commentable
has_many :tags, through: :taggings, inverse_of: :articles
```

**Why:** Without correct `inverse_of`, Rails creates separate in-memory copies. Parent validation on child save uses a stale copy.

### dependent: options

| Option | Behavior | Use when |
|--------|----------|----------|
| `:destroy` | Calls `destroy` on each child (runs callbacks) | Children have own callbacks/dependents |
| `:delete_all` | SQL DELETE, no callbacks | Performance-critical, simple children |
| `:nullify` | Sets FK to NULL | Children can exist independently |
| `:restrict_with_error` | Prevents delete, adds error | Soft protection with user-friendly message |
| `:restrict_with_exception` | Prevents delete, raises | Hard protection in jobs/APIs |

**Rule:** Every `has_many` and `has_one` MUST declare `dependent:`. Omitting it leaves orphan records.

### counter_cache and touch

```ruby
class Comment < ApplicationRecord
  belongs_to :post, counter_cache: true  # reads comments_count column, no COUNT(*)
  belongs_to :post, touch: true          # bumps post.updated_at for cache invalidation
end
```

### Polymorphic Associations

```ruby
class Comment < ApplicationRecord
  belongs_to :commentable, polymorphic: true
end
class Post < ApplicationRecord
  has_many :comments, as: :commentable, dependent: :destroy
end
```

**Gotchas:** No DB-level FK constraint; always add composite index on `[commentable_type, commentable_id]`; `commentable_type` stores class name — renames require data migration.

### STI (Single Table Inheritance)

**When to use:** All subtypes share the same columns (differ by 1-2 nullable at most).

**When to avoid:** Subtypes need different columns — a table full of NULLs is a smell. Use separate tables or polymorphic instead.

```ruby
# BAD — STI with divergent schemas (most columns NULL per subtype)
class Payment < ApplicationRecord
  # columns: type, amount, card_number, bank_name, crypto_wallet_address...
end

# GOOD — separate tables or polymorphic for divergent schemas
class Payment < ApplicationRecord
  belongs_to :payable, polymorphic: true
end
```

---

## 3. Validations

### Model Validation vs DB Constraint

Use BOTH. DB constraints are the safety net; model validations give user-friendly errors.

| DB constraint | Model validation | Why both |
|---------------|------------------|----------|
| `NOT NULL` | `validates :name, presence: true` | DB catches race conditions; model gives friendly error |
| `UNIQUE index` | `validates :email, uniqueness: true` | DB catches races; model gives error before hitting DB |
| `CHECK (amount >= 0)` | `validates :amount, numericality: { >= 0 }` | DB is safety net; model catches early |
| Foreign key | `belongs_to :user` (validates by default) | DB prevents orphans; model gives actionable error |

**Warning — uniqueness race condition:** Model validation alone is NOT enough. Always pair with a unique DB index. Handle `ActiveRecord::RecordNotUnique` for the race case.

### Conditional Validations

```ruby
# GOOD — method reference, readable and testable
validates :billing_address, presence: true, if: :requires_billing?
validates :ship_by_date, presence: true, unless: :digital_product?

# BAD — inline proc for complex logic
validates :billing_address, presence: true,
          if: -> { status.in?(%w[paid processing]) && !digital? && region != 'exempt' }
```

### validates_associated

Only declare on ONE side (typically the parent). Both sides declaring it causes infinite validation loops.

### Uniqueness with Scope

```ruby
validates :email, uniqueness: { scope: :account_id, message: 'already taken for this account' }
# Always pair with: add_index :users, [:account_id, :email], unique: true
```

### Custom Validators

```ruby
# app/validators/url_validator.rb
class UrlValidator < ActiveModel::EachValidator
  def validate_each(record, attribute, value)
    return if value.blank?
    unless value.match?(%r{\Ahttps?://[^\s]+\z})
      record.errors.add(attribute, options[:message] || 'is not a valid URL')
    end
  end
end

# Usage: validates :website, url: true
```

---

## 4. Enums

```ruby
# GOOD — Rails 7+ syntax, explicit integers
enum :status, { draft: 0, published: 1, archived: 2 }
enum :role, { member: 0, admin: 1, owner: 2 }, prefix: true

# BAD — old syntax (pre Rails 7)
enum status: { draft: 0, published: 1, archived: 2 }

# BAD — array form, position-dependent
enum :priority, [:low, :medium, :high, :critical]
```

**Why explicit integers:** Inserting new values between existing ones does not shift mappings or corrupt data:

```ruby
# Safe addition — :urgent gets 4, :critical stays 3
enum :priority, { low: 0, medium: 1, high: 2, urgent: 4, critical: 3 }
```

Use `prefix:` / `suffix:` when value names collide across enums:

```ruby
enum :status, { active: 0, inactive: 1 }, prefix: true
enum :subscription, { active: 0, expired: 1 }, prefix: true

user.status_active?        # no collision
user.subscription_active?
User.status_active         # scope
```

Querying: `Article.published` (scope), `article.published?` (predicate), `article.published!` (update).

---

## 5. normalizes (Rails 7.1+)

```ruby
# GOOD — declarative normalization
normalizes :email, with: ->(email) { email.strip.downcase }
normalizes :phone, with: ->(phone) { phone.gsub(/\D/, '') }

# BAD — imperative callback
before_validation :normalize_email
def normalize_email
  self.email = email&.strip&.downcase
end
```

**Why:** `normalizes` applies on assignment, in finders (`find_by`), and in uniqueness validations. Callbacks only run on save — leaving gaps in queries and comparisons.

---

## 6. strict_loading

```ruby
# Per-association
has_many :comments, strict_loading: true

# Per-query
User.strict_loading.includes(:posts)

# Per-record
user = User.find(1)
user.strict_loading!

# Global in development/test
# config/environments/development.rb
config.active_record.strict_loading_by_default = true
```

**Why:** Raises `ActiveRecord::StrictLoadingViolationError` on lazy loading — catches N+1 before production. Fix by adding `includes`, `preload`, or `eager_load`.

---

## 7. Callbacks

| Acceptable callbacks | Avoid callbacks for |
|---|---|
| Setting defaults (`before_validation`) | Sending emails / notifications |
| Generating slugs, tokens on create | Touching external services / APIs |
| Maintaining derived data within same model | Creating / modifying other models |
| Normalizing data (prefer `normalizes`) | Complex business logic orchestration |
| `after_commit` for cache invalidation | Enqueuing jobs (use `after_commit` only) |

```ruby
# GOOD — data consistency within model
before_validation :set_default_currency, on: :create

# BAD — hidden side effects
after_save :send_welcome_email
after_save :update_analytics_dashboard
after_save :sync_to_elasticsearch
```

### after_commit vs after_save

```ruby
# BAD — job may execute before transaction commits, finding stale/missing data
after_save :enqueue_processing_job

# GOOD — guaranteed committed to DB
after_commit :enqueue_processing_job, on: :create
```

**Why:** `after_save` fires inside the transaction. A background job on a separate connection may not see the uncommitted record. `after_commit` fires only after successful commit.

If you have more than 2-3 callbacks, the model is doing too much — extract to a service object (see `ruby-oop.md`, section 13).

---

## 8. Scopes

```ruby
# GOOD — chainable, descriptive
scope :active, -> { where(status: :active) }
scope :recent, -> { order(created_at: :desc) }
scope :by_author, ->(author) { where(author:) }

# Chain freely:
Article.active.recent.by_author(user)

# BAD — class method returning array breaks chaining
def self.active
  all.select(&:active?)  # loads ALL records into memory, returns Array
end
```

When to use class method instead of scope — conditional logic or early returns:

```ruby
def self.search(query)
  return all if query.blank?
  where('title ILIKE ?', "%#{sanitize_sql_like(query)}%")
end
```

### Why default_scope Is Dangerous

```ruby
# BAD — default_scope causes surprises everywhere
default_scope { where(active: true) }
# Affects new records (sets defaults), joins (unexpected WHERE),
# count/exists?, and is hard to override (unscoped removes ALL scopes).

# GOOD — explicit named scope
scope :active, -> { where(active: true) }
```

---

## 9. Concerns

```ruby
# GOOD — focused, cohesive trait (~50 lines max)
# app/models/concerns/archivable.rb
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

# BAD — dumping ground concern
module Utilities  # vague name, unrelated methods
  extend ActiveSupport::Concern
  # 200 lines of random helpers...
end
```

**Rules:**
- Name after the behavior: `Archivable`, `Sluggable`, `Trackable`, `Publishable`
- Keep under ~50 lines; one concern = one cohesive behavior
- If it grows beyond 50 lines, extract to a service or separate model
- Avoid concerns that depend on other concerns (implicit coupling)
- Concerns are not a substitute for domain modeling — see `ruby-oop.md` (SRP, composition)

---

## 10. Query Patterns

### Eager Loading

```ruby
# BAD — N+1
posts = Post.all
posts.each { |p| p.author.name }

# GOOD
posts = Post.includes(:author)
```

| Method | Strategy | Use when |
|--------|----------|----------|
| `includes` | Rails chooses | Default choice |
| `preload` | Separate queries | Many associations, avoid huge JOIN |
| `eager_load` | LEFT OUTER JOIN | Need to filter/order by association columns |

### select, pluck, find_each

```ruby
# GOOD — pluck for raw values (skips AR instantiation)
emails = User.active.pluck(:email)

# GOOD — select to limit loaded columns
users = User.select(:id, :name, :email).active

# BAD — loading full objects for one field
emails = User.active.map(&:email)

# GOOD — batch processing, constant memory
User.active.find_each(batch_size: 500) { |u| ExportJob.perform_later(u.id) }

# BAD — loads ALL records at once
User.active.each { |u| ExportJob.perform_later(u.id) }
```

### Merge for Cross-Model Scope Composition

```ruby
Post.joins(:comments).merge(Comment.approved).merge(Comment.recent)
```

---

## 11. Data Integrity Patterns

### Transactions

```ruby
ActiveRecord::Base.transaction do
  order.update!(status: :paid)
  payment.update!(confirmed_at: Time.current)
  inventory.decrement!(:quantity, order.quantity)
end
# All succeed or all roll back

# Pessimistic locking for critical records
account.with_lock do
  account.balance -= amount
  account.save!
end
```

### Migration Safety

```ruby
class CreateOrders < ActiveRecord::Migration[8.0]
  def change
    create_table :orders do |t|
      t.references :customer, null: false, foreign_key: true
      t.string :slug, null: false
      t.integer :status, null: false, default: 0
      t.integer :total_cents, null: false, default: 0
      t.timestamps
    end
    add_index :orders, :slug, unique: true
    add_index :orders, :status
  end
end
```

**Production rules:** Add NOT NULL with a default or backfill first. Add indexes concurrently on large tables (`algorithm: :concurrently`). Never rename columns in one step. Always add FK constraints for `belongs_to`.

---

## 12. Encrypted Attributes (Rails 7+)

```ruby
class User < ApplicationRecord
  encrypts :email, deterministic: true  # allows find_by, where
  encrypts :ssn                          # non-deterministic, more secure, no querying
end
```

- **Deterministic:** same plaintext = same ciphertext — enables queries but reveals value equality
- **Non-deterministic:** more secure but cannot be used in `find_by` or `where`

---

## 13. Common Anti-Patterns

### Fat Model

```ruby
# BAD — model does everything
class Order < ApplicationRecord
  def process!
    validate_inventory! && charge_payment! && send_email! && sync_warehouse!
  end
end

# GOOD — model handles its data; services handle orchestration
class Order < ApplicationRecord
  def place!
    update!(status: :placed, placed_at: Time.current)
  end
end

class OrderPlacer
  def initialize(order) = @order = order

  def call
    @order.place!
    PaymentCharger.new(@order).call
    OrderConfirmationJob.perform_later(@order.id)
  end
end
```

### Business Logic in Controllers

```ruby
# BAD — business decisions in controller
def create
  @order = Order.new(order_params)
  @order.status = calculate_initial_status(@order)
  @order.discount = @order.total > 1000 ? @order.total * 0.1 : 0
  @order.save
end

# GOOD — controller coordinates, business logic in model/service
def create
  @order = OrderCreator.new(current_user).call(order_params)
  if @order.persisted?
    redirect_to @order, notice: t('.success')
  else
    render :new, status: :unprocessable_entity
  end
end
```

### Query Logic in Controllers

```ruby
# BAD — raw query in controller
@orders = Order.where(status: :active).where('created_at > ?', 30.days.ago)
               .includes(:customer).order(created_at: :desc)

# GOOD — encapsulate in scopes
@orders = Order.active.recent.includes(:customer)
```

When you find more than 3 callbacks, the model is accumulating responsibilities — extract to service objects (see `ruby-oop.md`).

---

## 14. Testing Models

When tests are requested, focus on:

| Test | Skip |
|------|------|
| Custom validations and edge cases | Default Rails validations (presence, numericality) |
| Scope correctness (returns right records) | Association declarations |
| Callback side effects (if any) | Enum method generation |
| Instance/class methods with logic | Simple delegations, `normalizes` |

```ruby
# GOOD — test custom logic, not Rails internals
RSpec.describe Order do
  describe '#expedited?' do
    it 'returns true when total exceeds threshold' do
      order = build(:order, total_cents: 600_00)
      expect(order).to be_expedited
    end
  end

  describe '.total_revenue' do
    it 'sums total_cents for paid orders only' do
      create(:order, status: :paid, total_cents: 100_00)
      create(:order, status: :paid, total_cents: 200_00)
      create(:order, status: :cancelled, total_cents: 500_00)
      expect(Order.total_revenue).to eq(300_00)
    end
  end
end

# BAD — testing Rails itself
it 'validates presence of status' do
  order = Order.new(status: nil)
  expect(order).not_to be_valid
end
```

For full testing conventions, see `rspec-testing.md`.
