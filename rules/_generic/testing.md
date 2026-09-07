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
- Two lanes: an inner-loop suite under ten seconds — past that it stops being run and the refactor
  net is gone — and an on-demand pre-merge stage for DB, network and real concurrency. A flaky
  test is a broken signal: quarantine it into the second stage or delete it; a rerun verifies nothing.

## Naming

- Name a test as a fact about behaviour in domain words — `delivery_with_a_past_date_is_invalid`;
  never "should". Method-name templates only for utility code; an enforced stack shape wins.

## What to test

- Public behaviour and contracts, not private implementation details.
- Edge cases: empty, boundary, error path, concurrency where relevant.
- Bug fixes start with a failing test that reproduces the bug.
- Don't test: library/framework internals, thin I/O wrappers (test the pure logic they
  wrap), exact rendering character-by-character.

## Mock discipline

- Mock only what crosses the process boundary AND is observed from outside (UNMANAGED: SMTP, a bus,
  a third-party API); assert the outgoing payload at the last type before the call leaves the
  process, not at your own domain-flavoured wrapper — its names are your naming, not the contract.
- A MANAGED dependency (only your app reaches it — its own DB or cache) is never mocked: run the
  real thing, same DBMS vendor as production, in the integration lane and assert its final state.
- Over-mocking that mirrors the implementation is a smell — it tests the mock.
- A double you own is a claim it behaves like the real thing: write the role's contract test once,
  run it against every implementer, fakes included; where types guard the shape, check behaviour parity.

## Test doubles

| Double | Is | Reach for it when |
|---|---|---|
| Fake | a real, simpler implementation (in-memory repo/cache) | you need working behavior across calls |
| Stub | canned answers to queries | the code just needs *a* value back |
| Mock | records + asserts interactions | the interaction itself is the contract |
| Spy | records calls for later assertion | you want to check calls without scripting them |

- **Prefer fakes over mocks.** A small in-memory implementation is more robust and readable than
  interaction-checking mocks that mirror the implementation and break on every refactor.
- The double count is not what makes a test "integration": a unit is a unit of behaviour — one
  test may span several classes — and its double count follows from the unmanaged dependencies touched.

## Forbidden test patterns

Severity-ordered — flag these in any test review:

| Antipattern | Severity | Fix |
|---|---|---|
| Test with no assertion (or `raises`) | CRITICAL | add an assertion or delete — it proves nothing |
| Mocking your own domain logic | CRITICAL | test the real implementation; you're testing the mock |
| Test/case/assertion deleted or weakened without justification | CRITICAL | fix the code or the test's premise; name every removal in the report |
| Expected value computed — the code's formula, a loop, another method | CRITICAL | hard-code the literal from the spec; duplicated expectations are the point |
| Production code branches on "am I under test" (env flag, test mode) | CRITICAL | substitute through a seam in test code; per-environment capability config is fine |
| Real network / clock / filesystem in a unit test | STRUCTURAL | mock the boundary, or move to the integration lane |
| Unfrozen current time / unseeded randomness | STRUCTURAL | inject a fixed clock / seed; second-stage race repro with a calibrated timeout is the one exception |
| Shared mutable state → order dependency | STRUCTURAL | give each test its own state |
| Loop over cases inside one test | STRUCTURAL | use the table-driven/parameterized mechanism |
| `sleep` to wait for timing | STRUCTURAL | control the clock, or remove |
| Hardcoded temp path | STRUCTURAL | use the framework's temp-dir fixture |
| `assert_called` on a query double (returns a value, no side effect) | STRUCTURAL | CQS: stubs are configured, not verified; verify command doubles only |
| The assertion act extracted into a shared helper | STRUCTURAL | abstract setup, never the check; dedup cases via the table mechanism |
| Same setup data inlined across many tests (setup only — never the expectation) | STRUCTURAL | extract to a factory / shared fixture |
| Asserting on private internals or exact rendering | STYLE | test via the public API; a private method demanding its own test is dead code or a missing class — extract it, never widen access |

Severity: **CRITICAL** = false confidence / masks bugs; **STRUCTURAL** = hard to change
correctly; **STYLE** = fix when you're already in the file.

## Coverage

- Coverage is a floor, not a goal. A passing suite with no assertions is worthless.
- **A test that did not run counts as missing.** Before calling behaviour covered, confirm the
  covering test actually ran and passed *in the verification output* — one that exists but was
  unregistered, filtered out, skipped or disabled proves nothing, and a green run it never
  entered is indistinguishable from real coverage.
- Test edits have a direction: appending (a test, a case, an assertion) strengthens; deleting or
  weakening needs breaking-change justification whatever the motive ("redundant", green build).
  Never refactor tests and production code in one step — the unchanged side is the net checking the other.
- Aim higher where logic is pure and cheap to cover, lower where it's mostly I/O:

| Layer | Target | Why |
|---|---|---|
| Domain / pure core | ~100% | pure functions, no excuse to skip |
| Service / orchestration | 80%+ | mock external I/O, cover the wiring |
| Infrastructure / adapters | 60%+ | mostly integration-tested |
| Entry points (handlers, CLI) | smoke | thin shells — a happy-path smoke test |
