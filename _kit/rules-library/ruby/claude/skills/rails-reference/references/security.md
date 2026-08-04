# Rails security — worked examples

Companion reference to the `rails-security` rule; loaded on demand.

---

## 1. OWASP Top 10 for Rails

### SQL Injection

```ruby
# GOOD — parameterized queries
User.where('email = ?', params[:email])
User.where(email: params[:email])

# BAD — string interpolation
User.where("email = '#{params[:email]}'")  # attacker: ' OR 1=1 --
```

See `rails-activerecord-queries.md` section 6 for full SQL safety patterns.

---

### XSS (Cross-Site Scripting)

```ruby
# Rails auto-escapes by default in views
<%= user.name %>  # SAFE — auto-escaped

# DANGEROUS — bypasses escaping
<%= raw user.bio %>              # XSS if bio contains <script>
<%= user.bio.html_safe %>        # same problem
<%= content_tag(:div, user.bio.html_safe) %>

# GOOD — sanitize if you must render HTML
<%= sanitize user.bio, tags: %w[p br strong em], attributes: %w[href title] %>
```

---

### CSRF (Cross-Site Request Forgery)

```ruby
# Rails includes CSRF protection by default
class ApplicationController < ActionController::Base
  protect_from_forgery with: :exception  # default in Rails
end

# For API-only controllers that use token auth:
class Api::BaseController < ActionController::API
  # No CSRF needed — tokens are not auto-sent by browsers
end

# BAD — disabling CSRF globally
skip_forgery_protection  # NEVER do this in non-API controllers
```

---

### Mass Assignment

```ruby
# GOOD — strong parameters
params.require(:user).permit(:name, :email)

# BAD — permit all
params.require(:user).permit!  # attacker sets admin: true
```

---

### IDOR (Insecure Direct Object Reference)

```ruby
# BAD — any user can access any order
@order = Order.find(params[:id])

# GOOD — scope to current user
@order = current_user.orders.find(params[:id])

# GOOD — or check authorization
@order = Order.find(params[:id])
authorize! @order  # raises if not allowed
```

---

### Command Injection

```ruby
# BAD — user controls the command
system("convert #{params[:filename]} output.png")  # attacker: "; rm -rf /"

# GOOD — array form prevents shell interpretation
system('convert', params[:filename], 'output.png')

# GOOD — avoid system calls entirely when possible
# Use Ruby gems (mini_magick, image_processing) instead of shelling out
```

---

### Open Redirect

```ruby
# BAD — attacker sets return_to=https://evil.com
redirect_to params[:return_to]

# GOOD — use url_from (Rails 7+)
redirect_to url_from(params[:return_to]) || root_path
```

---

### File Access

```ruby
# BAD — path traversal
send_file "uploads/#{params[:filename]}"  # attacker: ../../etc/passwd

# GOOD — sanitize
basename = File.basename(params[:filename])  # strips directory traversal
path = Rails.root.join('uploads', basename)
raise ActiveRecord::RecordNotFound unless File.exist?(path)
send_file path
```

---

## 2. Content Security Policy

```ruby
# config/initializers/content_security_policy.rb
Rails.application.configure do
  config.content_security_policy do |policy|
    policy.default_src :self
    policy.font_src    :self, 'https://fonts.gstatic.com'
    policy.img_src     :self, :data, 'https://cdn.example.com'
    policy.script_src  :self
    policy.style_src   :self, 'https://fonts.googleapis.com'
    policy.connect_src :self

    # Report violations (monitoring)
    policy.report_uri '/csp-report'
  end

  # Use nonce for inline scripts (recommended over 'unsafe-inline')
  config.content_security_policy_nonce_generator = ->(request) { request.session.id.to_s }
  config.content_security_policy_nonce_directives = %w[script-src style-src]

  # Start with report-only mode
  config.content_security_policy_report_only = true
end
```

```erb
<%# In views — nonce-based inline scripts %>
<%= csp_meta_tag %>
<%= javascript_tag nonce: true do %>
  console.log("This is allowed by CSP");
<% end %>
```

---

## 3. Encrypted Credentials

```ruby
# Edit credentials (opens in $EDITOR)
# $ EDITOR=vim bin/rails credentials:edit

# Per-environment credentials
# $ bin/rails credentials:edit --environment production

# Access in code
Rails.application.credentials.dig(:aws, :access_key_id)
Rails.application.credentials.secret_key_base
```

Rules:
- NEVER commit `master.key` or `config/credentials/*.key`
- NEVER hardcode secrets in code, ENV vars, or initializers
- Use per-environment credentials for production vs staging
- Use `dig` for nested access (returns nil vs raising)

