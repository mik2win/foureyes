# ActiveRecord queries — worked examples

Companion reference to the `rails-activerecord-queries` rule; loaded on demand.

---

## 1. N+1 Prevention: includes vs preload vs eager_load

The N+1 problem: loading a collection (1 query) then accessing an association on each record (N queries).

```ruby
# BAD — N+1: 1 query for posts + N queries for comments
posts = Post.all
posts.each { |post| puts post.comments.count }
# SELECT "posts".* FROM "posts"
# SELECT COUNT(*) FROM "comments" WHERE "comments"."post_id" = 1
# SELECT COUNT(*) FROM "comments" WHERE "comments"."post_id" = 2
# ... one query per post

# GOOD — eager load eliminates N+1
posts = Post.includes(:comments)
posts.each { |post| puts post.comments.size }
# SELECT "posts".* FROM "posts"
# SELECT "comments".* FROM "comments" WHERE "comments"."post_id" IN (1, 2, 3)
```

| Method | SQL Strategy | Use When |
|--------|-------------|----------|
| `includes` | Decides automatically (separate queries OR LEFT JOIN) | Default choice — Rails picks optimal strategy |
| `preload` | Always separate queries (`SELECT * FROM comments WHERE post_id IN (1,2,3)`) | Large result sets, no WHERE on association |
| `eager_load` | Always LEFT OUTER JOIN | Need to filter/order by association columns |

### SQL Output for Each Strategy

```ruby
# includes — 2 separate queries (default behavior)
Post.includes(:comments).each { |p| p.comments.size }
# SELECT "posts".* FROM "posts"
# SELECT "comments".* FROM "comments" WHERE "comments"."post_id" IN (1, 2, 3)

# includes — switches to JOIN when filtering on association
Post.includes(:comments).where(comments: { approved: true })
# SELECT "posts".* LEFT OUTER JOIN "comments" ON ... WHERE "comments"."approved" = true

# preload — always separate queries
Post.preload(:comments)
# SELECT "posts".* FROM "posts"
# SELECT "comments".* FROM "comments" WHERE "comments"."post_id" IN (1, 2, 3)

# eager_load — always LEFT OUTER JOIN
Post.eager_load(:comments)
# SELECT "posts".*, "comments".* FROM "posts" LEFT OUTER JOIN "comments" ON ...
```

### Decision Tree

- **Default:** `includes` — let Rails decide
- **Filtering/ordering by association columns:** `eager_load` or `includes` with `references`
- **Large dataset, no filtering on association:** `preload`
- **Need to avoid JOIN:** `preload`

```ruby
# GOOD — nested eager loading
Post.includes(comments: :author).where(comments: { approved: true })

# GOOD — multiple associations
Post.includes(:comments, :tags, :author)
```

**Why `references` matters:** String SQL conditions with `includes` need `.references(:comments)` to force a JOIN. Hash conditions auto-detect.

```ruby
# BAD — includes with string WHERE, no references
Post.includes(:comments).where('comments.approved = ?', true)

# GOOD — add references so Rails uses JOIN
Post.includes(:comments).where('comments.approved = ?', true).references(:comments)

# GOOD — hash conditions auto-detect (no references needed)
Post.includes(:comments).where(comments: { approved: true })
```

---

## 2. load_async (Rails 7+)

Dispatch independent queries to background threads. Results materialize when first accessed.

```ruby
# GOOD — independent queries run in parallel
def index
  @posts = Post.published.load_async
  @stats = Stat.current.load_async
  @notifications = current_user.notifications.unread.load_async
  # Queries start immediately; results block only when first accessed
end

# BAD — sequential queries
def index
  @posts = Post.published.to_a          # waits for completion
  @stats = Stat.current.to_a            # waits for completion
  @notifications = current_user.notifications.unread.to_a
end
```

**Why:** Each `load_async` dispatches the query to a background thread. Three 50ms queries execute in ~50ms total instead of ~150ms sequential.

```ruby
# config/database.yml — async queries use a separate internal pool
production:
  adapter: postgresql
  pool: <%= ENV.fetch("RAILS_MAX_THREADS") { 5 } %>
```

---

## 3. Efficient Existence and Counting Checks

