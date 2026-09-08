# What a good test looks like (TDD)

**Gate:** read at `/tdd` RED when writing the slice's test; a run already following an approved
`/test-spec` skips it — the spec's assertions are the reference there.

This file is a quick reference for the RED step. The full discipline lives in
`rules/_generic/testing.md` and the installed stack testing rules — this only highlights what
matters most *while driving code test-first*. Don't restate framework idioms here; defer to the
stack rules for syntax, assertion style, and fixtures.

## A good test reads like a specification

The name states the capability; the body proves it through the public interface:

```
test_user_can_checkout_with_valid_cart
test_cancel_on_already_shipped_order_is_rejected
test_empty_cart_total_is_zero
```

If a failing name doesn't tell you what broke without opening the file, rename it. No
`test_works`, `test_case_1`, `test_process`.

## Through the interface, not the internals

- Exercise the **public interface** of the unit under test — call it the way real callers do.
- Verify the **observable outcome** (return value, emitted event, persisted state *read back
  through the interface*) — not a private field or an internal call you happened to make.
- A test that needs to reach inside the implementation is a signal the **seam is wrong** — move it
  (`/codebase-design` → DEEPENING.md) rather than mocking deeper.
- Crossing the persistence boundary: assert on the value re-read through a fresh session or query,
  not the object arrange handed you; clear shared state at the start of the test, not in teardown.

## One behaviour per test

Arrange → Act → Assert, no interleaving. One logical outcome per test (several assert lines for the
*same* outcome are fine). Store the result, then assert on it — never call the unit inside the
assertion.

## Assert real values

- Assert the **specific** expected value, not `is not None` / `len > 0` / "didn't throw".
- For exceptions, assert **both type and message** (message contains the offending value).
- Floats: compare with a tolerance helper, never `==`.

## Reproduce-first for bug fixes

The first slice of a bug fix is a test that **fails because the bug exists** — it reproduces the
reported behaviour. Watch it fail for that reason, then write the fix and watch it pass. That test
is the regression guard; it stays.

## Determinism

Seed randomness, freeze/inject the clock, use the framework's temp-dir helper — never the real
clock, real network, or hardcoded paths in a unit test. A flaky test is worse than no test: it
trains everyone to ignore red.