```ruby
# BAD — secrets in code
API_KEY = 'sk_live_abc123'

# BAD — even ENV vars have issues (visible in process list, logs)
API_KEY = ENV['API_KEY']  # acceptable but credentials are preferred

# GOOD — encrypted credentials
api_key = Rails.application.credentials.dig(:stripe, :api_key)
```

---

## 4. Brakeman — Static Security Analysis

```ruby
# Gemfile (development only)
group :development do
  gem 'brakeman'
end

# Run:
# $ brakeman
# $ brakeman -o report.html
# $ brakeman --only-files app/controllers/
```

Common warnings and fixes:

| Warning | Fix |
|---------|-----|
| SQL Injection | Use parameterized queries |
| Cross-Site Scripting | Remove `html_safe`, use `sanitize` |
| Mass Assignment | Use strong parameters |
| Command Injection | Avoid `system()` with user input; use array form |
| File Access | Don't use `params` in file paths |
| Redirect | Validate redirect URLs with `url_from` |
| Dangerous Send | Never use `send(params[:method])` |
| Deserialize | Never `Marshal.load` or `YAML.unsafe_load` untrusted data |

---

## 5. Logging

```ruby
# config/application.rb — tagged logging adds context to every log line
config.log_tags = [:request_id]

config.log_tags = [
  :request_id,
  ->(request) { "IP:#{request.remote_ip}" }
]

# Usage
Rails.logger.info("Order created: #{order.id}")
Rails.logger.tagged('PaymentService') { Rails.logger.info("Charged $#{amount}") }
# => [abc-123-def] [PaymentService] Charged $50.00

# Log levels
Rails.logger.debug   # development only, verbose
Rails.logger.info    # normal operations
Rails.logger.warn    # unusual but handled
Rails.logger.error   # errors requiring attention
Rails.logger.fatal   # system-breaking errors
```

Production: use `:info` level (not `:debug`), structured logging (JSON) for aggregation, meaningful events not SQL queries.

```ruby
# GOOD — structured, searchable log entries
Rails.logger.info("order.created user_id=#{user.id} order_id=#{order.id} total=#{order.total}")

# BAD — unstructured, impossible to parse at scale
Rails.logger.info("Order was created successfully!")
```

---

## 6. Rails Error Reporter (Rails 7+)

```ruby
# Handle — swallows error, continues execution
result = Rails.error.handle(fallback: -> { [] }) do
  ExternalApi.fetch_data
end

# Record — reports error but re-raises
Rails.error.record do
  CriticalOperation.perform!
end

# Manual report
Rails.error.report(exception, handled: true, severity: :warning, context: { user_id: 42 })

# Custom subscriber (integrate with Sentry, Honeybadger, etc.)
# config/initializers/error_reporting.rb
class ErrorSubscriber
  def report(error, handled:, severity:, context:, source: nil)
    Sentry.capture_exception(error, extra: context) unless handled
  end
end

Rails.error.subscribe(ErrorSubscriber.new)
```

| Method | Error Propagation | Use When |
|--------|-------------------|----------|
| `handle` | Swallows error, returns fallback | Non-critical operations (analytics, recommendations) |
| `record` | Reports and re-raises | Critical operations where you want monitoring + failure |
| `report` | Manual report only | Errors you've already handled but want to track |

---

## 7. Parameter Filtering

```ruby
# config/initializers/filter_parameter_logging.rb
Rails.application.config.filter_parameters += [
  :password, :password_confirmation, :token, :secret,
  :ssn, :credit_card, :cvv,
  /authorization/i, /bearer/i
]
# These values appear as [FILTERED] in logs

# Custom filtering for specific fields
config.filter_parameters += [:email]  # if PII must not appear in logs
```

---

## 8. Session Security

```ruby
# config/initializers/session_store.rb (or application.rb)
Rails.application.config.session_store :cookie_store,
  key: '_myapp_session',
  httponly: true,       # JavaScript cannot read the cookie
  secure: Rails.env.production?,  # only sent over HTTPS
  same_site: :lax       # CSRF protection for cross-site requests

# Force SSL in production
# config/environments/production.rb
config.force_ssl = true  # redirects HTTP -> HTTPS, sets HSTS header

# Session timeout
config.session_store :cookie_store, expire_after: 30.minutes
```

| Setting | Value | Why |
|---------|-------|-----|
| `httponly` | `true` | Prevents XSS from stealing session via `document.cookie` |
| `secure` | `true` (production) | Prevents session leaking over plain HTTP |
| `same_site` | `:lax` | Blocks cross-site form submissions while allowing navigation |
| `force_ssl` | `true` | Ensures all traffic is encrypted; sets HSTS header |
| `expire_after` | `30.minutes` | Limits window of attack for stolen sessions |

---

