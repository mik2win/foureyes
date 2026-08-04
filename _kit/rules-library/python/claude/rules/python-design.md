---
paths:
  - "**/*.py"
---

# Python Design and Architecture

SOLID, function/module structure, dependency direction, exceptions, logging. See `python-style.md` for syntax-level conventions.

---

## 1. SOLID (the load-bearing bits)

- **SRP** — one class, one reason to change. If you describe it with "and", split it.
- **DIP** — depend on `Protocol` interfaces (ports), not concretions. Adapters implement ports at the edges; the core never imports an adapter.
- **OCP** — add a new implementation file; existing code untouched. Use a registry/dispatch dict, not a growing if-chain.

### Protocols over ABC

Default to `Protocol` (structural, no inheritance coupling, retroactive conformance). Reach for ABC only when you need shared implementation or `register()`.

```python
class DataSource(Protocol):
    def fetch(self, symbol: str, timeframe: str) -> Frame: ...
```

### Composition over inheritance

Inject collaborators; don't subclass to reuse. Decompose a complex state manager into components behind a Protocol with `to_dict()`/`from_dict()`/`reset()`.

---

## 2. Function Design

| Category | Soft | Hard |
|----------|------|------|
| Pure domain logic | 25 | 40 |
| Setup / orchestration | 40 | 60 |

- Test: "describe it in one sentence without 'and'?" If no → extract.
- **Single level of abstraction** per function — don't mix high-level steps with low-level I/O calls.
- 0–2 args ideal, 3 acceptable, **4+ → parameter object** (a dataclass).
- No boolean flag args that switch behavior — write two functions. (OK for a minor variation.)
- Command/Query separation: a function either does something or returns something, not both (except atomic ops where splitting would race).

---

## 3. Module Decomposition

- Split a `module.py` into a `module/` package once it passes **~300 LOC** or mixes unrelated concerns (types + logic + I/O).
- Naming within the package:

| File | Visibility | Purpose |
|------|------------|---------|
| `types.py` | public | dataclasses, enums, type aliases |
| `<feature>.py` | public | single-concern public API |
| `_impl.py` / `_kernels.py` | private (`_` prefix) | internal helpers, perf-critical internals |

- **No re-exports in `__init__.py`** (keep it empty or docstring-only). Callers import from submodules directly — explicit paths show structure and prevent circular imports.
- Within the subpackage, siblings use relative imports (`from .types import ...`, `from ._impl import ...`).
- After a split: update **all** importers to the new explicit submodule paths (`grep` for the old module path), run the tests, then delete the original monolith — no compatibility re-export shim.

---

## 4. Dependency Direction

Dependencies point inward. Outer layers import inner; never the reverse.

```
Core (config, constants, pure types)
  ← Domain (pure compute: no I/O)
    ← Services (orchestration, repositories)
      ← I/O edges (network, DB, CLI, UI)        ← composition root wires it all
```

- No I/O in domain — same input must give same output.
- Sibling I/O modules don't import each other; communicate via injected callback Protocols, wired at the composition root.
- Wrap external APIs into domain dataclasses at the boundary (anti-corruption layer). External types never leak inward. Validate/parse untrusted input with **Pydantic v2** at that boundary, then hand plain dataclasses inward — keep Pydantic out of the core.

---

## 5. Thin-I/O-Shell over Pure Core

Push I/O to the edges; keep computation pure and testable. The shell is `load → compute → save`.

```python
def compute_totals(frame: Frame, params: Params) -> Series:
    """Pure. No file, no network."""
    ...

def run_and_save(config: Config) -> None:
    """Thin shell: orchestrate only, no business logic."""
    frame = load_frame(config)
    totals = compute_totals(frame, config.params)
    save(totals, config.output_path)
```

---

## 6. Service / Use-Case Structure

A use case (CLI command, request handler) is a thin shell: build config → delegate to a framework-free service function → format output.

- **Service functions take domain types and return domain types** — no framework imports (no Typer/Flask/Rich inside). Presentation stays in the shell; services log or emit callbacks instead of printing.
- Services orchestrate (load → compute → persist) but hold no business logic themselves — that lives in domain functions they call.
- Extract a shared `_prepare_*()` helper when 3+ use cases duplicate the same config/dependency construction.
- Push heavy imports (pandas, ML libs, network clients) **inside** the command function, not module top-level, to keep `--help` / startup fast. The cost: a broken import (typo, missing optional dep) now surfaces only when that command runs — smoke-run every command, not just `--help`.

```python
# Service: no CLI framework, returns a domain result
def run_check(config: Config, transform: Transform) -> Report:
    raw = run_pipeline(config, transform)
    report = build_report(raw)
    save_report(report)
    return report
```

---

## 7. Exceptions

- **Narrow the `try`** to the single line that can fail. Broad try/except hides bugs.
- Catch **specific** types; never bare `except:` (swallows `KeyboardInterrupt`/`SystemExit`). Multiple types: `except (ValueError, KeyError):`.
- Include offending values in the message: `raise ValueError(f"unknown strategy: {name!r}")`.
- **Chain**: `raise DomainError(...) from e` to preserve cause; `from None` only to deliberately suppress.
- Don't use exceptions for expected flow — return `T | None` / a sentinel for "not found", raise for genuine errors (bad input, impossible state).
- Pick the right type: `ValueError` (bad params), `TypeError` (wrong type at public API), `FileNotFoundError`, `RuntimeError` (impossible state).
- **Async**: always re-raise `asyncio.CancelledError` — never swallow it.

```python
try:
    await gather(*tasks)
except asyncio.CancelledError:
    raise                      # propagate cancellation
finally:
    for t in tasks:            # never leave orphaned tasks
        if not t.done():
            t.cancel()
```

- Catch-log-continue silently swallows failures. If you log an error you didn't handle, re-raise.
- Suppress a vetted warning with `warnings.catch_warnings()` scoped to the one call — never a
  global `warnings.filterwarnings("ignore")`. Investigate first (see the generic
  exception-patterns rule: broken feature → replace, don't silence).

---

## 8. Logging Discipline

`logger = logging.getLogger(__name__)` per module. No `print()` in production code.

- **Lazy %-args, never f-strings**: `logger.debug("state: %s", serialize(x))`. An f-string runs `serialize(x)` even when DEBUG is off. Guard truly expensive work with `if logger.isEnabledFor(logging.DEBUG):`.
- Correct level: DEBUG (diagnostics) · INFO (significant expected events) · WARNING (recoverable) · ERROR (needs attention) · CRITICAL (unusable).
- Include correlation context (id/key) in the message so logs are filterable.
- Don't log in tight loops — log at boundaries or sample (`if i % 1000 == 0`). Never log secrets.

```python
# BAD:  logger.debug(f"state: {expensive(x)}")   # always evaluated
# GOOD: logger.debug("state: %s", expensive(x))  # lazy
```
