# Enumerable Patterns

Ruby's `Enumerable` module provides 50+ methods. Master the core ones — they replace most loops.

### Core Trio: map, select, reject

```ruby
# map — transform each element
names = users.map { |u| u.name }
names = users.map(&:name)           # shorthand with Symbol#to_proc

# select — keep elements where block is true
active = users.select(&:active?)

# reject — remove elements where block is true
inactive = users.reject(&:active?)
```

### Building Collections: each_with_object

Prefer `each_with_object` over `inject`/`reduce` when building a hash or array. The accumulator is the same object — no need to return it from the block.

```ruby
# GOOD — each_with_object (clear, no accidental nil)
counts = items.each_with_object({}) do |item, hash|
  hash[item.category] = (hash[item.category] || 0) + 1
end

# BAD — inject requires returning the accumulator (easy to forget)
counts = items.inject({}) do |hash, item|
  hash[item.category] = (hash[item.category] || 0) + 1
  hash  # forget this and you get nil on next iteration
end
```

### Transform: flat_map, filter_map, tally

```ruby
# flat_map — map + flatten(1), great for one-to-many transforms
all_tags = articles.flat_map(&:tags)
# e.g., [['ruby', 'code'], ['ruby', 'oop']] → ['ruby', 'code', 'ruby', 'oop']

# filter_map (Ruby 2.7+) — select + map in one pass, skips nil
emails = users.filter_map { |u| u.email if u.active? }

# tally (Ruby 2.7+) — count occurrences
%w[ruby python ruby go ruby python].tally
# => {"ruby"=>3, "python"=>2, "go"=>1}

scores = results.map(&:score).tally
# => {2=>15, 1=>8, 0=>3}
```

### Grouping: group_by, chunk, slice_when

```ruby
# group_by — hash of arrays by key
by_status = orders.group_by(&:status)
# => { :pending => [...], :completed => [...] }

# chunk — consecutive runs of same value
[1, 1, 2, 2, 2, 1].chunk { |n| n }.to_a
# => [[1, [1, 1]], [2, [2, 2, 2]], [1, [1]]]

# slice_when — split when condition changes between consecutive elements
sorted_dates.slice_when { |a, b| b - a > 1 }.to_a  # groups of consecutive dates
```

### Lookups and Checks

```ruby
# find — first match (returns nil if not found)
admin = users.find(&:admin?)

# any? / all? / none? — boolean checks
users.any?(&:active?)
items.all? { |i| i.price > 0 }
errors.none?

# count — with optional block
active_count = users.count(&:active?)

# sort_by — prefer over sort with block (O(n log n) key extractions vs O(n log n) comparisons)
sorted = defects.sort_by(&:key)
```

### Include Enumerable in Your Own Classes

Define `each` and get 50+ methods for free:

```ruby
class DefectCollection
  include Enumerable

  def initialize(defects)
    @defects = defects
  end

  def each(&block)
    @defects.each(&block)
  end

  # Now you get: map, select, find, count, sort_by, group_by, etc.
end

collection = DefectCollection.new(defects)
collection.select { |d| d.score == 0 }
collection.group_by(&:category)
```