| Need | GOOD | BAD | Why |
|------|------|-----|-----|
| Record exists? | `users.exists?` | `users.present?` | `present?` loads ALL records |
| Any records? | `users.exists?` | `users.any?` | `any?` loads records if already loaded |
| Count | `users.count` | `users.length` | `length` loads all, `count` does SQL COUNT |
| Size (cached) | `users.size` | `users.count` | `size` uses counter_cache or loaded? check |
| Single column | `users.pluck(:email)` | `users.map(&:email)` | `map` instantiates AR objects |
| Single value | `users.pick(:email)` | `users.pluck(:email).first` | `pick` adds LIMIT 1 |
| All IDs | `users.ids` | `users.pluck(:id)` | `ids` is semantic alias |

```ruby
# GOOD
User.where(active: true).exists?           # SELECT 1 ... LIMIT 1
User.where(active: true).count             # SELECT COUNT(*)
User.where(active: true).pluck(:email)     # SELECT email FROM users
Order.where(user: current_user).pick(:total) # SELECT total ... LIMIT 1

# BAD
User.where(active: true).present?          # SELECT * (loads ALL)
User.where(active: true).to_a.count        # loads all, counts in Ruby
User.where(active: true).map(&:email)      # instantiates User objects for one column
```

### pluck vs select

```ruby
# pluck — returns plain arrays, no AR objects (reports, exports)
User.where(active: true).pluck(:id, :email)
# => [[1, "alice@example.com"], [2, "bob@example.com"]]

# select — returns AR objects with only specified columns
users = User.active.select(:id, :name, :email)
users.each { |u| u.gravatar_url }  # still an AR object
```

---

## 4. Batch Processing

Never load an entire table into memory.

```ruby
# GOOD — processes in batches (default 1000)
User.find_each do |user|
  UserExportService.new(user).call
end

# GOOD — custom batch size
User.find_each(batch_size: 100) { |user| user.generate_report }

# GOOD — batch as relation (for bulk updates)
User.inactive.in_batches { |batch| batch.update_all(anonymized: true) }

# GOOD — batch context for bulk operations
User.find_in_batches(batch_size: 500) { |group| SolrIndex.import(group) }

# BAD — loads entire table into memory
User.all.each { |user| user.export }
```

| Method | Yields | Use For |
|--------|--------|---------|
| `find_each` | One record at a time | Processing records individually |
| `find_in_batches` | Array of records (batch) | When you need batch context |
| `in_batches` | ActiveRecord::Relation | Bulk updates (`update_all`, `delete_all`) |

**Important:** Batch methods force ORDER BY primary key. You cannot use custom ordering with `find_each`.

```ruby
# GOOD — scoped batching with range
User.where(active: true).find_each { |u| process(u) }
User.find_each(start: 2000, finish: 10_000) { |u| migrate(u) }

# BAD — custom order is silently ignored
User.order(created_at: :desc).find_each { |u| process(u) }
```

---

## 5. Query Objects

Extract complex queries when they span 3+ conditions, involve multiple joins, or appear in multiple places.

```ruby
# app/queries/active_users_query.rb
class ActiveUsersQuery
  def initialize(scope = User.all)
    @scope = scope
  end

  def call(filters = {})
    scope = @scope
    scope = scope.where(active: true)
    scope = scope.where(role: filters[:role]) if filters[:role]
    scope = scope.where('created_at >= ?', filters[:since]) if filters[:since]
    scope = scope.joins(:orders).where('orders.total > ?', filters[:min_spend]) if filters[:min_spend]
    scope
  end
end

# Usage
ActiveUsersQuery.new.call(role: :premium, since: 30.days.ago)
ActiveUsersQuery.new(company.users).call(role: :admin)
```

| Signal | Action |
|--------|--------|
| 3+ conditions with parameters | Extract to query object |
| Same query logic in multiple places | Extract to query object |
| Joins across multiple tables | Extract to query object |
| Simple 1-2 condition query | Keep as scope on model |

---

## 6. SQL Safety

```ruby
# GOOD — parameterized queries (safe from SQL injection)
User.where('email = ?', params[:email])
User.where(email: params[:email])           # hash conditions — always safe
User.where('name ILIKE ?', "%#{User.sanitize_sql_like(params[:q])}%")

# GOOD — Arel for complex queries
users = User.arel_table
User.where(users[:created_at].gt(1.week.ago))

# BAD — string interpolation (SQL INJECTION!)
User.where("email = '#{params[:email]}'")   # attacker: ' OR 1=1 --
User.where("name LIKE '%#{params[:q]}%'")   # SQL injection + no LIKE escaping
```

