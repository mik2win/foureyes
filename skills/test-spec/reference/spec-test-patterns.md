# Spec-Test Writing Patterns & Worked Examples

**Loaded at Phase 3 (Write the tests) of `/test-spec`** — read this when entering the writing phase;
a run that stops after Phase 2 (spec review, no tests written yet) skips it entirely.
Contains: spec-notation → assertion mapping, the table → parametrize pattern, test skeleton, naming,
missing-implementation handling, factory/fixture reuse, and worked examples (failure investigation,
end-to-end flow).

Every code sample here is written in one common idiom for concreteness. **Render it in your stack's
framework** — the concrete runner, assertion helpers, parametrize mechanism, and factory locations
come from the installed stack testing rules and `PROJECT.md`, never from this file.

## Mapping spec values to assertions

| Spec notation | Assertion intent |
|---------------|------------------|
| `→ ~1.0` | approximate-equal with tolerance (e.g. `approx(1.0, abs=0.1)`), or `assert result >= 0.9` |
| `→ ~0.5` | approximate-equal with **relative** tolerance for proportional values |
| `→ 0` | exact equality: `assert result == 0` |
| `→ True / False` | identity: `assert result is True` / `is False` |
| `→ raises ValueError` | expected-exception guard asserting **both** type and message substring |
| `→ float in 0..1` | range assertion: `assert 0.0 <= result <= 1.0` |

Always assert the **specific** spec value or a tolerance around it — never a trivially-true check
(`is not None`, `len > 0`) that passes regardless of behaviour.

## Spec table → parametrized test

When the spec gives multiple input→output pairs for one function, use the framework's
table-driven/parametrize mechanism — one test, N rows — not N copy-pasted functions and not a loop
inside one test.

```
parametrize("weight, tier, min_expected", [
    (1.3, "gold",  0.9),   # high weight, top tier
    (0.7, "gold",  0.0),   # low weight (max 0.1)
    (1.3, "basic", 0.4),   # high weight, lower tier
    (1.0, "gold",  0.4),   # boundary
])
def test_compute_score(weight, tier, min_expected):
    result = compute_score(weight, tier)
    assert result >= min_expected
```

## Test placement & naming

- **Path:** the project's test path/naming for the target module (PROJECT.md → Architecture). The
  module docstring references the spec file it was derived from.
- **Name:** `test_<function>_<scenario>_<expected>` (or the stack idiom) — a failing name must say
  what broke without opening the file. Examples:
  - `test_compute_score_favourable_input_returns_high`
  - `test_validate_config_missing_field_raises_value_error`
  - `test_filter_blocked_returns_zero_factor`

## Test skeleton

```
"""Tests from spec: <plan-or-spec-file-name>.

These tests verify the SPECIFICATION, not the implementation.
A failing test means the CODE is wrong — investigate the code first; the spec is the source of truth.
"""

# Import the unit under test. If it doesn't exist yet, the import fails — that is expected in TDD flow.
from <module> import compute_score


def test_compute_score_high_weight_returns_high():
    # Spec: (1.3, "gold") → ~1.0
    result = compute_score(1.3, "gold")
    assert result >= 0.9, f"expected ~1.0 for high weight, got {result}"


def test_compute_score_low_weight_returns_low():
    # Spec: (0.7, "gold") → ~0.0
    result = compute_score(0.7, "gold")
    assert result <= 0.1, f"expected ~0.0 for low weight, got {result}"
```

## Handle a missing implementation (test-first)

In the TDD flow the code may not exist when the tests are written. Rather than let the whole file
error out, guard the import so the suite reports the cases as **skipped — awaiting implementation**
using the stack's skip-on-missing-import mechanism (e.g. an import-guard that skips the module, or
the framework's `importorskip` helper). Once the code lands, the guard is a no-op and the tests run.

## Reuse factories & fixtures (don't build inline)

Before constructing test data by hand, check the project's existing infrastructure (PROJECT.md →
Architecture, stack rules):

| Need | Where to look |
|------|---------------|
| Complex domain object | the project's factory location — reuse the builder |
| Shared setup across ≥2 files | the nearest shared fixture/setup location |
| One-file helper | a local `_make_*` at the top of the test file |

Always seed randomness and freeze/inject time so cases are **repeatable** — a spec test that varies
run to run can't be a source of truth.

```
def test_transform_is_deterministic():
    data = make_sample(n=100, seed=42)   # repeatable factory input
    assert transform(data) == transform(data)
```

## Determinism / idempotence template

A common spec-level invariant for pure logic — same input, same output:

```
def test_pure_function_deterministic():
    """Same input must always produce the same output."""
    data = make_sample(n=100, seed=42)
    first = compute(data)
    second = compute(data)
    assert first == second
```

## Failure investigation — worked example (Phase 5)

### 1. Show the mismatch
```
Expected (spec): ~1.0 (favourable input)
Actual (code):   0.3
Spec source:     <plan>.md, line 45
```

### 2. Locate the implementation
Grep the source tree for the function name to find where it lives — do this **only now**, during
investigation, never while writing the tests.

### 3. Root-cause it
Ask: *"why doesn't the code produce what the spec expects?"* Common causes:
- formula incorrect
- parameters swapped
- missing normalization (raw value returned instead of a 0..1 score)
- edge case unhandled

### 4. Suggest a fix direction
```
Root cause:    the function returns the raw ratio, not a normalized 0..1 score.
Fix direction: normalize the output against the favourable/unfavourable thresholds.
Do NOT modify the test — the spec defines correct behaviour.
```

## End-to-end flow

```
# 1. Derive tests from the spec (test-first — do not read the implementation)
/test-spec <plan-or-spec path>

# 2. Run the targeted suite — expect failures if the code doesn't exist yet
<test:targeted command from PROJECT.md>

# 3. Implement the code (or hand the plan to /implement)

# 4. Re-run — the spec tests should pass; then run the full suite for regressions
<test command from PROJECT.md>

# 5. Any remaining failure → investigate the CODE, not the tests (spec is the source of truth)
```

### Pipeline integration

```
# TDD flow (recommended): failing spec tests first, then implement to green
/test-spec <plan>      # tests derived from the plan, initially failing
/implement <plan>      # implementation done — the spec tests should pass

# Post-implementation verification: prove the code conforms to its spec
/implement <plan>
/test-spec <plan>      # tests verify the implementation matches the spec
```
