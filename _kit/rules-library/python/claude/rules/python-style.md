---
paths:
  - "**/*.py"
---

# Python Style and Modern Features

Modern Python (3.12+; 3.13/3.14 in production). You know the syntax — this is conventions and the non-obvious choices. See `python-design.md` for structure, `python-testing.md` for tests.

---

## 1. Type Hints

- Full hints on every public signature. Built-in generics (`list[str]`, `dict[str, int]`), `X | None` not `Optional`.
- PEP 695 aliases for domain vocabulary: `type Params = dict[str, float | int | str]`.
- `Callable` from `collections.abc`, never `typing`.
- `Final` + SCREAMING_SNAKE for module constants: `MAX_RETRIES: Final = 5`.

---

## 2. Dataclasses

| Need | Decorator |
|------|-----------|
| Hot path / many instances | `@dataclass(slots=True)` — ~40% less memory, no `__dict__` |
| Value object / event / fact | `@dataclass(frozen=True, slots=True)` — immutable, hashable |
| Computed field | `field(init=False)` + set in `__post_init__` |
| Modified copy | `dataclasses.replace(obj, x=1)` — never mutate frozen |

- Validate invariants in `__post_init__`; raise `ValueError` with the offending value.
- Default `slots=True` unless you need `@cached_property` or dynamic attributes (incompatible with slots).
- **Hashability follows `__eq__`.** A plain `@dataclass` — or any class that defines `__eq__` — gets `__hash__ = None` and raises `TypeError` the moment it enters a `set`/`dict`/`@lru_cache` argument. `frozen=True` generates the matching `__hash__`; a hand-written `__hash__` over a mutable field is worse than the error — mutate that field after insertion and the object goes ghost (`obj in d` is `False` while `d.keys()` still shows it).

---

## 3. Control Flow

- `match/case` for 3+ branches dispatching on shape/value; if/else for 2.
- Walrus to bind-and-test: `if (cached := load(key)) is not None:`.
- Guard clauses first, happy path last, unindented.

```python
match event:
    case ClickEvent(target=t, x=x):  ...
    case CloseEvent(reason=r):       ...
    case _: raise ValueError(f"unhandled: {event!r}")
```

---

## 4. Enums for Dispatch — Not String Compares

`StrEnum` (3.11+) for a closed set of identifiers. Match on members, not raw strings — catches typos at the boundary and makes `match` exhaustive.

```python
class Status(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"

# BAD: if status == "active"      # typo "Active" silently fails
# GOOD: if status is Status.ACTIVE
```

Parse external strings into enums at the edge (`Status(raw)`); pass enums internally.

---

## 5. No Magic Numbers / Strings

Named constant for any literal with meaning. The exceptions are `0`, `1`, `-1` and obvious identity values.

```python
# BAD: if attempts > 5
# GOOD: MAX_RETRIES: Final = 5 ; if attempts > MAX_RETRIES
```

---

## 6. Paths and Files

- `pathlib.Path` exclusively, never `os.path`. Use `/` to join, `.read_text()` / `.write_text()`, `.mkdir(parents=True, exist_ok=True)`.

---

## 7. Comprehensions and Generators

- Comprehension for simple transform/filter; a loop once it needs 2+ clauses or side effects.
- Generator for one-pass streaming over large/unknown-size data. **List** when you need `len`, indexing, multiple passes, or the data is small.
- Don't nest comprehensions more than two levels — extract a named helper.

---

## 8. Naming

| Kind | Rule | Example |
|------|------|---------|
| Class | Noun | `UserRepository`, `ReportBuilder` |
| Function | Verb + object | `compute_score()`, `fetch_profile()` |
| Boolean | `is_`/`has_`/`can_` | `is_valid`, `has_access` |
| Collection | Plural | `users`, `active_slots` |
| Private module/helper | `_` prefix | `_kernels.py`, `_normalize()` |

- One word per concept across the codebase: `fetch` (external) vs `load` (file); `compute` vs `calculate` — pick one. Reserve `get_` for cheap accessors.
- Reveal intent over brevity; short names only for short scopes (`for u in users`).
- Avoid noise words: `data`, `Manager`, `Helper`, `Utils`, `info` — name by what it is.
- File names `snake_case`, matching the primary class; suffix by role (`*_types.py`).

---

## 9. Docstrings

| Visibility | Docstring |
|------------|-----------|
| Public API | Yes — Google style (args/returns/raises that aren't obvious) |
| Internal but complex | One-liner |
| Private helper | No — the name suffices |

No noise docstrings: `"""Constructor."""` on `__init__` or restating the signature adds nothing.

---

## 10. f-strings

- Debug logs: `logger.debug("%s", x)` lazy form — NOT f-strings (see `python-design.md` logging).
- Everywhere else f-strings are preferred. `f"{value=}"` for ad-hoc debug prints (then delete).
- `print()` is for CLIs/REPL only — production code logs.