**Why `sanitize_sql_like`:** The `%` and `_` characters are LIKE wildcards. Without sanitizing, user input `%` matches everything.

```ruby
# GOOD — safe ORDER BY with allowlist
ALLOWED_SORT_COLUMNS = %w[name email created_at].freeze

def sort_column
  ALLOWED_SORT_COLUMNS.include?(params[:sort]) ? params[:sort] : 'created_at'
end

# BAD — user-controlled ORDER BY
User.order(params[:sort])  # attacker: "name; DROP TABLE users--"
```

---

## 7. Efficient Updates and Inserts

```ruby
# GOOD — single SQL statement, bypasses callbacks
User.where(active: false).update_all(anonymized: true)
# UPDATE "users" SET "anonymized" = true WHERE "active" = false

# GOOD — upsert_all (Rails 6+) — insert or update in one statement
User.upsert_all(
  [{ email: 'a@test.com', name: 'Alice' }, { email: 'b@test.com', name: 'Bob' }],
  unique_by: :email
)

# GOOD — insert_all for bulk inserts (skips duplicates)
Tag.insert_all([{ name: 'ruby' }, { name: 'rails' }], unique_by: :name)

# GOOD — delete without loading records
User.where('last_login_at < ?', 2.years.ago).delete_all

# BAD — N individual updates
User.where(active: false).each { |user| user.update(anonymized: true) }
```

| Method | Callbacks | Validations | SQL Queries | Use When |
|--------|-----------|-------------|-------------|----------|
| `update` | Yes | Yes | 1 per record | Need callbacks/validations |
| `update_all` | No | No | 1 total | Bulk data changes |
| `upsert_all` | No | No | 1 total | Insert-or-update in bulk |

---

## 8. EXPLAIN and Query Analysis

```ruby
# Show query plan
User.where(active: true).explain
# => Seq Scan on users  (cost=0.00..1.05 rows=3 width=540)

# With ANALYZE — runs the query and shows real timing
User.where(active: true).explain(:analyze)
# => Seq Scan on users (actual time=0.012..0.013 rows=3 loops=1)
```

| Red Flag | Meaning | Fix |
|----------|---------|-----|
| `Seq Scan` on large table | No index being used | Add appropriate index |
| `Nested Loop` with high rows | N+1 at SQL level | Use joins or includes |
| High `cost` | Expensive operation | Check indexes, simplify query |
| `Sort` without index | Sorting in memory | Add index on ORDER column |

### Adding Indexes

```ruby
class AddIndexesForPerformance < ActiveRecord::Migration[8.0]
  def change
    add_index :users, :email, unique: true              # single column
    add_index :orders, [:user_id, :status]              # composite
    add_index :orders, :created_at,                     # partial
              where: "status = 'pending'"
    add_index :users, [:active, :created_at],           # covering
              include: [:email, :name]
  end
end
```

**Why composite index order matters:** Put the most selective column first. `[:user_id, :status]` helps `WHERE user_id = 1 AND status = 'active'` and `WHERE user_id = 1`, but NOT `WHERE status = 'active'` alone.

---

## 9. Locking

```ruby
# Optimistic — add lock_version column (integer, default: 0, null: false)
order = Order.find(1)
order.update!(status: :shipped)
# => raises ActiveRecord::StaleObjectError if another process updated first

# Pessimistic — database row lock
Order.transaction do
  order = Order.lock.find(1)  # SELECT ... FOR UPDATE
  order.update!(status: :shipped)
end

# with_lock — shorthand for transaction + lock + reload
order.with_lock { order.update!(quantity: order.quantity - 1) }
```

| Type | Mechanism | Use When |
|------|-----------|----------|
| Optimistic | `lock_version` column, raises on conflict | Low contention, user-facing forms |
| Pessimistic | `SELECT ... FOR UPDATE` | High contention, inventory/money |

---

## 10. Scopes and Composition

