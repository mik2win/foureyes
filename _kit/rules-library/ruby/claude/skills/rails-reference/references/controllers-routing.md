# Rails controllers & routing — worked examples

Companion reference to the `rails-controllers-routing` rule; loaded on demand.

---

## 1. Thin Controller Pattern

Structure: guard → execute → respond.

```ruby
# GOOD — thin controller, logic in service
class OrdersController < ApplicationController
  before_action :set_order, only: %i[show edit update destroy]

  def create
    @order = OrderCreator.new(current_user).call(order_params)
    if @order.persisted?
      redirect_to @order, notice: t('.success')
    else
      render :new, status: :unprocessable_entity
    end
  end

  def update
    if @order.update(order_params)
      redirect_to @order, notice: t('.updated')
    else
      render :edit, status: :unprocessable_entity
    end
  end

  private

  def set_order = @order = current_user.orders.find(params[:id])

  def order_params
    params.require(:order).permit(:title, :description, :status)
  end
end

# GOOD — multiple calls, but no business logic in controller
def create
  @order = OrderCreator.new(current_user).call(order_params)
  if @order.persisted?
    WarehouseNotifier.new(@order).notify
    AnalyticsTracker.track('order_created', order_id: @order.id)
    redirect_to @order, notice: t('.success')
  else
    render :new, status: :unprocessable_entity
  end
end

# BAD — business logic inline (calculations, state management, conditions on domain data)
def create
  @order = Order.new(order_params)
  @order.user = current_user
  @order.status = :pending
  @order.total = params[:items].sum { |i| Item.find(i[:id]).price * i[:qty] }
  if @order.total > 1000
    @order.discount = @order.total * 0.1  # business rule in controller
  end
  @order.save
  AdminMailer.new_large_order(@order).deliver_now if @order.total > 500  # another business rule
end
```

**The line:** calling `OrderCreator` + `WarehouseNotifier` + `AnalyticsTracker` from a controller is fine — the controller coordinates. Writing `if order.total > 1000 then discount = ...` is not — that's a business decision that belongs in a service or model.

Action order convention: index, show, new, create, edit, update, destroy — then `private`. Matches RESTful lifecycle; every developer knows where to find each action.

---

## 2. Strong Parameters

```ruby
# Basic
params.require(:order).permit(:title, :status)

# Nested attributes
params.require(:order).permit(:title, items_attributes: [:id, :name, :quantity, :_destroy])

# Array params
params.require(:order).permit(tag_ids: [])

# Dynamic / polymorphic
def article_params
  permitted = [:title, :body]
  permitted << :admin_note if current_user.admin?
  params.require(:article).permit(permitted)
end

# BAD — permit all (mass assignment vulnerability)
params.require(:order).permit!
```

**Why:** `permit!` bypasses all protection. An attacker can set `admin: true` or any other attribute.

---

## 3. Filters (before_action, around_action)

```ruby
class ApplicationController < ActionController::Base
  before_action :authenticate_user!

  private

  def authenticate_user!
    redirect_to login_path unless current_user
  end
end

class OrdersController < ApplicationController
  before_action :set_order, only: %i[show edit update destroy]
  before_action :authorize_order!, only: %i[edit update destroy]
  skip_before_action :authenticate_user!, only: %i[index show]

  private

  def set_order = @order = Order.find(params[:id])

  def authorize_order!
    redirect_to root_path, alert: t('unauthorized') unless @order.user == current_user
  end
end
```

Execution order matters — filters run in the order declared. Halting (`redirect_to`, `render`) stops the chain. Place guards from broadest to most specific. `around_action` wraps the action (useful for time zones, transactions).

---

## 4. RESTful Routing

```ruby
# GOOD — standard RESTful resources
resources :orders
resources :orders, only: %i[index show create]

# Shallow nesting — max 1 level
resources :orders do
  resources :items, only: %i[index new create], shallow: true
end
# Generates:
# /orders/:order_id/items      (index, new, create)
# /items/:id                    (show, edit, update, destroy) — shallow!

# Member / collection routes
resources :orders do
  member do
    post :ship          # POST /orders/:id/ship
    post :cancel        # POST /orders/:id/cancel
  end
  collection do
    get :search         # GET /orders/search
  end
end

# Route concerns for DRY
concern :commentable do
  resources :comments, only: %i[index create destroy]
end

resources :articles, concerns: :commentable
resources :photos, concerns: :commentable

# BAD — deep nesting (>1 level)
resources :users do
  resources :orders do
    resources :items do
      resources :reviews  # /users/:user_id/orders/:order_id/items/:item_id/reviews — unreadable
    end
  end
end
```

