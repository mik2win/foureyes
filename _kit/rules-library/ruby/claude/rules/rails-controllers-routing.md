---
paths:
  - "app/controllers/**/*.rb"
  - "config/routes.rb"
  - "config/routes/**/*.rb"
---

# Rails Controllers & Routing

Based on Rails Guides (Action Controller, Routing).

For OOP principles and service object patterns, see `ruby-oop.md`.

> Worked examples live in the `rails-reference` skill (`references/controllers-routing.md`).

---

## 1. Thin Controller Pattern

- Controller coordinates — it does not contain business logic. Multiple model/service calls per action are fine. Business *decisions* (if/else on domain state, calculations, orchestration rules) belong in models or services.
- Structure each action: guard → execute → respond.
- **The line:** calling several collaborators (`OrderCreator` + `WarehouseNotifier` + `AnalyticsTracker`) is fine — that's coordination. `if order.total > 1000 then discount = ...` is not — that decision belongs in a service or model.
- Action order convention: index, show, new, create, edit, update, destroy — then `private`. Matches the RESTful lifecycle.

---

## 2. Strong Parameters

- Always whitelist: `params.expect(model: [:attr, ...])` on Rails 8+ (safer — raises a 400, not a 500, on param tampering); `params.require(...).permit(...)` on ≤7.x. Support nested attributes (`items_attributes: [...]`), array params (`tag_ids: []`), and dynamic permits built per role.
- **Never `permit!`** — it bypasses all protection; an attacker can set `admin: true` or any other attribute.

---

## 3. Filters (before_action, around_action)

- Use `before_action` for auth, loading records (`set_order`), and authorization guards; `skip_before_action` to opt specific actions out.
- **Declare the gate with `except:`, never `only:`.** `before_action :require_admin, except: %i[index show]` makes an action added later inherit the guard; `only:` turns the protected set into a hand-kept registry that drifts the first time someone adds an action, and the endpoint ships unauthenticated. `raise_on_missing_callback_actions` (7.1+) does not catch this — it only flags filter names that no longer exist.
- The polarity inverts for `skip_before_action`: there `only:` is the whitelist that fails closed and `except:` the blacklist that fails open. Reviewing a controller, grep `before_action.*only:` on guard-named filters and `skip_before_action.*except:` — every hit is an access-control finding until shown otherwise.
- Execution order matters — filters run in declaration order. Halting (`redirect_to`, `render`) stops the chain. Place guards broadest to most specific.
- `around_action` wraps the action (useful for time zones, transactions).

---

## 4. RESTful Routing

- Prefer standard `resources`; trim with `only:` / `except:`.
- **Max 1 level of nesting** — use `shallow: true` so members route at `/items/:id` instead of deep paths.
- Add extra verbs via `member` / `collection` blocks; DRY repeated route sets with a `concern`.
- Never nest deeper than one level (`/users/:user_id/orders/:order_id/items/...` is unreadable).

### Namespace, Scope, Constraints

| Construct | Effect |
|---|---|
| `namespace :admin` | URL prefix + module nesting + path helpers (`Admin::OrdersController`, `/admin/orders`) |
| `scope '/api'` | URL prefix only, no module |
| `constraints subdomain: 'api'` | Match on request attributes (subdomain, format, etc.) |
| `direct(:name) { ... }` | Custom named URL helper |

---

## 5. Response Patterns

- Use `respond_to` to serve HTML and Turbo Stream from one action; prefer `redirect_back_or_to fallback` (Rails 7.0+) over bare `redirect_back`.
- Return the right status — `:unprocessable_entity` (422) on validation failure so Turbo replaces the form with errors instead of following a redirect.

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

---

## 6. Error Handling

- Handle cross-cutting errors with `rescue_from` in `ApplicationController`; declare **most specific first** (`rescue_from` searches bottom-up). Branch on format (HTML vs JSON) in the handler.
- Prefer the Rails Error Reporter (Rails 7+): `Rails.error.handle` (swallow + fallback), `Rails.error.record` (report + re-raise), `Rails.error.report` (manual). Centralizes reporting so all subscribers (Sentry, Honeybadger) get every error without scattered `begin/rescue`.

---

## 7. API Controllers

- Inherit API controllers from `ActionController::API` via a versioned `BaseController` that holds auth + shared `rescue_from` handlers.
- Version in the URL path (`/api/v1/`) — simplest and most explicit.
- Keep a consistent JSON envelope: `{ data:, meta: }` on success, `{ errors: [...] }` on validation error, `{ error: ... }` for 4xx.

---

## 8. Rate Limiting (Rails 7.2+)

- Use the built-in `rate_limit to:, within:, only:, with:` (no gem) to throttle abuse-prone actions (e.g. `SessionsController#create`) and API base controllers. Prevents brute-force and API abuse.

---

## 9. Authentication (Rails 8)

- Scaffold with `bin/rails generate authentication`; model uses `has_secure_password` and `normalizes :email`.
- Authenticate with `User.authenticate_by(email:, password:)` (Rails 7.1+) — timing-safe even when the user doesn't exist.
- **Avoid** `find_by` + `&.authenticate` — it leaks timing info (find is faster when the user is absent).

---

## 10. Authorization (Policy Objects)

- Extract authorization into plain policy objects (`OrderPolicy.new(user, order).update?`) and call them from the controller, redirecting on denial.
- **Why:** controllers stay thin, policies test in isolation, and authorization rules live in one place.

---

## 11. Flash Messages and I18n

- Use action-scoped translations `t('.key')` (e.g. `t('.created')` → `orders.create.created`) from day one — zero extra effort, localization-ready.
- Use `flash.now[...]` with `render` (not redirect).

---

## 12. Common Anti-Patterns

- **Non-RESTful actions** — don't bolt on `get 'orders/process_payment'`; extract sub-resources (`resource :payment, only: :create`). More than 2 custom member actions means the resource is doing too much.
- **Querying in controllers** — push raw `where`/`order` chains into model scopes (`Order.active.recent.includes(:customer)`).
- **Forgetting status codes** — bare `render :new` returns 200 and Turbo treats it as success; use `status: :unprocessable_entity`.

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