```ruby
class Article < ApplicationRecord
  scope :published,   -> { where(published: true) }
  scope :recent,      -> { order(created_at: :desc) }
  scope :by_author,   ->(author) { where(author: author) }
  scope :tagged_with, ->(tag) { joins(:tags).where(tags: { name: tag }) }
  # Compose: Article.published.recent.tagged_with('ruby').limit(10)
end

# Scopes return relation even on nil — safe for chaining
scope :by_status, ->(status) { where(status: status) if status }

# BAD — class method returns nil when condition is false, breaks chain
def self.by_status(status)
  where(status: status) if status
end
# Article.by_status(nil).recent — NoMethodError on nil!
```

---

## 11. Common Anti-Patterns

### N+1 in Serializers

```ruby
# BAD — query per post in serializer
class PostSerializer
  def comments_count
    object.comments.count
  end
end

# GOOD — counter cache (add comments_count integer column to posts)
class Comment < ApplicationRecord
  belongs_to :post, counter_cache: true
end

# GOOD — or preload the count
Post.left_joins(:comments)
    .select('posts.*, COUNT(comments.id) AS comments_count').group('posts.id')
```

### Querying Inside Loops

```ruby
# BAD — query per iteration
users.each do |user|
  recent_order = Order.where(user: user).order(created_at: :desc).first
  process(user, recent_order)
end

# GOOD — preload, then iterate
recent_orders = Order.where(user: users)
                     .order(created_at: :desc)
                     .group_by(&:user_id)
users.each { |user| process(user, recent_orders[user.id]&.first) }
```

### Caching a Relation Instead of Data

```ruby
# GOOD — materialize before caching
Rails.cache.fetch('trending', expires_in: 5.minutes) do
  Post.published.order(view_count: :desc).limit(10).to_a
end

# BAD — caches the relation object, still fires query on access
Rails.cache.fetch('trending') { Post.published.order(view_count: :desc).limit(10) }
```

**Why `.to_a`:** Caching an `ActiveRecord::Relation` stores the query builder, not the results.

---

## 12. strict_loading (Rails 6.1+)

Prevent lazy loading — raise an error if an unloaded association is accessed.

```ruby
# Per-query
posts = Post.strict_loading.includes(:comments, :author)
posts.first.comments  # OK — was eager loaded
posts.first.tags      # raises ActiveRecord::StrictLoadingViolationError

# Per-model
class Post < ApplicationRecord
  self.strict_loading_by_default = true
end

# Per-association
has_many :comments, strict_loading: true
```

**Why:** Turns silent N+1 queries into loud errors during development. Forces you to declare all needed associations upfront.

```ruby
# config/environments/development.rb
config.active_record.strict_loading_by_default = true

# config/environments/production.rb
config.active_record.action_on_strict_loading_violation = :log
```

---

## 13. PostgreSQL-Specific Queries

```ruby
# DISTINCT ON — latest record per group in one query
Order.select('DISTINCT ON (user_id) *').order(:user_id, created_at: :desc)

# Lateral join — top N per group
Post.joins("INNER JOIN LATERAL (
  SELECT * FROM comments WHERE comments.post_id = posts.id
  ORDER BY created_at DESC LIMIT 3
) recent_comments ON true")
```

---

## 14. Query Performance Checklist

| Check | How |
|-------|-----|
| N+1 queries? | Enable `strict_loading` or check logs for repeated queries |
| Missing index? | Run `EXPLAIN ANALYZE` on slow queries |
| Loading unnecessary columns? | Use `select` or `pluck` instead of `SELECT *` |
| Loading unnecessary records? | Use `exists?`, `count`, `limit` |
| Updating one by one? | Use `update_all`, `upsert_all` for bulk |
| Query inside a loop? | Preload data before the loop |
| Caching a relation? | Call `.to_a` before caching |
| User input in raw SQL? | Use parameterized queries or hash conditions |
| Large table without batching? | Use `find_each` / `in_batches` |

### Recommended Tools

| Tool | Purpose |
|------|---------|
| `bullet` gem | Detects N+1 and unused eager loading in development |
| `prosopite` gem | N+1 detection for any Ruby code (not just views) |
| `pg_stat_statements` | PostgreSQL extension for tracking slow queries |
| `rack-mini-profiler` | Query count and timing in the browser |
| `explain(:analyze)` | Built-in Rails query plan analysis |
