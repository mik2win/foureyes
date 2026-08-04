---
paths:
  - "app/models/**/*.rb"
  - "app/controllers/**/*.rb"
  - "app/services/**/*.rb"
---

# Rails Multi-Tenancy (Isolation)

Based on the acts_as_tenant gem, Rails default-scope patterns, OWASP access-control guidance.

This is **defense-in-depth** below authorization. Policy objects (`rails-business-logic.md` section 7) and IDOR scoping (`rails-security.md` section 1) are the first line — `current_user.orders.find(...)`. Tenant isolation is the ORM backstop: even a query that forgets to scope is auto-filtered to the current tenant. You need both.

Patterns below are framework-agnostic (acts_as_tenant, or a `default_scope { where(tenant_id: Current.tenant_id) }`). The rules are the same regardless.

---

## 1. Set the Current Tenant in ONE Place

Resolve the tenant once, in a `before_action` (or middleware), from the **request** — subdomain, custom domain, or authenticated session. Every tenant-scoped model then auto-scopes its queries; no `where(tenant_id:)` in normal controller flow.

```ruby
# GOOD — single resolution point
class ApplicationController < ActionController::Base
  before_action :set_current_tenant

  private

  def set_current_tenant
    tenant = Tenant.find_by!(subdomain: request.subdomain)
    ActsAsTenant.current_tenant = tenant   # or Current.tenant = tenant
  end
end

# GOOD — model auto-scopes; query needs no tenant_id
class Order < ApplicationRecord
  acts_as_tenant(:tenant)   # belongs_to :tenant + default tenant scope
end
Order.find(params[:id])     # implicitly scoped to current_tenant
```

`current_tenant` stays `nil` only for genuinely global areas (the marketing site, or an admin panel with no tenant selected).

---

## 2. NEVER Accept `tenant_id` From User Input

The tenant is derived from the request, never from params, body, headers, or any user-controllable value. Accepting `tenant_id` from input is a cross-tenant escalation hole — an attacker sets it to someone else's tenant.

```ruby
# BAD — tenant from params (cross-tenant escalation)
def create
  Order.create!(order_params.merge(tenant_id: params[:tenant_id]))
end

# BAD — permitting tenant_id at all
params.require(:order).permit(:title, :tenant_id)   # never permit it

# GOOD — tenant comes from the resolved scope; never from input
def create
  Order.create!(order_params)   # tenant_id set automatically by acts_as_tenant
end
```

Even a superuser switching tenants derives the target from a server-trusted source (admin-selected, re-validated against their grants) and feeds it to the resolution point in section 1 — not into a write directly.

---

## 3. Wrap Code That Runs Outside a Tenant Request

Any code with no request context, or that must legitimately cross tenants, must lift or set the scope itself. Under strict enforcement, a tenant-scoped query with no current tenant raises (`ActsAsTenant::Errors::NoTenantSet`) rather than silently leaking across tenants.

| Situation | Wrap with |
|---|---|
| Maintenance/cleanup job across all tenants | `ActsAsTenant.without_tenant { }` (iterate tenants explicitly) |
| Background job that must run per-tenant | `ActsAsTenant.with_tenant(tenant) { }` |
| Admin reading **another** tenant within a request | `ActsAsTenant.without_tenant { }` |
| Public intake / signup / auth mailers (pre-tenant) | `ActsAsTenant.without_tenant { }` |
| Onboarding: building records for a target tenant | `ActsAsTenant.with_tenant(target) { }` |

```ruby
# GOOD — global job has no request context; iterate tenants explicitly
class BackfillCountsJob < ApplicationJob
  def perform
    Tenant.find_each do |tenant|
      ActsAsTenant.with_tenant(tenant) { Order.find_each { |o| ... } }
    end
  end
end
```

### Footgun: jobs serialize the current tenant

Many setups serialize `current_tenant` into every job enqueued during a request and re-find it on perform. **Deleting the resolved tenant breaks any job enqueued during its `destroy`** (reindex, cleanup) — the re-find raises `RecordNotFound`. Wrap tenant deletion in `ActsAsTenant.without_tenant { }` so no tenant reference is serialized into the jobs it spawns.

---

## 4. Enforcement Is Environment-Gated

Strict mode (raise on missing tenant) is the isolation regression gate. Turn it on always in **test**; flip it in production as a **separate ops-gated rollout**, not a feature task.

```ruby
# config/initializers/acts_as_tenant.rb
config.require_tenant = Rails.env.test? || ENV["TENANT_STRICT"] == "1"
```

Do not claim production enforcement is on — but write code as if it is (wrap every global path per section 3) so the flip is safe.

For NOT NULL `tenant_id` models the association is required (`belongs_to :tenant`, no `optional: true`). Keep `optional: true` only on models that are legitimately tenant-less (e.g. a superuser `User`).

---

## 5. Isolation Specs — Tenant A Cannot Read Tenant B

The one test that matters: a query running under tenant A must not see tenant B's rows. The spec must **fail when the scoping fix is reverted** — otherwise it's vacuous.

```ruby
# GOOD — proves cross-tenant reads are blocked
RSpec.describe "Order tenant isolation" do
  it "scopes reads to the current tenant" do
    a = create(:tenant); b = create(:tenant)
    ActsAsTenant.with_tenant(a) { create(:order, title: "A-order") }
    ActsAsTenant.with_tenant(b) { create(:order, title: "B-order") }

    ActsAsTenant.with_tenant(a) do
      expect(Order.pluck(:title)).to eq(["A-order"])   # B's row invisible
    end
  end
end
```

Footguns when writing these specs:

- **Lifting the scope globally makes the test vacuous.** A mode that sets the scope to "unscoped" lets code that forgot its `without_tenant` wrapper still pass — it tests nothing. Use it only for genuinely global logic.
- **The real regression mode is "no baseline tenant, scope NOT lifted":** any tenant-scoped query raises unless the code lifts the scope itself. Wrap setup *reads* (e.g. counting another tenant's rows) in `without_tenant`; factory *saves* should already be lifted by the factory's create hook.
- A green isolation spec under "no baseline tenant" means the spec isn't exercising the path — make it red first.

See also `rails-security.md` (IDOR, scoped queries) and `rails-background-jobs.md` (per-tenant jobs).
