# Range Usage

Ranges are powerful and idiomatic in Ruby. Use them for iteration, membership, case matching, and slicing.

```ruby
# Iteration
(1..10).each { |n| puts n }
('a'..'z').to_a

# Case matching
case status_code
when 200..299 then :success
when 400..499 then :client_error
when 500..599 then :server_error
end

# Array slicing
items[2..5]      # elements at index 2, 3, 4, 5
items[2...]      # from index 2 to end (endless range, Ruby 2.6+)
items[..3]       # from start to index 3 (beginless range, Ruby 2.7+)

# Membership
(1..100).include?(42)         # => true
(Date.today..Date.today + 7)  # date range for next week

# Cover? — more efficient than include? for large ranges
(1..1_000_000).cover?(500_000)  # O(1) — just compares endpoints
```
