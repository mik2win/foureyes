# Rails background jobs — worked examples

Companion reference to the `rails-background-jobs` rule; loaded on demand.

---

## 1. ActiveJob Interface

```ruby
# perform_later — enqueue for async execution (default)
OrderProcessingJob.perform_later(order.id)

# perform_now — execute inline, same process (tests or from other jobs)
OrderProcessingJob.perform_now(order.id)

# set — configure queue, delay, priority
OrderProcessingJob.set(wait: 5.minutes).perform_later(order.id)
OrderProcessingJob.set(queue: :critical).perform_later(order.id)
OrderProcessingJob.set(wait_until: Date.tomorrow.noon).perform_later(order.id)
```

### Argument Serialization

Only pass **primitives** and **GlobalID-capable objects** (ActiveRecord models). Supported: `String`, `Integer`, `Float`, `BigDecimal`, `NilClass`, `TrueClass`, `FalseClass`, `Symbol`, `Date`, `Time`, `Hash`/`Array` (with supported values), `ActiveRecord::Base` (via GlobalID).

```ruby
# GOOD — pass ID, re-fetch in job
class OrderProcessingJob < ApplicationJob
  queue_as :default

  def perform(order_id)
    order = Order.find_by(id: order_id)
    return unless order  # guard against deleted records

    OrderProcessor.new(order).call
  end
end

OrderProcessingJob.perform_later(order.id)

# GOOD — GlobalID auto-serialization (Rails handles find)
class OrderProcessingJob < ApplicationJob
  def perform(order)
    OrderProcessor.new(order).call
  rescue ActiveJob::DeserializationError
    # record was deleted between enqueue and execution
  end
end

OrderProcessingJob.perform_later(order)  # serializes as gid://app/Order/42

# BAD — passing complex objects
OrderProcessingJob.perform_later(order.attributes)  # stale data
OrderProcessingJob.perform_later(order.to_json)      # no type safety
```

**Why only pass IDs/primitives:** A job may run minutes later. The object may have changed or been deleted. Re-fetching guarantees fresh data.

---

## 2. Solid Queue (Rails 8 Default)

Database-backed queue. No Redis dependency.

```ruby
# config/queue.yml
default: &default
  dispatchers:
    - polling_interval: 1
      batch_size: 500
  workers:
    - queues: "*"
      threads: 3
      processes: 1
      polling_interval: 0.1

production:
  <<: *default
  workers:
    - queues: "critical"
      threads: 5
      processes: 2
      polling_interval: 0.1
    - queues: "default,mailers"
      threads: 3
      processes: 2
    - queues: "low"
      threads: 2
      processes: 1

# config/recurring.yml
production:
  cleanup_old_sessions:
    class: CleanupSessionsJob
    schedule: every day at 3am
  generate_daily_report:
    class: DailyReportJob
    schedule: every day at 6am
```

### Concurrency Controls

```ruby
class OrderProcessingJob < ApplicationJob
  limits_concurrency to: 1, key: ->(order_id) { "order_#{order_id}" }

  def perform(order_id)
    order = Order.find_by(id: order_id)
    return unless order

    OrderProcessor.new(order).call
  end
end
```

**Why Solid Queue over Sidekiq:** No Redis dependency. Database-backed (transactional reliability). Default in Rails 8. Use Sidekiq only if you need >10,000 jobs/minute or its specific features (batches, rate limiting).

---

## 3. Job Continuations (Large Batch Processing)

Split large work into continuations instead of one long job.

```ruby
# BAD — single job runs for hours, blocks queue, no recovery on failure
class LargeExportJob < ApplicationJob
  def perform(user_id)
    user = User.find(user_id)
    user.orders.each { |order| export(order) }  # 100k orders = hours
  end
end

# GOOD — cursor-based continuation, each chunk is a separate job
class LargeExportJob < ApplicationJob
  limits_concurrency to: 1, key: ->(user_id, **) { "export_#{user_id}" }

  def perform(user_id, cursor: nil)
    user = User.find_by(id: user_id)
    return unless user

    batch = user.orders
                .then { |scope| cursor ? scope.where('id > ?', cursor) : scope }
                .order(:id)
                .limit(1000)

    batch.each { |order| export(order) }

    if batch.size == 1000
      self.class.perform_later(user_id, cursor: batch.last.id)  # continue
    end
  end
end
```

**Why:** Each chunk is a separate job (bounded memory/time). Failed chunks retry independently. The queue stays responsive between chunks.

---

## 4. Idempotency

Every job MUST be safe to run multiple times (retries, worker restarts, duplicate enqueuing).

