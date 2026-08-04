---
name: test-spec
disable-model-invocation: true
description: >-
  Spec-first testing — derive tests from a plan/spec file WITHOUT reading the implementation,
  so the spec is the source of truth: a failing test means the CODE is wrong, not the test.
  For pure-logic units (calculations, transforms, validators, parsers, state reducers, filters).
  Enforces verbatim spec-quoting, one-test-per-spec-case coverage, and a deviation report.
  TRIGGER when: a plan/spec (a /prepare plan file, or an inline `f(1.3) → ~1.0` contract) defines
  pure-logic behaviour to verify — either test-first before /implement, or as post-implementation
  spec-conformance. DO NOT TRIGGER when: authoring/refactoring tests by READING an existing module
  (use /test), driving new code red-green from scratch (use /tdd), or covering integration wiring,
  IO/handlers/persistence, or anything needing 3+ mocks (use /test).
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
effort: medium
---

# Spec-First Testing: $ARGUMENTS

`$ARGUMENTS` is one of:
- **Plan/spec path** — a `/prepare` plan or spec file under the backlog location.
- **Inline spec** — `"compute_score(1.3, 'gold') → ~1.0, (0.7, 'gold') → ~0.0"`.

If `$ARGUMENTS` is empty, ask which plan or inline spec to test, then stop.

This skill carries only the invariant spec-first discipline. The test/run commands, test layout, and
framework idioms are read at runtime from `.claude/PROJECT.md` and the installed stack rules — never
hardcoded here.

## Core principle

```
Plan (spec) → Tests from spec → Code → Run tests
                                        │
                                  FAIL? → the CODE is wrong (spec = truth)
                                  PASS? → code matches spec ✓
```

**The spec is the source of truth.** Do **NOT** read the implementation while writing tests — tests
come from the spec alone, so they can't be "written to match the bug". A failing test is a finding
about the code, not a prompt to weaken the test.

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` — **Commands** (`test`, `test:targeted`) and **Architecture** (the test
   layout: where tests, fixtures, and factories live, and the naming convention). If missing or still
   `TEMPLATE`, fall back to the root `CLAUDE.md` (always in context) when it carries the
   commands/test layout — note you're running without a kit profile; only if *neither* has them,
   **STOP** → run `/bootstrap` first.
2. Read `.claude/rules/_generic/testing.md` and every stack testing rule whose `paths` match the
   target module — these carry the concrete framework, assertion style, and factory locations. This
   skill does not restate framework idioms.
3. If `CONTEXT.md` exists, read it so test names use the project's ubiquitous language.

## Phase 1 — Parse the spec (mandatory verbatim quoting)

1. Read the plan at `$ARGUMENTS` (or parse the inline `function(input) → expected_output` form).
   **Do not open the implementation.**
2. **Quote every testable behaviour verbatim** — never paraphrase: function signatures, concrete
   input→output mappings, edge cases, and error conditions, each with its spec line reference.
3. List ALL extracted cases before writing any test, and count them for the coverage check:

```
## Extracted test cases from spec
1. [spec line 45] `compute_score(1.3, "gold") → ~1.0`
2. [spec line 50] `compute_score(bad_input) → raises ValueError`
Total: N cases
```

**Extract only pure logic** — deterministic units with no external boundary: calculations
(`compute_score(x) → number`), transforms/parsers (`parse(raw) → Model`), validators
(`validate(cfg) → bool | raises`), state reducers (`reduce(state, event) → state`), filters
(`check(state) → (factor, blocked)`). **Do NOT extract** integration wiring, network/DB/filesystem
IO, request/message handlers, or anything needing 3+ mocks — those belong to `/test`.

## Phase 2 — Design the test cases

Build a table from the spec — one row per extracted case. Keep the spec's own notation (`~1.0`,
`raises ValueError`); the notation→assertion mapping lives in the reference.

| Function | Input | Expected output | Edge case? |
|----------|-------|-----------------|------------|
| `compute_score` | `(1.0, "gold")` | `~0.5` | boundary |
| `compute_score` | `(bad_input)` | `raises ValueError` | error |

## Phase 3 — Write the tests

**Entering the writing phase → read [`reference/spec-test-patterns.md`](reference/spec-test-patterns.md)**
for the spec-notation→assertion mapping, the table→parametrize pattern, naming, the test skeleton,
missing-implementation handling, and factory/fixture reuse. Render every idiom in **your stack's
framework** (from the installed testing rules), not a hardcoded one.

Non-negotiables:
- Place the test at the project's test path/naming for the target module (PROJECT.md → Architecture);
  the module docstring references the spec file.
- **Concrete assertions** tied to the spec value (`assert result >= 0.9`), never `assert result > 0`
  or `is not None`.
- One spec case → one test (or one parametrized row); a spec table → one parametrized test.
- Reuse the project's factories/fixtures for domain objects (check before building inline); seed all
  randomness; freeze/inject time — the spec cases must be repeatable.

## Phase 4 — Run the tests

Run the **targeted** command (PROJECT.md → Commands → `test:targeted`) on the new test file — never
hardcode the runner. If any test fails, do **NOT** assume the test is wrong → go to Phase 5 and
investigate the code first.

## Phase 5 — Failure investigation (spec = truth)

1. **Show the mismatch** — Expected (from the spec, with file + line) vs Actual (from the run).
2. **Locate the implementation** — grep the source tree for the function under test.
3. **Root-cause it** — ask *"why doesn't the code produce what the spec expects?"* Common causes:
   formula wrong, parameters swapped, missing normalization, edge case unhandled.
4. **Suggest a fix direction for the CODE** — do **not** modify the test to make it pass; the spec
   defines correct behaviour. The one exception: if the **spec itself** is contradictory or wrong,
   **STOP and ask** — do not silently pick a winner.

Worked example → `reference/spec-test-patterns.md`.

## Phase 6 — Verification

- Re-run the **targeted** command — the spec tests behave as expected (pass, or fail pointing at a
  real code defect you've reported).
- Run the **full** `test` command (PROJECT.md → Commands) — no regressions elsewhere.
- Optionally check coverage of the target module if the project defines a coverage command.

For spec tests, **Timely** (the T in FIRST) means *written from the spec before implementation* —
the strongest position, because the test cannot have been shaped by the code.

## Spec-compliance rules

**MUST**: write a test for **every** case extracted in Phase 1; quote the spec line in the test
docstring/comment; report coverage — which cases are tested, which are not.

**CANNOT without asking FIRST**: skip any case (even one that looks redundant); merge cases in a way
that loses coverage; declare a case "too hard to test".

**STOP and ask when**: you want to skip a case, a case describes behaviour that seems genuinely
untestable at this layer, or the spec contradicts itself.

## Output

```markdown
## Spec-based tests: <plan/spec name>

