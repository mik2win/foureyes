# RSpec testing — worked examples

Companion reference to the `rspec-testing` rule; loaded on demand.

---

## Comprehensive Coverage

When writing tests, cover both typical cases and edge cases:
- Happy path (expected behavior)
- Edge cases (boundary values, empty inputs, nil)
- Error conditions (invalid inputs, exceptions)
- Consider all possible scenarios for each method

```ruby
# GOOD — cover edge cases
describe '#calculate' do
  it 'returns the correct sum for positive values'
  it 'returns zero when input is empty'
  it 'handles nil gracefully'
  it 'raises ArgumentError for invalid input'
end

# BAD — only happy path
it 'calculates something'
```

---

## Readability and Clarity

```ruby
# GOOD — readable, clear intent
it 'returns empty array when no items match the filter' do
  result = described_class.new(items).filter_by(:active)
  expect(result).to eq([])
end

# BAD — unclear intent
it 'works' do
  expect(described_class.new(items).filter_by(:active)).to eq([])
end
```

---

## File Structure

Test file paths must mirror source structure inside `spec/`:

```
lib/services/report_generator.rb  → spec/services/report_generator_spec.rb
lib/models/order.rb               → spec/models/order_spec.rb
lib/utils/formatter.rb            → spec/utils/formatter_spec.rb
```

---

## RSpec Structure — BDD Style

Use `describe`, `context`, `it` with clear, human-readable names that form a sentence:

- `describe` for classes/modules or method names
- `context` for scenarios (always starts with "when" or "with")
- `it` for one specific behavior

```ruby
RSpec.describe PricingCalculator do
  describe '#total' do
    context 'when no discounts are applied' do
      it 'returns the sum of all item prices' do
        # ...
      end
    end

    context 'when a percentage discount is applied' do
      it 'reduces the total by the discount amount' do
        # ...
      end
    end

    context 'when items list is empty' do
      it 'returns zero' do
        # ...
      end
    end
  end
end
```

---

## Test Data

Use `let` and `let!` for test data setup. Use `subject` for the object under test.

```ruby
RSpec.describe PricingCalculator do
  subject(:calculator) { described_class.new(items, discounts: discounts) }

  let(:items)     { [Item.new(price: 100), Item.new(price: 200)] }
  let(:discounts) { [] }

  it 'calculates total without discounts' do
    expect(calculator.total).to eq(300)
  end
end
```

### Test Data with Data.define

For pure Ruby projects, use `Data.define` value objects as test data — no factory gem needed:

```ruby
Defect = Data.define(:key, :summary, :category, :subcategory)

RSpec.describe CategoryValidator do
  let(:defect) { Defect.new(key: 'PROJ-1', summary: 'Bug', category: 'Code', subcategory: 'Logic') }

  # Variations with .with()
  let(:defect_without_category) { defect.with(category: nil, subcategory: nil) }
  let(:defect_wrong_category) { defect.with(category: 'Environment', subcategory: 'Network') }
end
```

---

## Test Boundaries — Query vs Command

Distinguish **query methods** (return a value) from **command methods** (trigger an action):

```ruby
class OrderFulfiller
  def call
    result = calculate_total   # query
    order.complete!            # command
    Notifier.new(order).call   # command
    result
  end
end

RSpec.describe OrderFulfiller do
  subject(:fulfiller) { described_class.new(order) }
  let(:order) { Order.new(items: items, status: :pending) }

  # Test command outcome
  it 'marks the order as completed' do
    fulfiller.call
    expect(order.status).to eq(:completed)
  end

  # Test that collaborator was invoked — not its internals
  it 'sends notification' do
    notifier = instance_double(Notifier, call: true)
    allow(Notifier).to receive(:new).with(order).and_return(notifier)
    fulfiller.call
    expect(notifier).to have_received(:call)
  end
end
```

---

## Mocks and Stubs

Use `allow` / `expect` from RSpec. For double objects, use **verified doubles** (`instance_double`):

```ruby
# GOOD — verified double, will fail if method doesn't exist
let(:notifier) { instance_double(Notifier, call: true) }

# Mock external dependency — don't hit real APIs in tests
before do
  allow(ExternalApi).to receive(:fetch).and_return(fixture_data)
end

# For commands: verify invocation
expect(ExternalService).to have_received(:process).with(expected_value)

# For queries: test output
expect(subject.calculate).to eq(expected_result)
```

---

## WebMock for HTTP Isolation

Block all real HTTP in tests. Stub external APIs with predictable responses.

```ruby
# spec/spec_helper.rb
require 'webmock/rspec'
WebMock.disable_net_connect!

# Stub specific endpoints
before do
  stub_request(:post, 'https://api.example.com/v1/chat/completions')
    .with(body: hash_including('model' => 'gpt-4'))
    .to_return(
      status: 200,
      body: { choices: [{ message: { content: '{"score": 2}' } }] }.to_json,
      headers: { 'Content-Type' => 'application/json' }
    )
end

# Simulate error responses
it 'handles server errors gracefully' do
  stub_request(:post, api_url).to_return(status: 500, body: 'Internal Server Error')

  result = client.chat(prompt)
  expect(result.error).to include('server error')
end

# Simulate timeouts
it 'retries on timeout' do
  stub_request(:post, api_url).to_timeout.then
    .to_return(status: 200, body: success_body)

  result = client.chat(prompt)
  expect(result).to be_success
end
```

---

## Shared Examples and Custom Matchers

Use shared examples for behaviors that appear across multiple specs:

```ruby
# spec/support/shared_examples/processable.rb
RSpec.shared_examples 'processable' do
  describe '#process' do
    it 'changes status to processed' do
      subject.process
      expect(subject.status).to eq('processed')
    end
  end
end

# Usage
RSpec.describe Order do
  it_behaves_like 'processable'
end
```

Refactor repetitive assertions into **custom matchers** if they appear in 3+ specs:

```ruby
# spec/support/matchers/be_valid_with.rb
RSpec::Matchers.define :be_valid_with do |attribute, value|
  match do |record|
    record.send("#{attribute}=", value)
    record.valid?
  end
end
```

---

## What NOT to Test

Don't write tests that only test the language, stdlib, or gems:

```ruby
# BAD — testing Ruby itself
it 'adds two numbers' do
  expect(1 + 1).to eq(2)
end

# BAD — testing a gem's behavior
it 'parses JSON' do
  expect(JSON.parse('{"a":1}')).to eq({ 'a' => 1 })
end

# GOOD — testing your domain logic
it 'applies bulk discount when quantity exceeds threshold' do
  expect(calculator.total).to eq(expected_discounted_amount)
end
```

---

## Require and Setup

```ruby
# GOOD
require 'spec_helper'
require_relative '../../lib/services/report_generator'

RSpec.describe ReportGenerator do
  # described_class refers to ReportGenerator
end
```