```ruby
# GOOD — idempotent (safe to retry)
class ChargeOrderJob < ApplicationJob
  def perform(order_id)
    order = Order.find_by(id: order_id)
    return unless order
    return if order.charged?  # already processed

    ActiveRecord::Base.transaction do
      charge = PaymentProcessor.new(order).call
      order.update!(charged_at: Time.current, payment_id: charge.id)
    end
  end
end

# GOOD — idempotency key with unique constraint
class SendWebhookJob < ApplicationJob
  def perform(event_id)
    event = Event.find_by(id: event_id)
    return unless event

    WebhookDelivery.create!(event: event, delivered_at: Time.current)
    WebhookSender.new(event).call
  rescue ActiveRecord::RecordNotUnique
    # already delivered — safe to ignore
  end
end

# BAD — not idempotent (double-charges on retry)
class ChargeOrderJob < ApplicationJob
  def perform(order_id)
    order = Order.find(order_id)
    PaymentProcessor.new(order).call  # no guard, charges every time
  end
end
```

---

## 5. Error Handling in Jobs

```ruby
class ImportJob < ApplicationJob
  retry_on Net::OpenTimeout, wait: :polynomially_longer, attempts: 5
  retry_on ActiveRecord::Deadlocked, wait: 5.seconds, attempts: 3
  discard_on ActiveJob::DeserializationError  # record deleted

  # Custom discard with error tracking
  discard_on Import::InvalidFormatError do |job, error|
    import = Import.find_by(id: job.arguments.first)
    import&.update!(status: :failed, error_message: error.message)
    Rails.error.report(error, context: { import_id: job.arguments.first })
  end

  def perform(import_id)
    import = Import.find(import_id)
    ImportProcessor.new(import).call
  rescue StandardError => e
    Rails.error.report(e, context: { import_id: import_id })
    raise  # re-raise for retry mechanism
  end
end

# Wait strategies
retry_on SomeError, wait: 5.seconds, attempts: 3           # fixed
retry_on SomeError, wait: :polynomially_longer, attempts: 5 # 3s, 18s, 83s...
retry_on SomeError, wait: ->(executions) { executions ** 2 + 2 }, attempts: 5
```

**Why `raise` after reporting:** ActiveJob's `retry_on` only triggers when the job raises. If you swallow the error, retries never fire.

---

## 6. ApplicationJob Base Class

```ruby
# BAD — no base error handling, every job must handle its own retries
class ApplicationJob < ActiveJob::Base
  # empty — each job reinvents error handling
end

# GOOD — centralized error handling and dead letter queue
class ApplicationJob < ActiveJob::Base
  retry_on ActiveRecord::Deadlocked, wait: 5.seconds, attempts: 3
  discard_on ActiveJob::DeserializationError

  # Dead letter queue — capture jobs that exhaust all retries
  retry_on StandardError, wait: :polynomially_longer, attempts: 5 do |job, error|
    FailedJob.create!(
      job_class: job.class.name, arguments: job.arguments.to_json,
      error_class: error.class.name, error_message: error.message,
      failed_at: Time.current
    )
    Rails.error.report(error, severity: :error, context: {
      job_class: job.class.name, arguments: job.arguments
    })
  end
end
```

---

## 7. ActionMailer

```ruby
# app/mailers/application_mailer.rb
class ApplicationMailer < ActionMailer::Base
  default from: 'noreply@example.com'
  layout 'mailer'
end

# app/mailers/order_mailer.rb
class OrderMailer < ApplicationMailer
  def confirmation
    @order = params[:order]
    @user = @order.user
    mail(
      to: @user.email,
      subject: t('.subject', order_number: @order.number)
    )
  end

  def shipped
    @order = params[:order]
    @tracking_url = params[:tracking_url]
    mail(to: @order.user.email)
  end
end

# GOOD — parameterized mailer (Rails 5.1+)
OrderMailer.with(order: order).confirmation.deliver_later
OrderMailer.with(order: order, tracking_url: url).shipped.deliver_later

# BAD — positional args (hard to extend, unclear)
OrderMailer.confirmation(order.id, order.user.email).deliver_later
```

**Why parameterized:** Adding a new parameter doesn't break existing callers. The `params` hash is self-documenting. Enables `before_action` filters on params.

### deliver_later vs deliver_now

```ruby
# GOOD — always deliver_later in production (enqueues via ActiveJob)
OrderMailer.with(order: order).confirmation.deliver_later

# OK — deliver_now only inside jobs (already async)
OrderMailer.with(order: order).confirmation.deliver_now

# BAD — deliver_now in controllers (blocks the request, 100ms-5s)
def create
  @order = Order.create!(order_params)
  OrderMailer.with(order: @order).confirmation.deliver_now  # slow!
  redirect_to @order
end
```

### I18n for Subjects

```yaml
en:
  order_mailer:
    confirmation:
      subject: "Order %{order_number} confirmed"
```

