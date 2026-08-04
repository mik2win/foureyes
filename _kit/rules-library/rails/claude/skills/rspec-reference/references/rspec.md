# RSpec testing — worked examples

Companion reference to the `rspec-testing` rule; loaded on demand.

---

## Comprehensive Coverage

When writing tests, cover both typical cases and edge cases:

```ruby
# GOOD — cover edge cases
describe '#calculate' do
  it 'returns correct total for normal items'
  it 'returns zero when items list is empty'
  it 'handles nil quantity gracefully'
  it 'raises ArgumentError for negative prices'
  it 'applies discount when quantity exceeds threshold'
end

# BAD — only happy path
it 'calculates something'
```

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

## File Structure

Test file paths must mirror `app/` structure inside `spec/`:

```
app/models/record.rb                    → spec/models/record_spec.rb
app/services/order_fulfiller.rb         → spec/services/order_fulfiller_spec.rb
app/controllers/records_controller.rb   → spec/requests/records_spec.rb
app/components/card_component.rb        → spec/components/card_component_spec.rb
```

## RSpec Structure — BDD Style

Use `describe`, `context`, `it` with clear, human-readable names that form a sentence:

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

## Test Data — FactoryBot

Keep factories minimal. Use **traits** for edge cases, not separate factories:

```ruby
# spec/factories/records.rb
FactoryBot.define do
  factory :record do
    title    { 'Default Title' }
    status   { :draft }

    trait :active do
      status { :active }
    end

    trait :archived do
      status       { :archived }
      archived_at  { Time.current }
    end

    trait :with_items do
      after(:create) do |record|
        create_list(:item, 3, record: record)
      end
    end
  end
end
```

Use `let` and `let!` for test data setup. Use `subject` for the object under test:

```ruby
RSpec.describe PricingCalculator do
  subject(:calculator) { described_class.new(items, discounts: discounts) }

  let(:items)     { create_list(:item, 3) }
  let(:discounts) { [] }

  it 'calculates total without discounts' do
    expect(calculator.total).to be > 0
  end
end
```

```ruby
# BAD
before { @a = 1; @b = 2; @c = create(:user); @d = create(:record) }
```

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

# GOOD — test command outcome and that collaborator was used
it 'marks the order as completed' do
  fulfiller.call
  expect(order.reload.status).to eq('completed')
end

it 'sends notification' do
  expect(Notifier).to receive(:new).with(order).and_call_original
  fulfiller.call
end
```

## Model Specs

Use **Shoulda Matchers** for validations and associations; add custom examples for scopes and domain methods:

```ruby
RSpec.describe Record, type: :model do
  describe 'validations' do
    it { is_expected.to validate_presence_of(:title) }
    it { is_expected.to validate_uniqueness_of(:slug) }
  end

  describe 'associations' do
    it { is_expected.to belong_to(:user) }
    it { is_expected.to have_many(:items).dependent(:destroy) }
  end

  describe '.search' do
    let!(:match)    { create(:record, title: 'Found It') }
    let!(:no_match) { create(:record, title: 'Other Thing') }

    it 'returns records matching the query' do
      expect(Record.search('Found')).to include(match)
      expect(Record.search('Found')).not_to include(no_match)
    end
  end
end
```

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

## Shared Examples and Custom Matchers

Use shared examples for behaviors that appear across multiple specs:

```ruby
# spec/support/shared_examples/archivable.rb
RSpec.shared_examples 'archivable' do
  describe '#archive!' do
    it 'sets archived_at to current time' do
      subject.archive!
      expect(subject.archived_at).to be_present
    end
  end
end

# Usage
RSpec.describe Record, type: :model do
  it_behaves_like 'archivable'
end
```

## What NOT to Test

Don't write tests that only test Rails or gems:

```ruby
# BAD — testing ActiveRecord
it 'saves the record' do
  expect(record.save).to be true
end

# BAD — testing Devise internals
it 'has encrypted password' do
  expect(user.encrypted_password).to be_present
end

# GOOD — testing domain logic
it 'calculates total from items and applies discount' do
  expect(calculator.total).to eq(expected_amount)
end
```

## Request Specs

Use request specs for testing controller behavior and API endpoints:

```ruby
RSpec.describe 'Records', type: :request do
  describe 'POST /records' do
    let(:valid_params) { { record: { title: 'New Record', status: :draft } } }

    context 'with valid params' do
      it 'creates a record and redirects' do
        expect { post records_path, params: valid_params }
          .to change(Record, :count).by(1)
        expect(response).to redirect_to(Record.last)
      end
    end

    context 'with invalid params' do
      it 'renders the form with errors' do
        post records_path, params: { record: { title: '' } }
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end
end
```

## System Specs

Use system specs with Capybara for **critical user flows only** — they are slow:

```ruby
RSpec.describe 'User creates a record', type: :system do
  before { driven_by(:rack_test) }

  let(:user) { create(:user) }

  it 'creates a record and shows success message' do
    sign_in user
    visit new_record_path
    fill_in 'Title', with: 'My Record'
    click_button 'Save'
    expect(page).to have_content('Record created')
  end
end
```

## Require and Setup

```ruby
require 'rails_helper'

RSpec.describe OrderFulfiller do
  # described_class refers to OrderFulfiller
end
```
