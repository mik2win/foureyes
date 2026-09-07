**Gate:** loaded by `/test` Phase 4 when writing new tests. Refactor-only runs skip this file
except §Refactoring conversions. Nothing here is a rule — `rules/_generic/testing.md` carries the
principles; this file carries the worked good/bad shapes the principles are hard to apply without.

# Test writing patterns — good / bad

Examples are written in one concrete language for readability. **The idiom is what transfers,
not the syntax**: the concrete runner, mocking library, temp-dir helper, approx helper and
parametrize mechanism all come from `PROJECT.md` and the installed stack rules. If the stack's
idiom differs from what is written here, the stack wins.

## Naming

```
a statement of fact about the behaviour, in domain words
```

```python
# Good — the failing name alone states the broken behaviour
def test_charging_an_order_with_insufficient_funds_raises_payment_error(): ...
def test_config_with_an_unknown_key_is_rejected(): ...

# Bad — method name baked in: a rename turns the file red for a non-reason
def test_validate_delivery_date_past_date_returns_false(): ...
# Bad — no scenario, no expectation; a failure tells you nothing
def test_order(): ...
def test_case_1(): ...
def test_works(): ...
```

## AAA structure

Three logical sections, no interleaving:

```python
def test_charge_order_full_balance_marks_order_paid():
    # Arrange
    account = make_account(balance=100)
    order = make_order(total=100)

    # Act
    result = charge(account, order)

    # Assert
    assert result.status == "paid"
    assert account.balance == 0
```

- One logical assertion **target** per test; several `assert` lines about the same outcome are
  fine.
- Never put Act inside Assert (`assert f(x) == f(y)`) — call and store first, so a failure
  message shows the value.
- Arrange that the Act never uses is dead code. Delete it.

## Parametrize instead of copies

```python
# Bad — four functions, one behaviour
def test_valid_unit_seconds(): Config(unit="s")
def test_valid_unit_minutes(): Config(unit="m")
def test_valid_unit_hours():   Config(unit="h")
def test_valid_unit_days():    Config(unit="d")

# Good — one table-driven test
@pytest.mark.parametrize("unit", ["s", "m", "h", "d"])
def test_valid_unit_accepted(unit):
    Config(unit=unit)
```

Same logic over ≥2 inputs → one parametrized/table-driven test. **Not** a `for` loop inside one
test function: a loop reports one failure for the whole set and hides which case broke.

## Fixture scope

```python
# Default: per-test scope — a fresh object every time (correct for almost everything)
@pytest.fixture
def make_config():
    def _make(**overrides):
        defaults = dict(unit="h", retries=3, timeout_s=5.0)
        return Config(**{**defaults, **overrides})
    return _make

# Wider scope: justified only for expensive, READ-ONLY setup
@pytest.fixture(scope="session")
def sample_dataset():
    return load_fixture("sample.csv")
```

Never widen the scope of a fixture that mutates state — that is how order-dependence gets in.

## Mock discipline

Boundary rules (what may and may never be mocked) live in `rules/_generic/testing.md`. The
shapes:

```python
# MOCK the external boundary
def test_place_order_sends_market_order(mocker):
    gateway = mocker.patch("orders.service.gateway.create_order")
    gateway.return_value = {"id": "123", "status": "filled"}

    place_order(symbol="X", qty=0.1)

    gateway.assert_called_once_with(symbol="X", type="market", side="buy", amount=0.1)

# DON'T mock your own collaborators — this test proves nothing about the code
def test_checkout(mocker):
    mocker.patch("checkout.compute_total")     # own function
    mocker.patch("checkout.apply_discounts")   # own function
    ...
```

- Patch at the **call site**, not the definition site — the call site is what the unit resolves.
- Assert `call_count`/`call_args` only when the **side effect** (not the return value) is the
  thing under test.
- Use the framework's teardown-safe mocking helper, not a hand-rolled decorator that leaks
  patches into the next test.
- More than ~2 mocks in one test is a design signal, not a test problem: the unit has too many
  boundaries.

## Prefer a fake over a mock

```python
class FakeOrderRepository:
    def __init__(self):
        self._orders = {}

    def save(self, order):
        self._orders[order.id] = order

    def get(self, order_id):
        return self._orders.get(order_id)


def test_order_workflow_persists_the_order():
    repo = FakeOrderRepository()
    OrderService(repo).create(make_order(id="o-1"))
    assert repo.get("o-1") is not None
```

A fake exercises the real contract; a mock only records that you called it. Reach for the mock
when the boundary is genuinely external and stateless (a network call), the fake when it has
state (a store, a queue, a cache).

## Assertion quality

```python
# Bad — passes for the wrong reasons, tells you nothing on failure
assert result is not None
assert len(items) > 0
assert flag == True

# Good — specific, self-documenting
assert result.total_charged == 300
assert "order_id" in payload
assert flag is True
```

- Floats: compare with the stack's tolerance helper (`approx`, `within`, `assertAlmostEqual`),
  never `==`.
- Exceptions: assert **both** the type and the message, and make the message assertion contain
  the offending value — otherwise a differently-caused exception of the same type passes.

```python
with pytest.raises(ValueError, match="unknown unit: 2h"):
    Config(unit="2h")
```

## Isolation

Base invariants (no shared mutable state, no order dependence, no reads from generated
artifacts) are in `rules/_generic/testing.md`. Additionally:

- Filesystem → the framework's temp-dir helper, never a hardcoded path.
- Randomness → always seed (`make_rows(n=200, seed=42)`), never a bare RNG call.
- Time → freeze or inject the clock; never read the real one inside an assertion.
- Mark tests that cross an I/O boundary, and tests that are slow, per the stack's marker
  convention — an unmarked slow integration test degrades the whole suite's lane.

## Refactoring conversions (before / after)

### xUnit class style → plain assertions

```python
# BEFORE
class TestCheckout(unittest.TestCase):
    def setUp(self):
        self.account = make_account(balance=100)

    def test_charge(self):
        result = charge(self.account, make_order(total=100))
        self.assertEqual(result.status, "paid")
        self.assertAlmostEqual(self.account.balance, 0.0, places=6)

# AFTER — shared setUp state inlined into Arrange, merged assertions split
class TestCheckout:
    def test_charge_full_balance_marks_order_paid(self):
        account = make_account(balance=100)
        result = charge(account, make_order(total=100))
        assert result.status == "paid"

    def test_charge_full_balance_empties_the_account(self):
        account = make_account(balance=100)
        charge(account, make_order(total=100))
        assert account.balance == pytest.approx(0.0, abs=1e-6)
```

Two things change, and both matter: `setUp` state becomes visible Arrange, and one test asserting
two different outcomes becomes two tests. A merged test that fails tells you only that *something*
in it broke.

### Parametrize extraction

The same before/after shape as §Parametrize instead of copies: N near-identical `test_valid_*`
functions collapse into one parametrized test, with the varying value as the parameter.
