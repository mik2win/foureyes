---
name: write-tests
description: >-
  Generate RSpec tests for a Rails class following project BDD conventions (FactoryBot,
  Shoulda Matchers, verified doubles, comprehensive coverage).
  TRIGGER when the user wants tests written/generated for a Rails model, service,
  controller, or request. Do NOT trigger to run an existing suite or to debug a specific
  failure (use diagnose).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write
  - Edit
---

# Write Tests

Generate an RSpec spec file for the given Rails class or module.

## Input

`$ARGUMENTS` — relative path to the file under test (e.g., `app/services/order_fulfiller.rb`).

If `$ARGUMENTS` is empty, ask the developer which file to test and stop.

## Procedure

### 1. Read the target file

Read the file at `$ARGUMENTS`. Identify:

- Class/module name and namespace
- Public methods (instance and class)
- Constructor parameters and dependencies (injected collaborators)
- Return values, side effects, raised exceptions
- Inheritance and included modules/concerns
- ActiveRecord associations, validations, scopes, enums, callbacks

### 2. Determine the object type

Detect what kind of object it is and adjust coverage accordingly:

| Type | Detection hints | What to test |
|------|----------------|--------------|
| **Model** | Inherits `ApplicationRecord`, lives in `app/models/` | Validations (Shoulda Matchers), associations (Shoulda Matchers), scopes, enums, instance methods, class methods, callbacks with side effects |
| **Service** | Lives in `app/services/`, has `#call` | `#call` happy path, failure paths, side effects on collaborators, return value |
| **Form Object** | Lives in `app/forms/`, includes `ActiveModel::Model` | Validation rules (Shoulda Matchers), `#submit`/`#save` behavior, multi-model persistence |
| **Policy** | Lives in `app/policies/`, methods return boolean | Each policy method with different user roles and record states |
| **Query Object** | Lives in `app/queries/`, returns relations/collections | Various parameter combinations, empty results, chaining, edge cases |
| **Controller** | Lives in `app/controllers/` | Request specs: HTTP status, response body, redirects, side effects, authorization |
| **Job** | Lives in `app/jobs/`, has `#perform` | `#perform` happy path, idempotency, error handling, enqueue behavior |
| **Mailer** | Lives in `app/mailers/` | Mail subject, recipients, body content |
| **Component** | Lives in `app/components/` | Rendered output, conditional display logic |

### 3. Scan project conventions

Before generating, check for existing patterns in the project:

- `spec/rails_helper.rb` — confirm it exists
- `spec/support/` — shared examples, custom matchers, shared contexts
- `spec/factories/` — existing FactoryBot factories for related models
- A nearby existing spec file — match the style already used in the project

### 4. Generate the spec file

Create the spec at the mirror path:

```
app/services/order_fulfiller.rb         -> spec/services/order_fulfiller_spec.rb
app/models/order.rb                     -> spec/models/order_spec.rb
app/controllers/orders_controller.rb    -> spec/requests/orders_spec.rb
app/jobs/fulfillment_job.rb             -> spec/jobs/fulfillment_job_spec.rb
app/mailers/order_mailer.rb             -> spec/mailers/order_mailer_spec.rb
app/components/card_component.rb        -> spec/components/card_component_spec.rb
```

### 5. Follow these conventions

**Structure:**

- `describe` for the class and each public method (`#instance_method`, `.class_method`)
- `context` for scenarios — always starts with `when` or `with`
- `it` for one specific behavior — clear, human-readable sentence
- `subject` for the object under test, using `described_class`
- `let` / `let!` for test data — minimal setup, only what the test needs

**FactoryBot (primary tool for test data):**

- Use `build` for objects that don't need persistence, `create` only when DB state is required
- Use **traits** for variations — never create separate factories for edge cases
- Use `build_stubbed` when you need an object with an ID but no DB hit
- Check `spec/factories/` for existing factories before creating inline data
- If a factory doesn't exist yet, note it but don't create the factory file (just use inline `build`/`create` with attributes)

