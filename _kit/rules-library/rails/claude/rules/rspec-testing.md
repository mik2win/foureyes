---
paths:
  - "spec/**/*_spec.rb"
  - "spec/support/**/*.rb"
  - "spec/factories/**/*.rb"
---

# RSpec Testing Best Practices

Based on RSpec Best Practices (cursor.directory), POODR, and team conventions.

> Worked examples live in the `rspec-reference` skill (`references/rspec.md`).

> **Write tests ONLY when explicitly asked by the developer.**
> Never generate spec files as part of a feature. Never suggest writing tests unsolicited.
> Do NOT run RSpec automatically after edits — the developer runs tests manually.

## Stack

- **RSpec** for all tests (unit, integration, system)
- **FactoryBot** for test data
- **Shoulda Matchers** for model association and validation assertions
- **Capybara** for system/feature tests (sparingly — they are slow)

## Comprehensive Coverage

When writing tests, cover both typical cases and edge cases:
- Happy path (expected behavior)
- Edge cases (boundary values, empty inputs, nil)
- Error conditions (invalid inputs, exceptions)
- Consider all possible scenarios for each method

## Readability and Clarity

- Use clear, descriptive names for `describe`, `context`, and `it` blocks
- Prefer `expect` syntax over `should`
- Keep test code concise; avoid unnecessary complexity
- Write tests that are easy to understand for new developers
- Include comments where the logic being tested is complex

## File Structure

- Test file paths must mirror `app/` structure inside `spec/` (e.g. `app/models/record.rb` → `spec/models/record_spec.rb`; controllers → `spec/requests/`).

## RSpec Structure — BDD Style

Use `describe`, `context`, `it` with clear, human-readable names that form a sentence:

- `describe` for classes/modules or method names
- `context` for scenarios (always starts with "when" or "with")
- `it` for one specific behavior

## Test Data — FactoryBot

- Keep factories minimal. Use **traits** for edge cases, not separate factories.
- Use `let` and `let!` for test data setup. Use `subject` for the object under test.
- Use `let` (lazy) by default; `let!` only when the record must exist before the test runs
- Minimal setup — only create what is necessary for the test
- Use `described_class` instead of repeating class name

## Test Boundaries — Query vs Command

Distinguish **query methods** (return a value) from **command methods** (trigger an action):

- For commands: test the outcome and that the collaborator was used.
- For queries: test the returned value.

**Never test the implementation details of one class in another class's test suite.** Test the contract, not internals.

## Independence and Isolation

- Each test must be independent — no shared mutable state between tests
- Never rely on test execution order
- Use database cleaner or transactional fixtures to ensure clean state

## Model Specs

- Use **Shoulda Matchers** for validations and associations; add custom examples for scopes and domain methods.

## Mocks and Stubs

Use `allow` / `expect` from RSpec. For double objects, use **verified doubles** (`instance_double`):

- For commands: verify invocation. For queries: test output.

**Avoid over-mocking.** Only mock:
- External API calls (network)
- Time-sensitive operations (`Time.current`)
- Expensive operations that don't affect test intent

When possible, test real behavior with real objects.

## Shared Examples and Custom Matchers

- Use shared examples for behaviors that appear across multiple specs.
- Refactor repetitive assertions into **custom matchers** if they appear in 3+ specs.

## What NOT to Test

- Don't write tests that only test Rails or gems (e.g. `record.save` returning true, Devise's encrypted password). Test domain logic instead.

## Coverage Focus

| Test | Skip |
|------|------|
| Business logic in services (critical path) | Simple CRUD scaffolding |
| Complex model methods and scopes | Basic validations already enforced by DB |
| Calculation and domain rules | Framework behavior (Devise, ActiveRecord defaults) |
| Role-based or permission logic | Trivial getters/setters |
| Edge cases and error handling | Gem/library internals |

## Request Specs

- Use request specs for testing controller behavior and API endpoints.

## System Specs

- Use system specs with Capybara for **critical user flows only** — they are slow.
- Keep system specs minimal — only for critical flows (auth, checkout, main CRUD). Test business logic in unit/service specs.

## Require and Setup

- Start spec files with `require 'rails_helper'` and refer to the class under test via `described_class`.
