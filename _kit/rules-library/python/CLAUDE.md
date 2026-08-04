# Python Project — Claude Instructions

## Behaviour Rules

### Think, Then Propose
Before implementing, briefly describe what you're going to do and why. One short paragraph. Start coding only after.

### Simplicity First
Small team. Choose the simpler approach. Readable beats clever. YAGNI — don't build for hypothetical futures.

### Tests
**Do NOT write tests unless explicitly asked.** Never include tests in feature plans or generated code unsolicited.

---

## Architecture — Layer Responsibilities

| Layer | Responsibility |
|---|---|
| **Pure core / domain** | Deterministic business logic. No I/O, network, clock, or randomness. Same input → same output. |
| **Service / use-case** | Orchestration: load → compute (call core) → persist/emit. Framework-free, testable. |
| **I/O edges** | CLI, HTTP, DB, external APIs, filesystem. Thin shells that translate to/from the core. |

Dependencies point inward: edges → services → core. No I/O in the core.

---

## Critical Conventions

- **Types:** full type hints on public functions; `Protocol` over ABC for interfaces.
- **Data:** `@dataclass(slots=True)` for internal/hot objects, `frozen=True` for value objects; **Pydantic v2** at I/O boundaries (parsing/validating external input), plain dataclasses within the core.
- **Dispatch:** `match/case` for 3+ branches; `enum`/`StrEnum` instead of magic strings.
- **Paths:** `pathlib.Path`, never string concatenation.
- **Time:** timezone-aware UTC (`datetime.now(UTC)`), never naive datetimes.
- **Errors:** narrow `try` scope, specific exceptions, `raise X from e`; re-raise `asyncio.CancelledError`.
- **Logging:** `logging` with lazy `%`-args, correct levels — never `print()`, never f-strings in debug logs.
- **Async:** `asyncio.TaskGroup` for structured concurrency; never block the loop.

---

## Tooling

Standard modern Python toolchain (2025+) — assume these unless the project says otherwise:

- **`uv`** for environments, dependencies, and the lockfile — not pip/poetry/virtualenv/pyenv (`uv run`, `uv add`, `uv sync`).
- **`ruff`** for both lint and format — replaces black + flake8 + isort.
- **`pyright`** (or `mypy`) in strict mode for type-checking.
- **`pyproject.toml`** is the single source of truth for deps + ruff + type-checker config.
- Invoke them through the project's configured commands; never auto-run (see Prohibited Actions).

---

## Rules (auto-loaded by file path)

| When you edit... | Rules loaded |
|---|---|
| Any `.py` file | python-style, python-design |
| Any `.py` file (if project uses asyncio) | python-async-concurrency |
| Any `.py` file (if project uses pandas/numpy) | python-data |
| Any `.py` file (if project logs / runs as a service) | python-observability |
| `tests/`, `test_*.py`, `*_test.py`, `conftest.py` | python-testing |

For project context, read `.claude/rules/project-overview.md` first (if present).

---

## Prohibited Actions

- Do NOT run tests, linters, or formatters automatically — the developer runs them.
- Do NOT commit to git unless explicitly requested.
- Do NOT modify project rules without asking first.
- Do NOT create documentation files unless explicitly asked.