### Namespace, Scope, Constraints

```ruby
# namespace — URL prefix + module nesting + path helpers
namespace :admin do
  resources :orders  # Admin::OrdersController, /admin/orders, admin_orders_path
end

# scope — URL prefix only, no module
scope '/api' do
  resources :orders  # OrdersController, /api/orders
end

# Route constraints
constraints subdomain: 'api' do
  namespace :api do
    resources :orders
  end
end

# Direct routes
direct(:homepage) { 'https://example.com' }
```

---

## 5. Response Patterns

```ruby
# HTML + Turbo Stream
def create
  @comment = @post.comments.build(comment_params)
  if @comment.save
    respond_to do |format|
      format.turbo_stream  # renders create.turbo_stream.erb
      format.html { redirect_to @post, notice: t('.created') }
    end
  else
    render :new, status: :unprocessable_entity
  end
end

# redirect_back_or_to (Rails 7.1+)
redirect_back_or_to root_path, notice: t('.done')

# BAD — redirect_back without fallback (raises on missing referer)
redirect_back fallback_location: root_path  # old way, still works but verbose
```

### Status Codes Decision Table

| Status | Code | When |
|--------|------|------|
| `:ok` | 200 | Successful GET, PUT, PATCH |
| `:created` | 201 | Successful POST (API) |
| `:no_content` | 204 | Successful DELETE (API) |
| `:moved_permanently` | 301 | Permanent redirect |
| `:found` / `:see_other` | 302/303 | After POST redirect (default) |
| `:unauthorized` | 401 | Not logged in |
| `:forbidden` | 403 | Logged in but not authorized |
| `:not_found` | 404 | Resource doesn't exist |
| `:unprocessable_entity` | 422 | Validation failed |
| `:too_many_requests` | 429 | Rate limited |

**Why `:unprocessable_entity`:** Rails 7+ defaults to this on validation failure. Turbo replaces the form with errors instead of following a redirect.

---

## 6. Error Handling

```ruby
class ApplicationController < ActionController::Base
  # Order: most specific FIRST (rescue_from searches bottom-up)
  rescue_from ActiveRecord::RecordNotFound, with: :not_found
  rescue_from ActionPolicy::Unauthorized, with: :forbidden

  private

  def not_found
    respond_to do |format|
      format.html { render 'errors/not_found', status: :not_found }
      format.json { render json: { error: 'Not found' }, status: :not_found }
    end
  end

  def forbidden
    respond_to do |format|
      format.html { redirect_to root_path, alert: t('unauthorized') }
      format.json { render json: { error: 'Forbidden' }, status: :forbidden }
    end
  end
end
```

### Rails Error Reporter (Rails 7+)

```ruby
Rails.error.handle(fallback: -> { [] }) { ExternalApi.fetch_data } # swallows error
Rails.error.record { CriticalOperation.perform! }                   # reports + re-raises
Rails.error.report(exception, handled: true, severity: :warning)    # manual report
```

**Why:** Centralized reporting. All subscribers (Sentry, Honeybadger) receive every error without scattering `begin/rescue` blocks.

---

## 7. API Controllers

```ruby
# app/controllers/api/v1/base_controller.rb
module Api
  module V1
    class BaseController < ActionController::API
      before_action :authenticate_api_user!

      rescue_from ActiveRecord::RecordNotFound do |_e|
        render json: { error: 'Not found' }, status: :not_found
      end

      rescue_from ActiveRecord::RecordInvalid do |e|
        render json: { errors: e.record.errors.full_messages }, status: :unprocessable_entity
      end

      private

      def authenticate_api_user!
        # token-based auth
      end
    end
  end
end

# app/controllers/api/v1/orders_controller.rb
module Api
  module V1
    class OrdersController < BaseController
      def index
        orders = current_user.orders.includes(:items)
        render json: orders, each_serializer: OrderSerializer
      end

      def create
        order = OrderCreator.new(current_user).call(order_params)
        if order.persisted?
          render json: order, serializer: OrderSerializer, status: :created
        else
          render json: { errors: order.errors.full_messages }, status: :unprocessable_entity
        end
      end
    end
  end
end
```

API versioning: URL path (`/api/v1/`) is simplest and most explicit. Header versioning is cleaner URLs but harder to debug.

```ruby
# Consistent JSON envelope
{ data: { id: 1, ... }, meta: { page: 1, total: 42 } }           # success
{ errors: [{ field: 'email', message: '...' }] }                  # validation error
{ error: 'Not found' }                                             # 404/401/403
```

