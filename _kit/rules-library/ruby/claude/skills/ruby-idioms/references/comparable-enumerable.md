# Including Comparable and Enumerable

### Comparable

Define `<=>` and get `<`, `<=`, `==`, `>=`, `>`, `between?`, `clamp` for free.

```ruby
class Version
  include Comparable

  attr_reader :major, :minor, :patch

  def initialize(version_string)
    @major, @minor, @patch = version_string.split('.').map(&:to_i)
  end

  def <=>(other)
    return nil unless other.is_a?(Version)

    [major, minor, patch] <=> [other.major, other.minor, other.patch]
  end
end

v1 = Version.new('1.2.3')
v2 = Version.new('1.3.0')
v1 < v2              # => true
v1.between?(v1, v2)  # => true
[v2, v1].sort        # => [v1, v2]
```

### Enumerable

Define `each` and get 50+ collection methods. See `enumerable.md` for details.
