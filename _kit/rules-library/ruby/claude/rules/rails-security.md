---
paths:
  - "app/controllers/**/*.rb"
  - "config/initializers/**/*.rb"
---

# Rails Security & Operations

Based on Rails Guides (Security), OWASP Ruby on Rails Cheat Sheet, Brakeman documentation.

> Worked examples live in the `rails-reference` skill (`references/security.md`).

---

## 1. OWASP Top 10 for Rails

- **SQL injection** — parameterized queries only (`where('email = ?', x)` / `where(email: x)`); never interpolate user input into SQL. See `rails-activerecord-queries.md` section 6.
- **XSS** — rely on Rails auto-escaping in views; never `raw` / `.html_safe` on user input. If you must render HTML, `sanitize` with an explicit tag/attribute allowlist.
- **CSRF** — keep `protect_from_forgery with: :exception` (Rails default); never `skip_forgery_protection` on non-API controllers. Token-auth `ActionController::API` controllers don't need it.
- **Mass assignment** — strong params (`permit(:name, :email)`); never `permit!`.
- **IDOR** — scope lookups to the owner (`current_user.orders.find(params[:id])`), or authorize explicitly; never bare `Model.find(params[:id])` on user-owned data.
- **Command injection** — never interpolate params into `system(...)`; use the array form (`system('convert', path, ...)`), or prefer gems (`mini_magick`, `image_processing`) over shelling out.
- **Open redirect** — never `redirect_to params[:return_to]`; wrap with `url_from(...) || root_path` (Rails 7+).
- **File access** — never interpolate params into file paths; strip traversal with `File.basename`, join under a known root, and check existence before `send_file`.

---

## 2. Content Security Policy

- Configure CSP in `config/initializers/content_security_policy.rb`; set explicit per-directive sources, add a `report_uri`.
- Prefer nonces for inline scripts (`nonce_generator` + `nonce_directives`) over `'unsafe-inline'`; emit `csp_meta_tag` and `javascript_tag nonce: true` in views.
- Roll out in `content_security_policy_report_only = true` mode first.

---

## 3. Encrypted Credentials

- Prefer encrypted credentials over ENV vars; access with `Rails.application.credentials.dig(...)` (nil vs raising).
- NEVER commit `master.key` or `config/credentials/*.key`.
- NEVER hardcode secrets in code, ENV vars, or initializers.
- Use per-environment credentials for production vs staging.

---

## 4. Brakeman — Static Security Analysis

- Add `gem 'brakeman'` (development); run `brakeman` (optionally `-o report.html`, `--only-files`); wire into CI.

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

- Use tagged logging (`config.log_tags = [:request_id, ...]`) to add request context to every line.
- Production: `:info` level (not `:debug`), structured/searchable entries (key=value or JSON), meaningful events — not SQL queries or vague success messages.
- Levels: `debug` (dev only), `info` (normal), `warn` (unusual but handled), `error` (needs attention), `fatal` (system-breaking).

---

## 6. Rails Error Reporter (Rails 7+)

| Method | Error Propagation | Use When |
|--------|-------------------|----------|
| `handle` | Swallows error, returns fallback | Non-critical operations (analytics, recommendations) |
| `record` | Reports and re-raises | Critical operations where you want monitoring + failure |
| `report` | Manual report only | Errors you've already handled but want to track |

- Add a custom subscriber (`Rails.error.subscribe`) to integrate with Sentry/Honeybadger.

---

## 7. Parameter Filtering

- Add sensitive keys to `config.filter_parameters` (`:password`, `:token`, `:secret`, `:ssn`, `:credit_card`, `:cvv`, `/authorization/i`, `/bearer/i`); they appear as `[FILTERED]` in logs.
- Add PII fields (e.g. `:email`) that must not appear in logs.

---

## 8. Session Security

| Setting | Value | Why |
|---------|-------|-----|
| `httponly` | `true` | Prevents XSS from stealing session via `document.cookie` |
| `secure` | `true` (production) | Prevents session leaking over plain HTTP |
| `same_site` | `:lax` | Blocks cross-site form submissions while allowing navigation |
| `force_ssl` | `true` | Ensures all traffic is encrypted; sets HSTS header |
| `expire_after` | `30.minutes` | Limits window of attack for stolen sessions |

- Set these on `session_store :cookie_store`; set `config.force_ssl = true` in production.

---

## 9. Solid Cable (Rails 8)

- Use the `solid_cable` adapter (`config/cable.yml`) — database-backed WebSocket relay, no Redis. Messages retained 1 day by default. Use the Redis adapter only for very high WebSocket throughput.

---

## 10. Rate Limiting (Rails 7.2+)

- Apply `rate_limit to:, within:, only:/by:, with:` on auth-sensitive controllers (login, password reset, APIs) to block brute-force, user enumeration, and abuse of expensive endpoints.

---

## 11. Authentication Best Practices

- Use `has_secure_password` (bcrypt) — never roll your own hashing.
- Rate limit login and password reset endpoints.
- Normalize email before storage (downcase, strip) via `normalizes`.
- Use `ActiveSupport::SecurityUtils.secure_compare` for token comparison.
- Call `reset_session` before setting `session[:user_id]` on login (prevents session fixation).

---

## 12. HTTP Security Headers

| Header | Purpose |
|--------|---------|
| `X-Frame-Options: SAMEORIGIN` | Prevents clickjacking via iframes |
| `X-Content-Type-Options: nosniff` | Prevents browser MIME type guessing |
| `Referrer-Policy` | Limits referrer data sent to other origins |
| `Permissions-Policy` | Disables unused browser features |
| `Strict-Transport-Security` | Forces HTTPS (set by `force_ssl`) |

- Set via `config.action_dispatch.default_headers`; disable the legacy XSS filter (`X-XSS-Protection: 0`) and rely on CSP.

---

## 13. Gem Vulnerability Scanning

- Add `gem 'bundler-audit'` (development); run `bundle audit check --update` in CI on every build — gem vulnerabilities are the #1 source of Rails security incidents.

---

## 14. Secrets in Version Control

- `.gitignore` must include `config/master.key`, `config/credentials/*.key`, `.env`, `.env.*`, `*.pem`, `*.key`.

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
| Rate limiting on auth endpoints | Required (Rails 7.2+) |
| `bundler-audit` for gem vulnerabilities | Recommended |
| HTTP security headers configured | Recommended |
| `reset_session` after login | Required |
| No `system()`/`exec()` with user input | Required |
| No `Marshal.load`/`YAML.unsafe_load` on untrusted data | Required |
| `.gitignore` includes key files and `.env` | Required |
| Per-environment credentials for production vs staging | Recommended |
