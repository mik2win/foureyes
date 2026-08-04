# Freeze Patterns

### frozen_string_literal: true

Add to **every** Ruby file. This makes all string literals frozen by default, catching accidental mutations early. (Ruby 3.4 introduced "chilled strings": files *without* this magic comment emit a deprecation warning when a literal is mutated — full enforcement was deferred, so the comment stays the explicit, reliable way to opt in.)

```ruby
# frozen_string_literal: true

name = 'hello'
name << ' world'  # => FrozenError! Caught at development time.

# When you need a mutable string:
buffer = +''         # unfrozen empty string
buffer << 'chunk1'
buffer << 'chunk2'

# Alternative:
buffer = String.new
buffer << 'data'
```

### Freeze Constants

```ruby
# GOOD — frozen constants prevent accidental modification
VALID_STATUSES = %w[active inactive suspended].freeze
DEFAULT_CONFIG = { timeout: 30, retries: 3 }.freeze

# BAD — mutable constant, can be modified anywhere
VALID_STATUSES = %w[active inactive suspended]
VALID_STATUSES << 'deleted'  # silently modifies the constant
```

**Note:** `freeze` on an Array or Hash is shallow — it prevents adding/removing elements but doesn't freeze the elements themselves. With `frozen_string_literal: true`, string elements inside frozen arrays are already frozen.
