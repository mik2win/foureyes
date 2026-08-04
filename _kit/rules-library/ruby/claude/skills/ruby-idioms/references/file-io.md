# File and IO

### Always Use Block Form

Block form guarantees the file handle is closed, even on exceptions.

```ruby
# GOOD — block form, auto-closes
File.open('report.csv', 'w') do |file|
  results.each { |r| file.puts(r.to_csv) }
end

# BAD — manual close, leaks on exception
file = File.open('report.csv', 'w')
results.each { |r| file.puts(r.to_csv) }
file.close
```

### Read Strategies

```ruby
# Small files — read entire content
content = File.read('config/categories.yml')

# Large files — read line by line (constant memory)
File.foreach('huge_log.txt') do |line|
  process(line) if line.include?('ERROR')
end

# BAD — reads entire large file into memory
lines = File.readlines('huge_log.txt')  # all lines in array
```

### Path Building

```ruby
# GOOD — File.join handles separators cross-platform
path = File.join('config', 'prompts', 'system.erb')
# => "config/prompts/system.erb"

# GOOD — expand relative to current file
config_path = File.expand_path('../config/settings.yml', __dir__)

# BAD — hardcoded separators
path = 'config' + '/' + 'prompts' + '/' + 'system.erb'
```