---

## 8. Rate Limiting (Rails 8)

```ruby
class SessionsController < ApplicationController
  rate_limit to: 10, within: 3.minutes, only: :create,
             with: -> { redirect_to new_session_url, alert: t('.rate_limited') }
end

class Api::V1::BaseController < ActionController::API
  rate_limit to: 100, within: 1.minute
end
```

**Why:** Prevents brute-force attacks and API abuse. Built-in to Rails 8 — no gem needed.

---

## 9. Authentication (Rails 8)

```ruby
# $ bin/rails generate authentication
# Generated: User model, Session model, controllers, mailers, views

class User < ApplicationRecord
  has_secure_password
  normalizes :email, with: ->(email) { email.strip.downcase }
end

# GOOD — authenticate_by (Rails 7.1+), timing-safe even when user not found
User.authenticate_by(email: params[:email], password: params[:password])

# BAD — leaks timing info (find is faster when user doesn't exist)
user = User.find_by(email: params[:email])
user&.authenticate(params[:password])
```

---

## 10. Authorization (Policy Objects)

```ruby
# app/policies/order_policy.rb
class OrderPolicy
  attr_reader :user, :order

  def initialize(user, order)
    @user = user
    @order = order
  end

  def show?   = owner? || user.admin?
  def update? = owner? && order.editable?
  def destroy? = owner? && order.draft?

  private

  def owner? = order.user_id == user.id
end

# In controller
class OrdersController < ApplicationController
  def update
    @order = Order.find(params[:id])
    policy = OrderPolicy.new(current_user, @order)
    return redirect_to root_path, alert: t('unauthorized') unless policy.update?
    # ...
  end
end
```

**Why policy objects:** Controllers stay thin. Policies are easy to test in isolation. Authorization rules are in one place.

---

## 11. Flash Messages and I18n

```ruby
# Use t('.key') for action-scoped translations
redirect_to @order, notice: t('.created')   # looks up orders.create.created
redirect_to @order, notice: t('.updated')   # looks up orders.update.updated

# flash.now for render (not redirect)
flash.now[:alert] = t('.invalid')
render :new, status: :unprocessable_entity
```

**Why I18n:** Using `t('.key')` from day one is zero extra effort and enables localization when needed.

---

## 12. Common Anti-Patterns

### Non-RESTful Actions

```ruby
# BAD — custom actions for everything
get 'orders/process_payment'
get 'orders/archive'

# GOOD — extract to separate RESTful controllers
resources :orders do
  resource :payment, only: :create         # POST /orders/:id/payment
  resource :archive, only: :create         # POST /orders/:id/archive
end
```

If you have more than 2 custom member actions, the resource is doing too much — extract sub-resources.

### Querying in Controllers

```ruby
# BAD — raw query logic in controller
@orders = Order.where(status: :active).where('created_at > ?', 30.days.ago)
               .includes(:customer).order(created_at: :desc)

# GOOD — encapsulate in scopes
@orders = Order.active.recent.includes(:customer)
```

### Forgetting Status Codes

```ruby
# BAD — returns 200, Turbo treats it as success
render :new

# GOOD — 422, Turbo replaces form with errors
render :new, status: :unprocessable_entity
```

---

## 13. Testing Controllers

When tests are requested, prefer request specs over controller specs (controller specs are legacy).

| Test | Skip |
|------|------|
| Response status codes | Internal controller methods |
| Redirect targets | Filter chain order |
| JSON response structure (API) | View rendering details |
| Authentication / authorization flows | Flash message text |
| Error handling (404, 422, 500) | Strong params internals |

```ruby
# GOOD — request spec
RSpec.describe 'Orders', type: :request do
  describe 'POST /orders' do
    context 'with valid params' do
      it 'creates order and redirects' do
        post orders_path, params: { order: valid_attributes }
        expect(response).to redirect_to(Order.last)
      end
    end

    context 'with invalid params' do
      it 'returns 422' do
        post orders_path, params: { order: invalid_attributes }
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end
end
```

For full testing conventions, see `rspec-testing.md`.

---

## 14. Routing Checklist

| Check | Action |
|-------|--------|
| More than 7 RESTful actions? | Extract sub-resource controller |
| More than 2 custom member actions? | Extract to separate controller |
| Nesting deeper than 1 level? | Use `shallow: true` |
| Same routes in multiple resources? | Extract `concern` |
| API and HTML on same resource? | Separate namespaces (`/api/v1/` vs `/`) |
| Unused routes exposed? | Use `only:` / `except:` to limit |
