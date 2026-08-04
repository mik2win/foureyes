# Structured Logging

### Logger from Stdlib

Inject the logger via constructor (Dependency Injection). Use structured messages.

```ruby
class BatchValidator
  def initialize(validators:, logger: Logger.new($stdout))
    @validators = validators
    @logger = logger
  end

  def call(defects)
    defects.each_with_index do |defect, index|
      start = Process.clock_gettime(Process::CLOCK_MONOTONIC)
      result = validate(defect)
      elapsed = Process.clock_gettime(Process::CLOCK_MONOTONIC) - start

      logger.info("[#{index + 1}/#{defects.size}] #{defect.key}: score=#{result.score} (#{elapsed.round(1)}s)")
    end
  end

  private

  attr_reader :validators, :logger
end
```

### Rules

```ruby
# GOOD — structured context in log messages
logger.info("Validation complete: total=#{total} success=#{success} errors=#{errors} (#{elapsed.round(1)}s)")

# GOOD — log levels for different audiences
logger.debug("Token usage: #{tokens}/#{limit} (#{(tokens.to_f / limit * 100).round(1)}%)")
logger.info("[5/20] PROJ-123: score=2 (1.3s)")
logger.warn("Approaching token limit: #{tokens}/#{limit}")
logger.error("LLM API error for #{defect.key}: #{e.message}")

# BAD — no context, hard to parse
logger.info("Done")
logger.info(result.to_s)
```

### Security: Never Log Credentials

```ruby
# BAD — leaking secrets
logger.debug("Connecting with token: #{ENV['API_TOKEN']}")
logger.info("Auth header: #{headers['Authorization']}")

# GOOD — mask or omit
logger.debug("Connecting to #{url} (token: #{ENV['API_TOKEN']&.slice(0, 4)}...)")
logger.info("Request to #{url}: #{method} (#{body.bytesize} bytes)")
```
