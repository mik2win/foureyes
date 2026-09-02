---
paths:
  - "app/views/**/*"
  - "app/components/**/*.rb"
---

# Rails Caching, Storage & Performance

Based on Rails Guides (Caching, Active Storage), Solid Cache documentation.

> Worked examples live in the `rails-reference` skill (`references/caching-storage.md`).

---

## 1. Fragment Caching

- Cache expensive view partials with `cache @model do ... end`; Rails keys on `id` + `updated_at` (e.g. `products/123-20240101120000`).
- Use collection caching (`render ..., collection:, cached: true`) for lists — one multi-fetch-optimized cache read per item.
- **Russian Doll** — nest caches and add `belongs_to :post, touch: true` so inner changes bump the parent's `updated_at` and bubble up. Only the changed fragment and its ancestors regenerate; unchanged siblings stay cached.

## 2. Low-Level Caching

- Use `Rails.cache.fetch(key, expires_in:)` for read-through caching of expensive computations, API calls, or complex queries.
- Add `race_condition_ttl:` on hot keys — serves the stale value briefly so only one process regenerates (prevents thundering herd).
- Invalidate manually with `Rails.cache.delete(key)`.
- **Cache key design** — include model state (`[user, 'dashboard', Date.current]`) so it auto-invalidates; never a static string that stays stale forever.
- **Materialize before caching** — append `.to_a` (or `pluck`). Caching a bare `ActiveRecord::Relation` stores the query builder, so it re-runs the query on every access.

## 3. Solid Cache (Rails 8)

- Database-backed cache store, default in Rails 8, no external dependencies; set `config.cache_store = :solid_cache_store`. Configure `database` / `max_age` / `max_size` in `config/cache.yml`.
- Usage is identical to any store — `Rails.cache.fetch` and view fragment caching work the same. `Rails.cache.clear` (all) / `cleanup` (expired only; Solid Cache auto-cleans).

| Criteria | Solid Cache | Redis / Memcached |
|----------|-------------|-------------------|
| Default Rails 8 | Yes | No (external dependency) |
| Persistence | Transactional (DB) | Redis: optional; Memcached: none |
| Throughput | Good for most apps | Better for >10k reads/second |
| Operational cost | Zero (uses existing DB) | Separate service to manage |

- Prefer Solid Cache; reach for Redis/Memcached only for ultra-high-throughput (>10k reads/second).

## 4. HTTP Caching

- Let browsers/CDNs serve cached responses. Use `stale?(@model)` (conditional GET → 304) or `fresh_when @model` for simple cases; collections via `stale?(etag:, last_modified:)`.
- Set `Cache-Control` with `expires_in N, public: true`.

| Header | Meaning | Use For |
|--------|---------|---------|
| `public` | CDN + browser can cache | Static content, product pages |
| `private` | Browser only | User-specific data |
| `no-cache` | Must revalidate every request | Sensitive data, real-time |
| `max-age=N` | Cache for N seconds | TTL-based expiry |

## 5. Counter Caches

- Use `counter_cache: true` on `belongs_to` with a `*_count` integer column to eliminate `COUNT(*)` queries — reads the pre-computed column instead of firing SQL each time.
- Custom column via `counter_cache: :total_comments`; fix drift after bulk ops with `Model.reset_counters(id, :assoc)`.

## 6. ActiveStorage

- Attach with `has_one_attached` / `has_many_attached`; upload via `record.attachment.attach(...)`.
- Generate image variants with `.variant(resize_to_limit:/resize_to_fill:)`; declare named/preprocessed variants in the model block so they're built on upload, not on first request.
- **Direct uploads** — `form.file_field :avatar, direct_upload: true` (needs the `activestorage` JS) sends files browser→S3/GCS/Azure, bypassing the Rails server; cuts memory and request time for large files.
- No built-in attachment validations — add custom `ActiveModel::EachValidator`s (content type, file size) and apply via `validates :avatar, content_type:, file_size:`.
- Configure services in `config/storage.yml` (Disk / S3 / etc.) and select per env with `config.active_storage.service`.
- **N+1** — eager load attachments with the `with_attached_*` scope; never check `attached?` in a loop over un-eager-loaded records.

