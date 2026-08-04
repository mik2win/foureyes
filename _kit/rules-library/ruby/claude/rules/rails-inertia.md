---
paths:
  - "app/controllers/**/*.rb"
---

# Rails + Inertia (Backend Bridge)

Based on Inertia Rails docs (inertia-rails.dev), the Inertia.js protocol.

The set's UI rules assume Hotwire/Turbo (`rails-controllers-routing.md` section 5). This file is the **React/Inertia alternative** for the backend half of that bridge — how a Rails controller hands data to a React page. The frontend half lives in `react-ts/inertia-react.md`.

**Thin controllers still apply.** Everything in `rails-controllers-routing.md` (guard → execute → respond, strong params, filters, policy objects) is unchanged. Inertia only changes the *response* — `render inertia:` replaces `render`/`respond_to`. Page data still comes from a presenter (`rails-business-logic.md` section 5), never inline in the action.

---

## 1. The Props Envelope: `data` / `meta` / `errors`

Every action that renders an Inertia page returns the same three-key shape. This is a discipline rule — pick it on day one so every screen reads the same on the frontend.

```ruby
# GOOD — fixed envelope, data from a presenter
def show
  render inertia: "Orders/Show", props: {
    data:   OrderPresenter.new(@order).as_screen,  # the screen's content
    meta:   { current_tab: params[:tab] },         # page/list machinery only
    errors: {},                                      # always present
  }
end

# GOOD — list screen: pagination lives under meta, never top-level
def index
  render inertia: "Orders/Index", props: {
    data:   { items: OrdersPresenter.new(@orders).rows },
    meta:   { pagy: pagy_metadata(@pagy), filters: filter_values },
    errors: {},
  }
end

# BAD — flat props bag: component can't tell content from navigation state
render inertia: "Orders/Index", props: { orders:, pagy:, filters:, current_tab: }
```

| Key | Holds | Rule |
|-----|-------|------|
| `data` | The screen's content (presenter output) | One screen presenter per page; component reads its props from here |
| `meta` | Page state + list machinery: `pagy`, `filters`, `current_tab` | Never mix into `data` — content vs navigation state must stay separable |
| `errors` | Field validation messages | Always present (see section 4) |

The page name (`"Orders/Show"`) is a path into the React component tree, not a Rails view path.

---

## 2. Deferred Props — `InertiaRails.defer { }`

Wrap any prop that **triggers a query or costs more than ~50ms** in `InertiaRails.defer { }`. The initial render returns immediately; Inertia fetches the deferred prop in a follow-up request.

```ruby
data: {
  order:         OrderPresenter.new(@order).as_screen,        # already loaded — eager
  line_items:    InertiaRails.defer { line_item_rows(@order) }, # query-backed — defer
  audit_history: InertiaRails.defer { audit_rows(@order) },     # slow — defer
}
```

Do **not** defer cheap, already-loaded values (the record you just fetched, a constant, a memoised `Current.*`).

```ruby
# Presenters return EAGER values or InertiaRails.defer — NEVER a bare lambda.
# A `-> { ... }` inside a presenter closes over the presenter instance; Inertia's
# as_json prop serialization recurses into that closure and overflows the stack.
# Bare lambdas are only safe defined directly in a controller action.

# BAD — bare lambda from a presenter
images: -> { @order.attachments.map { ... } }   # stack overflow on serialization

# GOOD — typed deferred prop
images: InertiaRails.defer { @order.attachments.map { ... } }
```

### Grouped partial reloads — `group:`

Props belonging to the same UI section share a `group:` so one partial reload fetches them together instead of one request per prop. One section → one group.

```ruby
items_rows: InertiaRails.defer(group: "items") { items_data[:rows] },
items_pagy: InertiaRails.defer(group: "items") { items_data[:pagy] },
```

---

## 3. Validation Errors — Surface via `inertia: { errors: }` + Redirect Back

Inertia has no `render :new, status: :unprocessable_entity`. On failure you **redirect back** carrying the errors; Inertia re-renders the same page component with `errors` populated. Use string keys.

```ruby
# GOOD — failure redirects back with field errors
def create
  @order = Orders::Creator.new(current_user).call(order_params)
  if @order.persisted?
    redirect_to @order, notice: t(".created")
  else
    redirect_to new_order_path, inertia: { errors: @order.errors }
  end
end
```

`config.always_include_errors_hash = true` (in `config/initializers/inertia_rails.rb`) injects the `errors` key on every response, so the frontend can always read it.

---

## 4. Flash Semantics — One Mechanism Per Outcome

A redirect carries **either** field errors **or** a flash message — never both for the same outcome. Co-using `alert:` and `inertia: { errors: }` on one redirect is contradictory and banned.

| Outcome | Mechanism |
|---|---|
| Form field validation errors | `redirect ..., inertia: { errors: {...} }` (string keys) |
| Business-rule violation, no specific field | `redirect ..., alert: "..."` |
| Inline non-field error tied to the form | `inertia: { errors: { "base" => ["..."] } }` |
| Success message | `redirect ..., notice: "..."` |
| Warning (non-blocking) | `flash[:warning] = "..."` |

For service `Result` failures (`rails-business-logic.md` section 4), route through one helper so a redirect can never carry both — the helper returns `{ inertia: { errors: } }` when any field-level (non-`base`) error exists, otherwise `{ alert: result.error }`:

```ruby
if result.success?
  redirect_to order_path(result.value), notice: t(".created")
else
  redirect_to new_order_path, **flash_for_service_error(result)
end
```

Configure the surfaced flash keys explicitly: `inertia_rails.flash_keys = %i[notice alert warning]`.

---

## 5. Shared Data

Data needed on every page (current user, tenant, feature flags) goes through `inertia_share` on `ApplicationController`, not into each action's props. Keep it small — it ships on every response.

```ruby
class ApplicationController < ActionController::Base
  inertia_share do
    { current_user: current_user && { id: current_user.id, name: current_user.name } }
  end
end
```

Lazy-evaluate expensive shared values with a block (`inertia_share thing: -> { ... }`) — a bare lambda is safe here because it's defined in the controller, not a presenter (see section 2).

---

## 6. Checklist for a New Inertia Action

| Check | Required |
|---|---|
| Renders `data` / `meta` / `errors`; `pagy`/`filters`/`current_tab` under `meta` | Required |
| `data` comes from a screen presenter, not inline serialization | Required |
| Every query-backed or >50ms prop wrapped in `InertiaRails.defer` | Required |
| No bare `-> { }` props returned from a presenter | Required |
| Related deferred props share one `group:` | Recommended |
| Failure path uses `inertia: { errors: }` OR `alert:` — never both | Required |
| Controller still thin (auth, params, delegate, respond) | Required |