Use `t('.subject', order_number: @order.number)` in the mailer method -- Rails auto-scopes to `mailer/action`.

```ruby
# GOOD — eager loaded in mailer method
def confirmation
  @order = params[:order]
  @items = @order.line_items.includes(:product)
  mail(to: @order.user.email)
end

# BAD — lazy loading in view template (N+1 in email)
# <% @order.line_items.each do |item| %>
#   <%= item.product.name %>  <%# N+1 %>
# <% end %>
```

---

## 8. Mailer Previews

```ruby
# test/mailers/previews/order_mailer_preview.rb
class OrderMailerPreview < ActionMailer::Preview
  def confirmation
    order = Order.last || FactoryBot.create(:order)
    OrderMailer.with(order: order).confirmation
  end

  def shipped
    order = Order.where(status: :shipped).last || FactoryBot.create(:order, :shipped)
    OrderMailer.with(order: order, tracking_url: 'https://track.example.com/ABC123').shipped
  end
end
# Visit: http://localhost:3000/rails/mailers/order_mailer/confirmation
# Visit: http://localhost:3000/rails/mailers/order_mailer/shipped
```

---

## 9. Interceptors and Observers

```ruby
# Redirect all mail in staging to a safe address
class StagingMailInterceptor
  def self.delivering_email(message)
    message.to = ['staging-inbox@example.com']
    message.subject = "[STAGING] #{message.subject}"
  end
end

ActionMailer::Base.register_interceptor(StagingMailInterceptor) if Rails.env.staging?

# Log all sent emails for audit
class EmailAuditObserver
  def self.delivered_email(message)
    EmailLog.create!(to: message.to&.join(', '), subject: message.subject, sent_at: Time.current)
  end
end

ActionMailer::Base.register_observer(EmailAuditObserver)
```

---

## 10. Testing Jobs

```ruby
RSpec.describe OrderProcessingJob do
  it 'enqueues the job' do
    expect { described_class.perform_later(42) }
      .to have_enqueued_job(described_class).with(42).on_queue('default')
  end

  describe '#perform' do
    let(:order) { create(:order, status: :pending) }

    it 'processes the order' do
      described_class.perform_now(order.id)
      expect(order.reload.status).to eq('processed')
    end

    it 'does nothing when order is not found' do
      expect { described_class.perform_now(-1) }.not_to raise_error
    end

    it 'does nothing when already processed' do
      order.update!(status: :processed)
      described_class.perform_now(order.id)
      expect(order.reload.updated_at).to eq(order.updated_at)
    end
  end
end
```

---

## 11. Testing Mailers

```ruby
RSpec.describe OrderMailer do
  describe '#confirmation' do
    let(:order) { create(:order) }
    let(:mail) { described_class.with(order: order).confirmation }

    it 'sends to the correct recipient' do
      expect(mail.to).to eq([order.user.email])
    end

    it 'sets the correct subject' do
      expect(mail.subject).to eq("Order #{order.number} confirmed")
    end

    it 'renders the order details in the body' do
      expect(mail.body.encoded).to include(order.number)
    end
  end
end

# Test email enqueuing in integration
RSpec.describe OrderPlacementService do
  it 'enqueues confirmation email' do
    expect { described_class.new(order).call }
      .to have_enqueued_mail(OrderMailer, :confirmation)
      .with(params: { order: order }, args: [])
  end
end
```

---

## 12. Common Anti-Patterns

### Long-Running Jobs

```ruby
# BAD — single job runs for hours
User.find_each { |user| generate_report(user) }

# GOOD — fan out into per-user jobs
User.find_each { |user| ExportUserJob.perform_later(user.id) }
```

### Side Effects in Transactions

```ruby
# BAD — job enqueued inside transaction, may run before commit
ActiveRecord::Base.transaction do
  order.update!(status: :placed)
  OrderProcessingJob.perform_later(order.id)
end

# GOOD — enqueue after commit
ActiveRecord::Base.transaction do
  order.update!(status: :placed)
end
OrderProcessingJob.perform_later(order.id)

# GOOD — use after_commit callback
class Order < ApplicationRecord
  after_commit :enqueue_processing, on: :update, if: :saved_change_to_status?

  private

  def enqueue_processing
    OrderProcessingJob.perform_later(id) if status == 'placed'
  end
end
```

**Why:** With Redis-backed queues, the job may execute before the transaction commits. With Solid Queue (same DB), the job rolls back with the transaction -- safer, but after-commit remains best practice.

### Passing Too Much Data

```ruby
# BAD — large payload in the queue
ProcessDataJob.perform_later(huge_hash)  # 10MB hash serialized to JSON

# GOOD — store data in DB/storage, pass a reference
ProcessDataJob.perform_later(upload_id)
```
