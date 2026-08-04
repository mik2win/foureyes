---
paths:
  - "spec/**/*_spec.rb"
  - "spec/support/**/*.rb"
  - "spec/factories/**/*.rb"
---

# RSpec Testing Best Practices

Based on RSpec Best Practices, POODR (Sandi Metz), Eloquent Ruby (Russ Olsen), and team conventions.

> Worked examples live in the `rspec-reference` skill (`references/rspec.md`).

> **Write tests ONLY when explicitly asked by the developer.**
> Never generate spec files as part of a feature. Never suggest writing tests unsolicited.
> Do NOT run RSpec automatically after edits — the developer runs tests manually.

---

## Stack

- **RSpec** for all tests
- **WebMock** to block all real HTTP in tests
- Optionally: SimpleCov for coverage, FactoryBot for test data

> If using FactoryBot, add factory patterns and conventions to your project-specific testing rules.

---

## Comprehensive Coverage

When writing tests, cover both typical cases and edge cases:
- Happy path (expected behavior)
- Edge cases (boundary values, empty inputs, nil)
- Error conditions (invalid inputs, exceptions)
- Consider all possible scenarios for each method

---

## Readability and Clarity

- Use clear, descriptive names for `describe`, `context`, and `it` blocks
- Prefer `expect` syntax over `should`
- Keep test code concise; avoid unnecessary complexity
- Write tests that are easy to understand for new developers
- Include comments where the logic being tested is complex

---

## File Structure

- Test file paths must mirror source structure inside `spec/` (e.g. `lib/models/order.rb` → `spec/models/order_spec.rb`).

---

## RSpec Structure — BDD Style

Use `describe`, `context`, `it` with clear, human-readable names that form a sentence:

- `describe` for classes/modules or method names
- `context` for scenarios (always starts with "when" or "with")
- `it` for one specific behavior

---

## Test Data

Use `let` and `let!` for test data setup. Use `subject` for the object under test.

- Use `let` (lazy) by default; `let!` only when the record must exist before the test runs
- Minimal setup — only create what is necessary for the test
- Use `described_class` instead of repeating class name

### Test Data with Data.define

For pure Ruby projects, use `Data.define` value objects as test data — no factory gem needed. Build variations with `.with()`.

---

## Test Boundaries — Query vs Command

Distinguish **query methods** (return a value) from **command methods** (trigger an action):

- For commands, test the outcome (state change, side effect).
- For collaborators, test that they were invoked — not their internals.

**Never test the implementation details of one class in another class's test suite.** Test the contract, not internals.

---

## Independence and Isolation

- Each test must be independent — no shared mutable state between tests
- Never rely on test execution order
- Use database cleaner or transactional fixtures to ensure clean state

---

## Mocks and Stubs

Use `allow` / `expect` from RSpec. For double objects, use **verified doubles** (`instance_double`):

- For commands: verify invocation.
- For queries: test output.

**Avoid over-mocking.** Only mock:
- External API calls (network)
- Time-sensitive operations
- Expensive operations that don't affect test intent

When possible, test real behavior with real objects.

---

## WebMock for HTTP Isolation

- Block all real HTTP in tests (`WebMock.disable_net_connect!`). Stub external APIs with predictable responses.
- Cover error responses, timeouts, and retries by stubbing the relevant status/behavior.

**Why WebMock over manual mocking:** WebMock catches accidental real HTTP calls. If you forget to stub an endpoint, the test fails loudly instead of making a real request.

---

## Shared Examples and Custom Matchers

- Use shared examples (`shared_examples` / `it_behaves_like`) for behaviors that appear across multiple specs.
- Refactor repetitive assertions into **custom matchers** if they appear in 3+ specs.

---

## What NOT to Test

Don't write tests that only test the language, stdlib, or gems. Test your domain logic instead.

---

## Coverage Focus

| Test | Skip |
|------|------|
| Business logic in services | Simple delegation methods |
| Complex methods with branching | Trivial getters/setters |
| Edge cases and error handling | Language/stdlib behavior |
| Public API of your classes | Private method internals |
| Critical path (money, auth, data) | Gem/library internals |

---

## Require and Setup

- `require 'spec_helper'` and `require_relative` the file under test; rely on `described_class` inside the `describe` block.
