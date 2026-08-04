# Rails caching & storage — worked examples

Companion reference to the `rails-caching-storage` rule; loaded on demand.

---

## 1. Fragment Caching

Cache expensive view partials. Rails generates cache keys from the model's `id` and `updated_at`.

```erb
<%# In view (ERB syntax for universality) %>
<% cache @product do %>
  <div class="product">
    <%= render @product %>
  </div>
<% end %>
<%# Cache key: products/123-20240101120000 (id + updated_at) %>

<%# Collection caching — one cache read per item, multi-fetch optimized %>
<%= render partial: 'products/product', collection: @products, cached: true %>
```

### Russian Doll Caching

Nested caches where inner cache invalidation bubbles up via `touch`. When a comment changes, its post's `updated_at` is bumped, expiring the outer cache.

```ruby
class Comment < ApplicationRecord
  belongs_to :post, touch: true  # bumps post.updated_at when comment changes
end
```

```erb
<%# View: outer cache invalidates when any comment changes %>
<% cache @post do %>
  <h1><%= @post.title %></h1>
  <% @post.comments.each do |comment| %>
    <% cache comment do %>
      <%= render comment %>
    <% end %>
  <% end %>
<% end %>
```

**Why Russian Doll:** Only the changed inner fragment and its ancestors regenerate. Unchanged siblings are served from cache.

---

## 2. Low-Level Caching

Use `Rails.cache.fetch` for read-through caching of expensive computations, API calls, or complex queries.

```ruby
# Rails.cache.fetch — read-through cache
def trending_posts
  Rails.cache.fetch('trending_posts', expires_in: 5.minutes) do
    Post.published.order(views_count: :desc).limit(10).to_a  # .to_a materializes!
  end
end

# With race_condition_ttl — prevents thundering herd
Rails.cache.fetch('stats', expires_in: 1.hour, race_condition_ttl: 10.seconds) do
  compute_expensive_stats
end

# Manual invalidation
Rails.cache.delete('trending_posts')

# Conditional caching — per-user data
Rails.cache.fetch("user_#{user.id}_settings", expires_in: 30.minutes) do
  user.compute_settings
end
```

**Why `race_condition_ttl`:** When a cached value expires, multiple processes may simultaneously try to regenerate it. `race_condition_ttl` extends the stale value briefly so only one process regenerates while others serve the old value.

### Cache Key Design

```ruby
# GOOD — includes model state in key (auto-invalidates on change)
Rails.cache.fetch([user, 'dashboard', Date.current]) do
  # key: users/42-20240101/dashboard/2024-01-15
  build_dashboard_data(user)
end

# BAD — static key (stale forever until explicit delete)
Rails.cache.fetch('dashboard_data') { compute_data }
```

### Caching a Relation vs Data

```ruby
# GOOD — materialize before caching
Rails.cache.fetch('trending', expires_in: 5.minutes) do
  Post.published.order(view_count: :desc).limit(10).to_a
end

# BAD — caches the relation object, still fires query on access
Rails.cache.fetch('trending') { Post.published.order(view_count: :desc).limit(10) }
```

**Why `.to_a`:** Caching an `ActiveRecord::Relation` stores the query builder, not the results. The query executes every time the cached relation is accessed.

---

## 3. Solid Cache (Rails 8)

Database-backed cache store. Default in Rails 8. No external dependencies.

```ruby
# config/environments/production.rb
config.cache_store = :solid_cache_store
```

```yaml
# config/cache.yml
production:
  database: cache
  max_age: 604800       # 7 days in seconds
  max_size: 256.megabytes
```

| Criteria | Solid Cache | Redis / Memcached |
|----------|-------------|-------------------|
| Default Rails 8 | Yes | No (external dependency) |
| Persistence | Transactional (DB) | Redis: optional; Memcached: none |
| Throughput | Good for most apps | Better for >10k reads/second |
| Operational cost | Zero (uses existing DB) | Separate service to manage |

**Why Solid Cache:** No Redis dependency. Database-backed. Transactional reliability. Default in Rails 8. Use Redis/Memcached only for ultra-high-throughput caching (>10k reads/second).

```ruby
# Usage is identical to any cache store — Rails.cache.fetch works the same
Rails.cache.fetch('homepage_stats', expires_in: 15.minutes) do
  StatsCalculator.new.compute  # stored in the database, not Redis
end

# Fragment caching in views also uses Solid Cache automatically
# <% cache @product do %> ... <% end %>

# Clearing the cache
Rails.cache.clear       # deletes all entries
Rails.cache.cleanup     # removes expired entries only (Solid Cache auto-cleans)
```

---

## 4. HTTP Caching

Reduce server load by letting browsers and CDNs serve cached responses.

```ruby
# Conditional GET — returns 304 Not Modified when data hasn't changed
def show
  @product = Product.find(params[:id])
  if stale?(@product)
    respond_to do |format|
      format.html
      format.json { render json: @product }
    end
  end
end

# fresh_when — shorthand for simple cases
def show
  @product = Product.find(params[:id])
  fresh_when @product
end

# Collection caching with etag
def index
  @products = Product.published
  if stale?(etag: @products, last_modified: @products.maximum(:updated_at))
    render json: @products
  end
end

expires_in 1.hour, public: true  # Cache-Control headers
```