## 9. Solid Cable (Rails 8)

```ruby
# config/cable.yml
production:
  adapter: solid_cable
  silence_polling: true
  connects_to:
    database:
      writing: cable
      reading: cable

# No Redis needed — database-backed WebSocket relay
# Messages retained for 1 day by default
```

**Why Solid Cable:** Eliminates Redis dependency for Action Cable. Database-backed. Simpler deployment. Use Redis adapter only for very high WebSocket throughput.

---

## 10. Rate Limiting (Rails 8)

```ruby
class SessionsController < ApplicationController
  rate_limit to: 10, within: 3.minutes, only: :create, with: -> {
    redirect_to new_session_url, alert: 'Too many login attempts. Try again later.'
  }
end

class Api::BaseController < ApplicationController
  rate_limit to: 300, within: 5.minutes, by: -> { request.remote_ip }
end

class PasswordResetsController < ApplicationController
  rate_limit to: 5, within: 1.hour, only: :create, with: -> {
    head :too_many_requests
  }
end
```

**Why:** Without rate limiting, attackers can brute-force passwords, enumerate users, or overwhelm expensive endpoints.

---

## 11. Authentication Best Practices

```ruby
# Rails 8 built-in authentication generator
# $ bin/rails generate authentication

# has_secure_password — bcrypt-based, constant-time comparison
class User < ApplicationRecord
  has_secure_password

  normalizes :email, with: ->(email) { email.strip.downcase }
  validates :email, presence: true, uniqueness: true,
            format: { with: URI::MailTo::EMAIL_REGEXP }
end
```

Rules:
- Use `has_secure_password` (bcrypt) — never roll your own hashing
- Rate limit login and password reset endpoints
- Normalize email before storage (downcase, strip)
- Use `ActiveSupport::SecurityUtils.secure_compare` for token comparison
- Call `reset_session` before setting `session[:user_id]` on login (prevents session fixation)

```ruby
# GOOD — rotate session on login
def create
  user = User.authenticate_by(email: params[:email], password: params[:password])
  if user
    reset_session  # prevents session fixation
    session[:user_id] = user.id
    redirect_to root_path
  else
    flash.now[:alert] = 'Invalid email or password'
    render :new, status: :unprocessable_entity
  end
end
```

---

## 12. HTTP Security Headers

```ruby
# config/application.rb or middleware
config.action_dispatch.default_headers = {
  'X-Frame-Options' => 'SAMEORIGIN',          # prevents clickjacking
  'X-Content-Type-Options' => 'nosniff',       # prevents MIME sniffing
  'X-XSS-Protection' => '0',                   # disable legacy filter (CSP is better)
  'Referrer-Policy' => 'strict-origin-when-cross-origin',
  'Permissions-Policy' => 'camera=(), microphone=(), geolocation=()'
}
```

| Header | Purpose |
|--------|---------|
| `X-Frame-Options: SAMEORIGIN` | Prevents clickjacking via iframes |
| `X-Content-Type-Options: nosniff` | Prevents browser MIME type guessing |
| `Referrer-Policy` | Limits referrer data sent to other origins |
| `Permissions-Policy` | Disables unused browser features |
| `Strict-Transport-Security` | Forces HTTPS (set by `force_ssl`) |

---

## 13. Gem Vulnerability Scanning

```ruby
# Gemfile
group :development do
  gem 'bundler-audit'
end

# $ bundle audit check --update
# Run in CI on every build — gem vulnerabilities are the #1 source of Rails security incidents.
```

---

## 14. Secrets in Version Control

```gitignore
# .gitignore — always include these
config/master.key
config/credentials/*.key
.env
.env.*
*.pem
*.key
```

---

## 15. Security Checklist

| Check | Status |
|-------|--------|
| Strong parameters on every controller action | Required |
| No `html_safe`/`raw` without explicit justification | Required |
| CSRF protection enabled (non-API controllers) | Default in Rails |
| Scoped queries (`current_user.orders.find`) | Required |
| Encrypted credentials (not ENV vars) | Recommended |
| `force_ssl = true` in production | Required |
| `config.filter_parameters` for PII | Required |
| Brakeman in CI pipeline | Recommended |
| Content Security Policy configured | Recommended |
| Session cookies: httponly, secure, same_site | Required |
| Rate limiting on auth endpoints | Required (Rails 8) |
| `bundler-audit` for gem vulnerabilities | Recommended |
| HTTP security headers configured | Recommended |
| `reset_session` after login | Required |
| No `system()`/`exec()` with user input | Required |
| No `Marshal.load`/`YAML.unsafe_load` on untrusted data | Required |
| `.gitignore` includes key files and `.env` | Required |
| Per-environment credentials for production vs staging | Recommended |
