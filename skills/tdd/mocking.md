# Mocking (TDD)

**Gate:** read at `/tdd` RED when the slice touches an external boundary (network, DB, clock,
queue). A slice that is pure computation skips this file — the answer there is always "no mock".

The default is **don't**. Mocks are how TDD tests rot into structure-coupled tests that break on
every refactor. Reach for one only at a true external boundary. The stack rules carry the
framework's mocking syntax — this file is the *decision*, not the API.

## The one rule

**Mock external boundaries only. Never mock your own domain logic or same-module internals.**

- ✅ Mock: network calls, the database when you're not testing persistence, the filesystem, the
  clock/`now`, `sleep`, third-party SDKs, message queues.
- ❌ Don't mock: the function under test, its same-module collaborators, value objects, pure
  domain logic. Mocking those tests the *mock*, not the behaviour.

## Why it matters for TDD

A test that mocks internal collaborators passes whether or not the real code works, and breaks the
moment you rename or move an internal — exactly the refactor TDD's third step depends on. If you
*need* to mock an internal to write the test, the design is telling you the **seam is in the wrong
place**: the thing you want to swap should be behind an interface (`/codebase-design`), and your
test should swap a fake at *that* seam instead.

## Prefer a fake at the seam over a mock of calls

- A **fake** (an in-memory implementation of the real interface) lets the test exercise real
  behaviour through the same seam production uses — and survives refactors.
- A **mock that asserts call count/args** couples the test to *how* the code works. Use it only
  when the side effect itself (that the email was sent, that the event was published) is the
  behaviour under test — not when you're really checking a return value.

## Smell: too many mocks

Painful setup is a report about the code, not a problem to write around. Name what it reports before
you reach for a wider seam, a shared fixture, or the integration label:

- a long arrange before the unit will run → the object expects too much context;
- objects dragged in that the assertion never mentions → too many dependencies;
- a stub that must return another stub → the unit reaches through a collaborator for behaviour;
- an expectation too large to state → a value is hard-coded that should have been injected.

Extract and inject what the test is fighting; out of scope here → report it as a finding instead of
writing around it, and widen to integration only when the seam is genuinely wide. The implication
runs one way: cheap tests are not evidence of good design, and a unit's tests are its first reuse.