```ruby
# GOOD — traits for variations
let(:order) { create(:order, :with_items) }
let(:cancelled_order) { create(:order, :cancelled) }

# GOOD — build when DB not needed
let(:order) { build(:order, total: 500) }
```

**Shoulda Matchers (primary tool for model specs):**

- Use for validations: `validate_presence_of`, `validate_uniqueness_of`, `validate_numericality_of`
- Use for associations: `belong_to`, `have_many`, `have_one`
- Use for enums: `define_enum_for`
- Custom domain methods still need hand-written specs

```ruby
describe 'validations' do
  it { is_expected.to validate_presence_of(:title) }
  it { is_expected.to validate_uniqueness_of(:slug).scoped_to(:account_id) }
end

describe 'associations' do
  it { is_expected.to belong_to(:user) }
  it { is_expected.to have_many(:line_items).dependent(:destroy) }
end
```

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

**File header:**

- Always `require 'rails_helper'`

## Template — Model

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe Order, type: :model do
  describe 'associations' do
    it { is_expected.to belong_to(:user) }
    it { is_expected.to have_many(:line_items).dependent(:destroy) }
    it { is_expected.to have_one(:invoice) }
  end

  describe 'validations' do
    it { is_expected.to validate_presence_of(:status) }
    it { is_expected.to validate_numericality_of(:total).is_greater_than_or_equal_to(0) }
  end

  describe 'enums' do
    it { is_expected.to define_enum_for(:status).with_values(draft: 0, confirmed: 1, shipped: 2, cancelled: 3) }
  end

  describe '.recent' do
    let!(:old_order) { create(:order, created_at: 2.months.ago) }
    let!(:new_order) { create(:order, created_at: 1.day.ago) }

    it 'returns orders from the last 30 days' do
      expect(described_class.recent).to include(new_order)
      expect(described_class.recent).not_to include(old_order)
    end
  end

  describe '#total_with_tax' do
    subject(:order) { build(:order, total: 100) }

    it 'returns total plus tax' do
      expect(order.total_with_tax).to eq(110)
    end
  end
end
```

## Template — Service

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe OrderFulfiller do
  subject(:fulfiller) { described_class.new(order, notifier: notifier) }

  let(:order)    { create(:order, :with_items, status: :confirmed) }
  let(:notifier) { instance_double(Notifier, call: true) }

  describe '#call' do
    context 'when order is valid' do
      it 'marks the order as completed' do
        fulfiller.call
        expect(order.reload.status).to eq('completed')
      end

      it 'returns the calculated total' do
        expect(fulfiller.call).to eq(order.line_items.sum(:price))
      end

      it 'sends a notification' do
        fulfiller.call
        expect(notifier).to have_received(:call)
      end
    end

    context 'when order has no items' do
      let(:order) { create(:order, status: :confirmed) }

      it 'returns zero' do
        expect(fulfiller.call).to eq(0)
      end
    end

    context 'when order is already completed' do
      let(:order) { create(:order, status: :completed) }

      it 'raises an error' do
        expect { fulfiller.call }.to raise_error(OrderFulfiller::AlreadyCompletedError)
      end
    end
  end
end
```

## Template — Request Spec (Controller)

```ruby
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'Orders', type: :request do
  let(:user) { create(:user) }

  before { sign_in user }

  describe 'POST /orders' do
    let(:valid_params) { { order: { title: 'New Order', status: :draft } } }

    context 'with valid params' do
      it 'creates an order and redirects' do
        expect { post orders_path, params: valid_params }
          .to change(Order, :count).by(1)
        expect(response).to redirect_to(Order.last)
      end
    end

    context 'with invalid params' do
      it 'renders the form with errors' do
        post orders_path, params: { order: { title: '' } }
        expect(response).to have_http_status(:unprocessable_entity)
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
