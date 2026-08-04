---
paths:
  - "tests/**/*.py"
  - "**/test_*.py"
  - "**/*_test.py"
  - "**/conftest.py"
---

# Python Testing (pytest)

Conventions and the non-obvious safety rules. See `python-design.md` for what makes code testable.

---

## 1. Structure and Naming

- **AAA** — Arrange / Act / Assert, separated by blank lines.
- Name: `test_<unit>_<scenario>_<expected>` — e.g. `test_parse_empty_input_returns_none`.
- One concept per test; multiple asserts OK only if they verify the same behavior.

```python
def test_discount_single_item_applies_rate():
    items = [Item(price=100.0, qty=1)]          # Arrange
    result = apply_discount(items, rate=0.10)   # Act
    assert result == pytest.approx(90.0)        # Assert
```

---

## 2. FIRST

Fast (ms, no real I/O) · Independent (any order, parallel-safe, no shared mutable state) · Repeatable (freeze time, seed RNG — never rely on `now()` or unseeded randomness) · Self-validating (assert, don't `print`) · Timely (with the code).

Speed targets: unit < 10 ms; integration < 1 s and marked (`@pytest.mark.integration`); register the markers you use in `pyproject.toml`. Prefer mocking the boundary to make a test fast over tagging it slow.

---

## 3. Parametrize, Don't Copy-Paste

```python
@pytest.mark.parametrize("kind", ["sma", "ema", "wma"])
def test_moving_average_returns_nonempty(kind, sample_frame):
    assert compute_ma(sample_frame, kind, length=20).dropna().size > 0
```

---

## 4. Fixtures

- Shared fixtures in `conftest.py`; keep each focused, return in-memory data (no file/network I/O).
- Scope by cost: `function` (default) for mutable state; `session`/`module` only for expensive read-only setup.
- Tear down side-effecting resources in the fixture (yield + cleanup) — signal handlers, connections, thread pools, temp dirs.
- Code that registers signal handlers must save and restore the originals (`old = signal.signal(...)` → restore in cleanup). A leaked handler outlives the test; during interpreter shutdown a stale handler logging to closed stdout hangs the run. A mocked `signal.signal` must honor the real contract and return the previous handler.

---

## 5. Mock Only at Boundaries

Mock external I/O (network, third-party API, DB, clock). **Never mock your own domain functions** — that tests the mock, not the code.

```python
# GOOD — mock the external edge, assert the call
def test_signup_sends_welcome_email(mocker):
    api = mocker.patch("accounts.mailer.send", return_value={"id": "1"})
    register_user("ada@example.com")
    api.assert_called_once()

# BAD — mocking internal collaborators
mocker.patch("accounts.build_profile")     # don't
```

Prefer a **fake** (small working in-memory implementation) over a mock for repositories/stores. Test doubles: fake (working) · stub (canned value) · mock (verify interaction) · spy (record).

---

## 6. What to Test

- Behavior and contracts, not implementation. Edge cases: empty, boundary, max/min, invalid input.
- **Bug-repro-first**: every bug fix starts with a failing test that reproduces it.
- Domain-specific invariants explicitly (ordering, symmetry, no look-ahead, warmup exclusion — whatever your domain guarantees).
- Skip: stdlib/3rd-party internals, external network, thin I/O wrappers (test the pure logic they wrap).
- **Coverage is a floor, not a goal.** Pure domain → 100%; services → high with edges mocked; I/O → smoke/integration.

### Forbidden test patterns (flag in any test review)

| Antipattern | Severity | Fix |
|-------------|----------|-----|
| Test with no `assert` / `pytest.raises` | CRITICAL | add an assertion or delete — it proves nothing |
| `setUp` assigning `self.*` state | CRITICAL | `@pytest.fixture` or a local `_make_*` helper — setUp hides Arrange |
| Mocking your own domain modules | CRITICAL | remove — test the real implementation (see §5) |
| `class TestFoo(unittest.TestCase)` | STRUCTURAL | drop the base class; plain pytest functions |
| `self.assertRaises(E, fn, arg)` | STRUCTURAL | `with pytest.raises(E): fn(arg)` |
| `time.sleep(N)` in a test | STRUCTURAL | mock the sleep or remove it |
| Unfrozen `datetime.now()` / unseeded RNG | STRUCTURAL | freeze time / seed via fixture |
| Hardcoded `/tmp/...` paths | STRUCTURAL | `tmp_path` fixture |
| Same fixture data built inline in 5+ tests | STRUCTURAL | move to a factory / nearest `conftest.py` |
| `self.assertEqual(a, b)` / `assertIn` | STYLE | plain `assert a == b` / `assert x in c` |

---

## 7. Async Test Safety

The dangerous footgun: a mocked `asyncio.sleep` returns instantly, so a `while running:` loop spins at CPU speed — millions of allocations/sec → OOM and a frozen machine.

- **Bound every async test** that drives a loop: `@pytest.mark.timeout(N)`.
- pytest-xdist masks the explosion: the OOM-killed worker just reports as a crashed worker while the main process survives — a "crashed worker" failure is a spin-loop suspect.
- **Give the loop a termination condition** — side_effect that raises `CancelledError` after N iterations.
- In production loops, defend with an iteration counter that bails when `time.monotonic()` deltas stay sub-second (`asyncio.sleep(0)` does NOT help — it's mocked too).
- **No orphaned tasks**: `asyncio.gather` does not cancel siblings on failure — cancel all tasks in `finally`.
- **Cancellation propagates**: re-raise `asyncio.CancelledError`, never swallow it.

```python
@pytest.mark.asyncio
@pytest.mark.timeout(10)            # fail fast — don't freeze the system
async def test_loop_handles_errors(mocker):
    mocker.patch("svc.asyncio.sleep", new_callable=AsyncMock)

    calls = 0
    async def stop_after_three(*_):
        nonlocal calls
        calls += 1
        if calls >= 3:
            raise asyncio.CancelledError    # terminates the loop
        raise ConnectionError
    ...
```
