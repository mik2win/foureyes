# Hash, Array, and Set Patterns

## Hash Patterns

### Symbol vs String Keys

```ruby
# GOOD — symbol keys for internal data
config = { timeout: 30, retries: 3 }

# GOOD — string keys for external data (JSON, API responses)
parsed = JSON.parse(response.body)  # => { "status" => "ok", "data" => [...] }

# Convert when crossing boundaries
parsed.transform_keys(&:to_sym)     # string → symbol
config.transform_keys(&:to_s)       # symbol → string
```

### Safe Access: dig and fetch

```ruby
# dig — safe nested access (returns nil if any key missing)
name = response.dig(:user, :profile, :name)

# fetch — raises KeyError by default (catches bugs)
timeout = config.fetch(:timeout)              # raises if missing
timeout = config.fetch(:timeout, 30)          # default value
timeout = config.fetch(:timeout) { calculate_default }  # lazy default

# BAD — silent nil on missing key
timeout = config[:timeuot]  # typo returns nil, no error
```

### Transform and Combine

```ruby
# slice — extract subset of keys
user_params = params.slice(:name, :email, :role)

# except — remove specific keys (Rails or Ruby 3.0+ with require 'core_ext')
public_attrs = user.attributes.except(:password_hash, :token)

# transform_values — modify all values
normalized = scores.transform_values { |v| v.round(2) }

# merge — combine hashes (right wins on conflict)
defaults = { retries: 3, timeout: 30 }
config = defaults.merge(user_config)

# ** splat — in method calls
def create_user(**attrs)
  User.new(**defaults, **attrs)
end
```

## Array and Set

### Set for Uniqueness

`Set` provides O(1) `include?` vs Array's O(n). Built-in since Ruby 3.2 — no `require` needed.

```ruby
# GOOD — Set for membership checks
VALID_CATEGORIES = Set['Code Defect', 'Data Defect', 'Environment', 'Integration']

def valid_category?(category)
  VALID_CATEGORIES.include?(category)  # O(1)
end

# BAD — Array for membership checks on large collections
VALID_CATEGORIES = ['Code Defect', 'Data Defect', 'Environment', 'Integration']
VALID_CATEGORIES.include?(category)  # O(n)
```

### Windowing: each_cons, each_slice

```ruby
# each_cons — sliding window of N consecutive elements
[1, 2, 3, 4, 5].each_cons(3).to_a
# => [[1, 2, 3], [2, 3, 4], [3, 4, 5]]

# each_slice — split into chunks of N
items.each_slice(100) do |batch|
  process_batch(batch)  # process 100 at a time
end
```

### Prefer Readable Predicates

```ruby
# GOOD
return if items.empty?
results.any?(&:failed?)

# BAD
return if items.size == 0
return if items.length == 0
results.select(&:failed?).size > 0
```