## 7. Performance in Views

- Eager load in the controller for everything the view touches (`includes(:author, :tags)`); use `strict_loading` to surface missed associations. Never trigger associations lazily inside the view (`post.author.name` in a loop is N+1).
- Detect N+1 in development with the `bullet` gem (`Bullet.enable` + alert / rails_logger / add_footer).

## 8. Cache Invalidation Strategies

| Strategy | Pros | Cons | Use When |
|----------|------|------|----------|
| Touch-based | Automatic, precise | Extra DB writes | Fragment caching with associations |
| Key-based | Automatic, no manual work | Old entries linger until evicted | View caching |
| TTL-based | Simple, predictable | Stale during TTL window | Expensive computations, API data |
| Manual | Full control | Easy to forget, creates coupling | Cross-model invalidation |

- Touch-based: `belongs_to :post, touch: true`. Key-based: `cache @product` (key includes version). TTL: `expires_in:`. Manual: `Rails.cache.delete`.

## 9. Cache Warming and Write-Through

- **Warm** cold caches in a background job with `Rails.cache.fetch(..., force: true)` (schedule via `config/recurring.yml` on Solid Queue) — avoids latency spikes after deploy/eviction.
- **Write-through** — update the cache immediately when data changes (`Rails.cache.write([key, model], rendered, expires_in:)` after `update!`).

## 10. CDN and Performance Monitoring

- CDN: `config.action_controller.asset_host`; for ActiveStorage set `config.active_storage.resolve_model_to_route = :rails_storage_proxy`.
- Dev profiling gems: `rack-mini-profiler`, `memory_profiler`, `stackprof`.
- Query insight: `config.active_record.verbose_query_logs` (caller location) and `query_log_tags_enabled` (context tags).

## 11. Caching Decision Table

| Scenario | Strategy | Expiry |
|----------|----------|--------|
| Expensive view partial | Fragment caching | Touch-based (auto) |
| API response data | Low-level `Rails.cache.fetch` | TTL (5-60 min) |
| Static page | HTTP caching (`stale?`) | ETag + Last-Modified |
| Computed dashboard data | Low-level cache | Short TTL + race_condition_ttl |
| Frequently counted associations | `counter_cache` | Real-time (auto) |
| User avatars/files | ActiveStorage + CDN | CDN TTL |

## 12. Anti-Patterns

- **No expiry** — never `Rails.cache.write` without a TTL; always set `expires_in`.
- **Over-caching** — don't cache trivial reads (a DB read beats a cache lookup); cache only expensive operations.
- **Large objects** — cache plain data (hashes via `pluck`), not whole AR objects.
- **N+1 inside the cache block** — eager load (`includes`) within the `fetch` block; a miss otherwise runs N+1.

## 13. Database Query Caching

- Rails auto-caches identical SQL within a single request only; background jobs and the console do not. Wrap explicitly with `ActiveRecord::Base.cache do ... end`; bypass with `ActiveRecord::Base.uncached do ... end` for real-time reads.
- Don't lean on query caching to mask N+1 — prefer explicit `includes` (and `strict_loading`) over hoping the cache saves you.

## 14. Performance Checklist

| Check | How |
|-------|-----|
| Fragment caching on expensive partials? | Wrap with `cache @model do` |
| N+1 queries in views? | `includes` in controller, Bullet gem |
| Counter cache for counts? | `counter_cache: true` on `belongs_to` |
| HTTP caching for API responses? | `stale?` / `fresh_when` in controller |
| Race condition on cache expiry? | `race_condition_ttl` on hot keys |
| Cache warming for cold starts? | Background job before TTL expires |
| ActiveStorage N+1? | `with_attached_*` scope |
| Monitoring in place? | rack-mini-profiler, verbose_query_logs |
| Cache keys include model state? | `[model, context]` not static strings |
| Large objects in cache? | Cache data hashes, not AR objects |