### Extracted cases (from spec)
| # | Spec location | Case | Covered? |
|---|---------------|------|----------|
| 1 | line 45 | `compute_score(1.3, "gold") → ~1.0` | yes |
| 2 | line 50 | `compute_score(bad_input) → raises` | no — skipped (reason) |
**Coverage: X/Y spec cases**

### Spec deviation report — ALWAYS include ("No deviations" if all covered)
| # | Spec said | What I did | Reason |
|---|-----------|-----------|--------|
| 2 | invalid input raises | skipped | user approved — input unreachable in production |

### Tests written
- `<test path>` — N cases (M parametrized)

### Test results
- Passed: X · Failed: Y · Skipped: Z (awaiting implementation)

### Failures (if any)
| Test | Expected (spec) | Actual (code) | Root cause | Fix direction |
|------|-----------------|---------------|------------|---------------|
```

## How this fits the pipeline

- **`/prepare` → plan → `/test-spec` → `/implement`** — the recommended TDD flow: derive failing
  spec tests from the plan, then implement until they pass (the plan is the shared spec).
- **Post-implementation** — run `/test-spec <plan>` after `/implement` to prove the code conforms to
  the spec it was built from.

## Cross-reference

- **`/tdd`** — drives *new* code red→green→refactor one slice at a time. `/test-spec` writes the spec
  tests up front from a written plan; use `/tdd` when there is no spec and you're discovering the
  design as you go.
- **`/test`** — code-first: reads an *existing* module to author/refactor tests for coverage,
  fixtures, async, and antipatterns. `/test-spec` deliberately does **not** read the code.
- **`/implement`** — executes the plan `/test-spec` derived tests from; mirrors its **Commit
  Message** pattern for the block below.

## Commit
*(Only if test files were written, and only if tracked files changed)*

Offer a copy-paste `git add <explicit test paths>` + `git commit` block — follow the **Commit
Message** pattern in `/implement`: explicit paths only (never `-A` / `.` / a bare directory), text
the user pastes (**never run it**), no `Co-Authored-By` trailer.