| Header | Meaning | Use For |
|--------|---------|---------|
| `public` | CDN + browser can cache | Static content, product pages |
| `private` | Browser only | User-specific data |
| `no-cache` | Must revalidate every request | Sensitive data, real-time |
| `max-age=N` | Cache for N seconds | TTL-based expiry |

---

## 5. Counter Caches

Pre-computed counts stored in a column. Eliminates `COUNT(*)` queries.

```ruby
# Migration
add_column :posts, :comments_count, :integer, default: 0, null: false

# Model
class Comment < ApplicationRecord
  belongs_to :post, counter_cache: true
end

# Usage — no COUNT(*) query
@post.comments_count  # reads cached column

# Reset counters (after bulk operations)
Post.reset_counters(post_id, :comments)

# Custom counter cache (different column name)
belongs_to :post, counter_cache: :total_comments
```

**Why:** `@post.comments.count` fires a SQL `COUNT(*)` every time. `counter_cache` reads a pre-computed column — instant, no query.

---

## 6. ActiveStorage

### Model and Upload

```ruby
class User < ApplicationRecord
  has_one_attached :avatar
  has_many_attached :documents
end

# Upload (controller)
def update
  @user.avatar.attach(params[:user][:avatar])
end

# Variants (image processing)
@user.avatar.variant(resize_to_limit: [200, 200])
@user.avatar.variant(resize_to_fill: [100, 100])

# Preprocessed variants (generate on upload, not on first request)
class User < ApplicationRecord
  has_one_attached :avatar do |attachable|
    attachable.variant :thumb, resize_to_fill: [100, 100]
    attachable.variant :medium, resize_to_limit: [300, 300]
  end
end
```

### Direct Uploads

```erb
<%# Direct upload to cloud storage — bypasses Rails server %>
<%= form.file_field :avatar, direct_upload: true %>
<%# Requires: javascript_include_tag "activestorage" %>
```

**Why Direct Uploads:** Files upload directly from the browser to S3/GCS/Azure, bypassing the Rails server. Reduces server memory usage and request time for large files.

### Validations (no built-in -- use custom validators)

```ruby
# app/validators/content_type_validator.rb
class ContentTypeValidator < ActiveModel::EachValidator
  def validate_each(record, attribute, value)
    return unless value.attached?
    unless Array(options[:in]).include?(value.content_type)
      record.errors.add(attribute, :invalid_content_type)
    end
  end
end

# app/validators/file_size_validator.rb
class FileSizeValidator < ActiveModel::EachValidator
  def validate_each(record, attribute, value)
    return unless value.attached?
    if value.byte_size > options[:max]
      record.errors.add(attribute, :too_large,
        max: ActiveSupport::NumberHelper.number_to_human_size(options[:max]))
    end
  end
end

# Usage
class User < ApplicationRecord
  has_one_attached :avatar
  validates :avatar, content_type: { in: %w[image/png image/jpeg] },
                     file_size: { max: 5.megabytes }
end
```

### Service Configuration

```yaml
# config/storage.yml
local:
  service: Disk
  root: <%= Rails.root.join("storage") %>

amazon:
  service: S3
  access_key_id: <%= Rails.application.credentials.dig(:aws, :access_key_id) %>
  secret_access_key: <%= Rails.application.credentials.dig(:aws, :secret_access_key) %>
  region: us-east-1
  bucket: my-bucket
```

```ruby
config.active_storage.service = :amazon   # config/environments/production.rb
config.active_storage.service = :local    # config/environments/development.rb
```

### N+1 Prevention with ActiveStorage

```ruby
# BAD — N+1 queries for attachments
@users = User.all
@users.each { |u| u.avatar.attached? }  # query per user

# GOOD — eager load attachments
@users = User.with_attached_avatar  # no N+1
```

---

## 7. Performance in Views

```ruby
# GOOD — eager load in controller for views
@posts = Post.includes(:author, :tags).published.recent

# GOOD — strict_loading catches missed associations
@posts = Post.strict_loading.includes(:author, :tags)

# BAD — N+1 in view
<% @posts.each do |post| %>
  <%= post.author.name %>      <%# N+1 if not eager loaded %>
  <%= post.tags.map(&:name) %> <%# N+1 again %>
<% end %>
```

### Bullet Gem for N+1 Detection

```ruby
# Gemfile
group :development do
  gem 'bullet'
end

# config/environments/development.rb
config.after_initialize do
  Bullet.enable = true
  Bullet.alert = true              # JS popup
  Bullet.rails_logger = true       # Rails log
  Bullet.add_footer = true         # page footer
end
```

---

## 8. Cache Invalidation Strategies

```ruby
# Touch-based (automatic) — association bumps parent's updated_at
class Comment < ApplicationRecord
  belongs_to :post, touch: true  # any fragment cache keyed on @post auto-invalidates
end

# Key-based (automatic) — cache key includes model version
cache @product  # key: products/123-20240315120000

# TTL-based (expiry)
Rails.cache.fetch('homepage_stats', expires_in: 15.minutes) { compute_stats }

# Manual invalidation
Rails.cache.delete('trending_posts')
```

