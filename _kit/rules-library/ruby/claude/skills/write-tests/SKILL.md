---
name: write-tests
description: >-
  Generate RSpec tests for a Ruby class or module following project BDD conventions
  (verified doubles, comprehensive coverage).
  TRIGGER when the user wants tests written/generated for a Ruby class or module. Do NOT
  trigger to run an existing suite or to debug a specific failure (use diagnose).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Edit
---

# Write Tests

Generate an RSpec spec file for the given Ruby class or module.

## Input

`$ARGUMENTS` — relative path to the file under test (e.g., `lib/services/order_fulfiller.rb`).

If `$ARGUMENTS` is empty, ask the developer which file to test and stop.

## Procedure

### 1. Read the target file

Read the file at `$ARGUMENTS`. Identify:

- Class/module name and namespace
- Public methods (instance and class)
- Constructor parameters and dependencies (injected collaborators)
- Return values, side effects, raised exceptions
- Inheritance and included modules

### 2. Determine the object type

Detect what kind of object it is and adjust coverage accordingly:

| Type | Detection hints | What to test |
|------|----------------|--------------|
| **Model** | Inherits from a base model, lives in `models/` | Validations, associations, scopes, instance methods, class methods, callbacks with side effects |
| **Service** | Lives in `services/`, has `#call` | `#call` happy path, failure paths, side effects on collaborators, return value |
| **Form Object** | Lives in `forms/`, includes `ActiveModel` | Validation rules, `#submit`/`#save` behavior, multi-model persistence |
| **Policy** | Lives in `policies/`, methods return boolean | Each policy method with different roles/contexts |
| **Query Object** | Lives in `queries/`, returns relations/collections | Various parameter combinations, empty results, edge cases |
| **Controller** | Lives in `controllers/` | Request specs: HTTP status, response body, redirects, side effects |
| **Job** | Lives in `jobs/`, has `#perform` | `#perform` happy path, idempotency, error handling |
| **Plain Ruby** | Anything else | Public API: every public method, constructor edge cases |

### 3. Scan project conventions

Before generating, check for existing patterns in the project:

- `spec/spec_helper.rb` or `spec/rails_helper.rb` — which require to use
- `spec/support/` — shared examples, custom matchers, shared contexts
- `spec/factories/` — existing factories (if FactoryBot is present)
- A nearby existing spec file — match the style already used in the project

### 4. Generate the spec file

Create the spec at the mirror path:

```
lib/services/order_fulfiller.rb   -> spec/services/order_fulfiller_spec.rb
lib/models/order.rb               -> spec/models/order_spec.rb
lib/utils/formatter.rb            -> spec/utils/formatter_spec.rb
app/services/order_fulfiller.rb   -> spec/services/order_fulfiller_spec.rb
app/models/order.rb               -> spec/models/order_spec.rb
```

### 5. Follow these conventions

**Structure:**

- `describe` for the class and each public method (`#instance_method`, `.class_method`)
- `context` for scenarios — always starts with `when` or `with`
- `it` for one specific behavior — clear, human-readable sentence
- `subject` for the object under test, using `described_class`
- `let` / `let!` for test data — minimal setup, only what the test needs

**Doubles and mocking:**

- Use `instance_double` (verified doubles) for all collaborator dependencies
- `allow` / `expect(...).to have_received` for command methods
- Direct assertion on return values for query methods
- Only mock: external APIs, time-sensitive operations, expensive side effects
- Never over-mock — test real behavior when practical

**Coverage per test file:**

- Happy path for every public method
- Edge cases: nil inputs, empty collections, boundary values
- Error conditions: invalid arguments, raised exceptions
- For commands: verify side effects happened
- For queries: verify return values

**Test data:**

- For pure Ruby projects: use `Data.define` value objects or plain Ruby objects
- If FactoryBot is available: use `create` / `build` with traits
- Keep data minimal — only attributes relevant to the test

**File header:**

- `require 'spec_helper'` (or `require 'rails_helper'` if Rails project)
- `require_relative` to the source file (for non-Rails projects)

## Template — Service

```ruby
# frozen_string_literal: true

require 'spec_helper'
require_relative '../../lib/services/order_fulfiller'

RSpec.describe OrderFulfiller do
  subject(:fulfiller) { described_class.new(order, notifier: notifier) }

  let(:order)    { Order.new(items: items, status: :pending) }
  let(:items)    { [Item.new(price: 100), Item.new(price: 200)] }
  let(:notifier) { instance_double(Notifier, call: true) }

  describe '#call' do
    context 'when order is valid' do
      it 'marks the order as completed' do
        fulfiller.call
        expect(order.status).to eq(:completed)
      end

      it 'returns the calculated total' do
        expect(fulfiller.call).to eq(300)
      end

      it 'sends a notification' do
        fulfiller.call
        expect(notifier).to have_received(:call)
      end
    end

    context 'when order has no items' do
      let(:items) { [] }

      it 'returns zero' do
        expect(fulfiller.call).to eq(0)
      end
    end

    context 'when order is already completed' do
      let(:order) { Order.new(items: items, status: :completed) }

      it 'raises an error' do
        expect { fulfiller.call }.to raise_error(OrderFulfiller::AlreadyCompletedError)
      end
    end
  end
end
```

## Rules

- Do NOT run RSpec after generating the file — the developer runs tests manually
- Do NOT modify the source file — only create/update the spec file
- If a spec file already exists at the target path, read it first and extend it rather than overwriting
- Ask the developer before overwriting an existing spec
- Use `frozen_string_literal: true` in every generated file
