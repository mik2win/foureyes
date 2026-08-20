---
description: Stack-agnostic testing principles — FIRST, AAA, naming, mock discipline, what to test. Loaded on file read (code work).
paths:
  - "**/*"
---

# Testing (generic)

Framework-neutral. Stack packs name the concrete test runner, fixtures and factories.

## Principles

- **FIRST:** Fast, Independent, Repeatable, Self-validating, Timely.
- **AAA:** Arrange → Act → Assert. One logical assertion target per test.
- Tests are isolated: no shared mutable state, no order dependency, no real network/
  clock/filesystem unless that's the thing under test.
- Same logic over many cases: use the framework's table-driven/parameterized mechanism,
  not copy-pasted test bodies.

## Speed & lanes

- Prefer mocking the boundary to make a test fast over tagging it slow.
- Two lanes: a fast inner-loop suite (unit, milliseconds) you run constantly, and the
  complete pre-merge suite (integration and slow tests included). Keep the fast lane fast.

## Naming

- `test_<unit>_<scenario>_<expected>` (or the stack's idiomatic equivalent).
  A failing test name should tell you what broke without opening the file.

## What to test

- Public behaviour and contracts, not private implementation details.
- Edge cases: empty, boundary, error path, concurrency where relevant.
- Bug fixes start with a failing test that reproduces the bug.
- Don't test: library/framework internals, thin I/O wrappers (test the pure logic they
  wrap), exact rendering character-by-character.

## Mock discipline

- Mock at boundaries (I/O, external services, time), never your own domain logic.
- Over-mocking that mirrors the implementation is a smell — it tests the mock.
- Prefer real objects / factories for domain values; mock only what's slow or external.
- A mock must honor the contract of what it replaces (return shape, side effects the
  code under test depends on) — an unfaithful mock proves nothing.

## Test doubles

| Double | Is | Reach for it when |
|---|---|---|
| Fake | a real, simpler implementation (in-memory repo/cache) | you need working behavior across calls |
| Stub | canned answers to queries | the code just needs *a* value back |
| Mock | records + asserts interactions | the interaction itself is the contract |
| Spy | records calls for later assertion | you want to check calls without scripting them |

- **Prefer fakes over mocks.** A small in-memory implementation is more robust and readable than
  interaction-checking mocks that mirror the implementation and break on every refactor.
- If a test needs more than ~2 mocks, it's probably an integration test — reconsider its scope.

## Forbidden test patterns

Severity-ordered — flag these in any test review:

| Antipattern | Severity | Fix |
|---|---|---|
| Test with no assertion (or `raises`) | CRITICAL | add an assertion or delete — it proves nothing |
| Mocking your own domain logic | CRITICAL | test the real implementation; you're testing the mock |
| Assertion deleted/weakened to make it pass | CRITICAL | fix the code or the test's premise instead |
| Real network / clock / filesystem in a unit test | STRUCTURAL | mock the boundary, or move to the integration lane |
| Unfrozen current time / unseeded randomness | STRUCTURAL | inject a fixed clock / seed |
| Shared mutable state → order dependency | STRUCTURAL | give each test its own state |
| Loop over cases inside one test | STRUCTURAL | use the table-driven/parameterized mechanism |
| `sleep` to wait for timing | STRUCTURAL | control the clock, or remove |
| Hardcoded temp path | STRUCTURAL | use the framework's temp-dir fixture |
| Same setup data inlined across many tests | STRUCTURAL | extract to a factory / shared fixture |
| Asserting on private internals or exact rendering | STYLE | assert on public behavior |

Severity: **CRITICAL** = false confidence / masks bugs; **STRUCTURAL** = hard to change
correctly; **STYLE** = fix when you're already in the file.

## Coverage

- Coverage is a floor, not a goal. A passing suite with no assertions is worthless.
- **A test that did not run counts as missing.** Before calling behaviour covered, confirm the
  covering test actually ran and passed *in the verification output* — one that exists but was
  unregistered, filtered out, skipped or disabled proves nothing, and a green run it never
  entered is indistinguishable from real coverage.
- Don't delete or weaken assertions to make a test pass — fix the code or the test's
  premise.
- Aim higher where logic is pure and cheap to cover, lower where it's mostly I/O:

| Layer | Target | Why |
|---|---|---|
| Domain / pure core | ~100% | pure functions, no excuse to skip |
| Service / orchestration | 80%+ | mock external I/O, cover the wiring |
| Infrastructure / adapters | 60%+ | mostly integration-tested |
| Entry points (handlers, CLI) | smoke | thin shells — a happy-path smoke test |
