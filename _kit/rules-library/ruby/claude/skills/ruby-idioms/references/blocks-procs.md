# Blocks, Procs, Lambdas

### When to Use What

| Type | Use Case | Arity | Return Behavior |
|------|----------|-------|-----------------|
| **Block** | 95% of cases: iterators, callbacks, resource management | Flexible | N/A (not an object) |
| **Lambda** | Named, reusable code chunks (strategies, callbacks) | Strict | Returns from lambda only |
| **Proc** | Rare; when you need return to exit enclosing method | Flexible | Returns from enclosing method |
| **Method object** | Passing existing methods as blocks | Strict | Returns from method only |

```ruby
# Block — most common
items.each { |item| process(item) }

# Lambda — reusable strategy
json_formatter = ->(data) { data.to_json }
csv_formatter  = ->(data) { data.to_csv }
Formatter.new(strategy: json_formatter)

# Method object — pass method as block
names = users.map(&method(:format_name))
# equivalent to: users.map { |u| format_name(u) }

# Proc — avoid unless you specifically need the return semantics
```

### Execute-Around Pattern

Wrap resource setup/teardown in a method that yields. Guarantees cleanup.

**Why:** The caller focuses on the "what", the method handles setup/teardown. No forgotten `ensure` blocks.

```ruby
# GOOD — execute-around: setup, yield, teardown
def with_timing(label)
  start = Process.clock_gettime(Process::CLOCK_MONOTONIC)
  result = yield
  elapsed = Process.clock_gettime(Process::CLOCK_MONOTONIC) - start
  logger.info("#{label}: #{elapsed.round(2)}s")
  result
end

# Usage — caller only cares about the work
total = with_timing('validation') { validator.call(defect) }
```

```ruby
# GOOD — file handling (Ruby stdlib already does this)
File.open('data.csv', 'w') do |file|
  file.write(csv_content)
end  # file automatically closed

# BAD — manual open/close (easy to leak file handles)
file = File.open('data.csv', 'w')
file.write(csv_content)
file.close  # forgotten on exception
```

### Yielding with Arguments

```ruby
# Yield sends data to the block
def each_with_index_and_total
  total = size
  each_with_index do |item, index|
    yield item, index, total
  end
end

# Checking if block was given
def process(items)
  items.each do |item|
    result = transform(item)
    yield result if block_given?
  end
end
```