| Strategy | Pros | Cons | Use When |
|----------|------|------|----------|
| Touch-based | Automatic, precise | Extra DB writes | Fragment caching with associations |
| Key-based | Automatic, no manual work | Old entries linger until evicted | View caching |
| TTL-based | Simple, predictable | Stale during TTL window | Expensive computations, API data |
| Manual | Full control | Easy to forget, creates coupling | Cross-model invalidation |

---

## 9. Cache Warming and Write-Through

```ruby
# Cache warming — pre-populate in background job
class CacheWarmerJob < ApplicationJob
  queue_as :low

  def perform
    Rails.cache.fetch('homepage_stats', expires_in: 1.hour, force: true) do
      StatsCalculator.new.call
    end
  end
end

# config/recurring.yml (Solid Queue, Rails 8)
cache_warmer:
  class: CacheWarmerJob
  schedule: every 30 minutes

# Write-through — update cache immediately when data changes
class ProductUpdater
  def call(product, params)
    product.update!(params)
    Rails.cache.write(["product_card", product],
      ProductCardRenderer.new(product.reload).render, expires_in: 1.day)
  end
end
```

**Why Cache Warming:** Prevents cold-cache latency spikes after deployment or cache eviction.

---

## 10. CDN and Performance Monitoring

```ruby
# CDN configuration
config.action_controller.asset_host = 'https://cdn.example.com'
config.active_storage.resolve_model_to_route = :rails_storage_proxy  # Rails 7+

# Performance monitoring gems
group :development do
  gem 'rack-mini-profiler'  # query count, timing in browser badge
  gem 'memory_profiler'     # ?pp=profile-memory
  gem 'stackprof'           # ?pp=flamegraph
end

# Query logging
config.active_record.verbose_query_logs = true     # shows caller location
config.active_record.query_log_tags_enabled = true  # tags queries with context
```

---

## 11. Caching Decision Table

| Scenario | Strategy | Expiry |
|----------|----------|--------|
| Expensive view partial | Fragment caching | Touch-based (auto) |
| API response data | Low-level `Rails.cache.fetch` | TTL (5-60 min) |
| Static page | HTTP caching (`stale?`) | ETag + Last-Modified |
| Computed dashboard data | Low-level cache | Short TTL + race_condition_ttl |
| Frequently counted associations | `counter_cache` | Real-time (auto) |
| User avatars/files | ActiveStorage + CDN | CDN TTL |

---

## 12. Anti-Patterns

### Caching Without Expiry

```ruby
# BAD — no expiry, stale forever
Rails.cache.write('stats', compute_stats)

# GOOD — always set expires_in
Rails.cache.fetch('stats', expires_in: 1.hour) { compute_stats }
```

### Over-Caching

```ruby
# BAD — caching trivial operations
Rails.cache.fetch("user_#{id}_name") { user.name }  # DB read is faster than cache lookup

# GOOD — cache only expensive operations
Rails.cache.fetch("user_#{id}_permissions", expires_in: 10.minutes) do
  user.compute_permissions  # complex query with joins
end
```

### Storing Large Objects / Missing N+1 in Cached Blocks

```ruby
# BAD — caching entire ActiveRecord objects (large, fragile)
Rails.cache.fetch('featured') { Product.featured.to_a }

# GOOD — cache only the data you need (hashes, not AR objects)
Rails.cache.fetch('featured') do
  Product.featured.pluck(:id, :name, :price).map { |id, name, price| { id:, name:, price: } }
end

# BAD — N+1 inside cache block (slow on cache miss)
Rails.cache.fetch('dashboard') do
  Post.recent.limit(10).map { |p| { title: p.title, author: p.author.name } }  # N+1!
end

# GOOD — eager load inside cache block
Rails.cache.fetch('dashboard') do
  Post.recent.includes(:author).limit(10).map { |p| { title: p.title, author: p.author.name } }
end
```

---

## 13. Database Query Caching

Rails automatically caches SQL query results within a single request — identical queries return cached results without hitting the database again.

```ruby
# Within a single request, the second call uses cache:
User.find(1)  # SQL: SELECT * FROM users WHERE id = 1
User.find(1)  # CACHE: no SQL executed

# This only works within the same request/action.
# Background jobs and console do NOT have query caching.

# Enable query caching explicitly outside of requests:
ActiveRecord::Base.cache do
  User.find(1)  # SQL hit
  User.find(1)  # cached
end

# Disable within a request (for real-time data):
ActiveRecord::Base.uncached do
  Order.where(status: :pending).count  # always hits DB
end
```

**Why it matters:** Query caching silently eliminates duplicate queries in views. But relying on it masks N+1 problems — `strict_loading` is better than hoping the cache saves you.

```ruby
# BAD — relies on query cache to mask N+1
@posts = Post.all
@posts.each do |post|
  post.author.name  # N+1, but "fast" due to query cache on second page load
end

# GOOD — explicit eager loading, no reliance on query cache
@posts = Post.includes(:author)
```

---

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
</content>
</invoke>
