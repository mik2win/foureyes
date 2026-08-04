---
name: test
disable-model-invocation: true
description: >-
  Author new tests or refactor existing ones — layer classification, inventory & gap
  analysis, test-design table, AAA/naming/mock discipline, async safety, antipattern
  cleanup, and coverage verification. Covers both writing tests from scratch and
  improving the quality of tests that already exist.
  TRIGGER when: the user wants to write/add/generate tests for a file, directory, or
  feature, OR to audit/refactor/clean up existing tests.
  DO NOT TRIGGER when: the user wants to build NEW code test-first (use /tdd), only wants to run
  the existing suite, or wants to debug a specific failure (use /diagnose — but come back here to
  lock the fix with a test).
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Agent
effort: high
---

# Test Authoring & Refactoring

Target: $ARGUMENTS — one of:
- A **source file/dir** (`<src>/foo`) → write tests for it.
- A **test file/dir** → audit and refactor existing tests.
- A **description** (`"login error isolation"`) → write targeted scenarios.
- `staged` → audit/cover the test or source files in staged changes.

If `$ARGUMENTS` is empty, ask what to test and stop. Work the phases in order; Phases 1–3
are investigative (plan before writing), 4–7 implement, 8 verifies.

**Progressive loading.** Phases 1–3 and 8 need nothing but this file. Phases 4–7 carry the
rules inline and the *worked examples* in `reference/`, read **only when the target calls for
it** — each phase below names its file and its short-circuit. A run that writes three
synchronous unit tests should never open the async reference.

## Phase 0 — Load profile

Make this generic workflow concrete from project facts:

- [ ] Read `.claude/PROJECT.md` — **Stack**, **Commands** (`test`, `test:targeted`/`test:one`),
      and **Architecture** (modules/layers, and the **test layout**: where tests, fixtures,
      and factories live).
- [ ] Read `.claude/rules/_generic/testing.md`.
- [ ] If `CONTEXT.md` exists, read it so test names use the project's domain vocabulary.
- [ ] Read every stack testing rule whose `paths` frontmatter matches the target. These
      packs carry the concrete framework, assertion style, fixtures, and factory locations —
      never hardcode them here.
- [ ] If `PROJECT.md` is missing or still `TEMPLATE`, fall back to the root `CLAUDE.md` (always in
      context) when it carries the stack, test command, and test layout — note you're running
      without a kit profile. Only if *neither* has them, run `/bootstrap` first.

Use the test command, test layout, and layers from PROJECT.md everywhere below. Apply the
stack-specific test patterns from the installed `.claude/rules/*` — do not invent framework
idioms in this skill.

---

## Phase 1 — Classify

**Mode:**
- Source file/feature given → **new tests** (Phase 2, then 4–7).
- Existing test file/dir given → **refactoring** (Phase 2, then 6).
- Both → do both, in that order.

**Layer of the code under test** (use the layers named in PROJECT.md → Architecture):

| Layer | Examples | Test approach |
|-------|----------|---------------|
| Pure / domain | calculations, transforms, validators, value objects | Pure unit tests — no mocks, deterministic inputs from factories |
| Service / use-case | commands, queries, orchestration | Mock only the external boundary; test the real domain logic they call |
| Infra / IO | network, DB, filesystem, queues, clock | Mock the external boundary only; async-aware where the language has async |
| UI | components, views | Render + behavior via public output; query by role/text, not internals |

The layer decides the strategy: unit (no mocks) vs mock-boundary vs async-aware vs render.
Find existing coverage before planning — map the target to its expected test path by the
project's naming convention and grep the test tree for references to the units.

---

## Phase 2 — Inventory & gap analysis

For **new tests**, list every public unit (function, method, class, exported symbol) and
mark coverage. For **refactoring**, list the existing tests and the antipatterns they carry.

| Unit | Kind | Covered? | Priority |
|------|------|----------|----------|
| `process_order` | pure | partial | high |
| `OrderResult` | value object | yes | — |
| `fetch_remote` | io | no | high |

Kind: `pure` (deterministic, no side effects) · `stateful` (mutates state) · `async` ·
`io` (network/file/DB/clock).

**Evidence before the audit (refactoring mode)** — gather with the stack's own idioms (from the
installed testing rule / `CONTEXT.md`), never a hardcoded framework token. Grep the target test
tree for:
- [ ] test functions with **no assertion / no expected-exception** (the stack's assert/raises idiom).
- [ ] **real sleeps** and **real-clock reads** (`sleep`, `now`, `time()`), and **unseeded randomness**.
- [ ] **hardcoded temp/output paths** instead of the framework's temp-dir helper.
- [ ] mocks that patch the project's **own modules/layers** (from PROJECT.md → Architecture), not boundaries.
- [ ] legacy xUnit-style setup/teardown/assert calls where the stack prefers plain asserts.

Record each hit as a row that feeds the Phase 6 findings table.

Before writing any fixture, check the project's factory/fixture location (from PROJECT.md /
stack rules) — reuse existing builders instead of constructing domain objects inline.

For large or unfamiliar targets, **delegate to the `test-gap-finder` agent** to enumerate
untested paths and rank them by risk, then design tests for the critical gaps it reports.

---

## Phase 3 — Test design

Plan every test as a row before writing code:

| Unit | Scenario | Expected | Type | Mock boundary |
|------|----------|----------|------|---------------|
| `process_order` | no items | empty result, no charge | unit | none |
| `process_order` | valid items | total computed, 1 charge | unit | none |
| `fetch_remote` | network error | propagates after retry | integration | network client |
| `handle_event` | subscriber callback raises | engine does not propagate | async unit | none |

**Mock decision — three rules:**
1. Mock external boundaries only: network, DB, filesystem, clock/`now`, sleep.
2. Never mock your own domain logic or same-module internals — that tests the mock, not
   behavior.
3. More than ~2 mocks → it's probably an integration test; reconsider scope.
4. **Prefer a fake over a mock** for a collaborator you own but must stand in for (a repository,
   a queue, a store): a small working in-memory implementation exercises real behavior, where a
   mock only replays a scripted return and asserts on the script.

**Fixture vs local helper:** reusable across ≥2 files → shared fixture/setup in the nearest
common location; used once → local helper at the top of the file; complex domain object →
the project's factory location.

---

## Phase 4 — Writing rules

**Load on demand:** writing new tests → read
[`reference/writing-patterns.md`](reference/writing-patterns.md) (worked good/bad shapes for
naming, AAA, parametrize, fixture scope, mock discipline, fakes, assertion quality, isolation).
Refactor-only runs skip it except its §Refactoring conversions (Phase 6).

- **Naming:** `test_<unit>_<scenario>_<expected>` (or the stack idiom). A failing name
  must say what broke without opening the file. No `test_works`, `test_case_1`.
- **AAA:** Arrange → Act → Assert, no interleaving. One logical assertion target per test
  (several `assert` lines for the same outcome are fine). Never call the unit inside the
  assertion — store the result first. Delete arrange that the act doesn't use.
- **Parametrize:** same logic over ≥2 inputs → one parametrized/table-driven test, not N
  copy-pasted functions and not a `for` loop inside one test.
- **Properties over examples, where an invariant exists:** if the unit has a nameable
  invariant ("output stays sorted", "sums are conserved", "encode∘decode = identity" —
  `rules/_generic/core.md`), add one property test asserting it across generated
  inputs — the stack's generator library if PROJECT.md/rules name one (Hypothesis,
  fast-check, StreamData…), else a seeded loop over randomized + boundary inputs. Example
  tests pin points; the property pins the region between them.
- **Fixture scope:** default to per-test (fresh) scope. Wider scope (module/session) only
  for expensive read-only setup — never for fixtures that mutate state.
- **Mock discipline:** patch at the call site, not the definition site. Assert call
  count/args only when the side effect (not the return value) is the thing under test. Use
  the framework's teardown-safe mocking from the stack rules.
- **Isolation:** no shared mutable module-level state; each test passes independently and in
  any order. Filesystem → the framework's temp-dir helper, never hardcoded paths. Randomness
  → always seed. Time → freeze/inject, never read the real clock in assertions.
- **Assertion quality:** assert specific values, not `is not None` / `len > 0`. Compare
  floats with an approx/tolerance helper. For exceptions, assert both type and message
  (message must contain the offending value).

---

## Phase 5 — Async test safety (where the language has async)

**Load on demand:** the target actually contains async code → read
[`reference/async-patterns.md`](reference/async-patterns.md) (async test shapes, the invariant
checklist, orphaned-task cleanup, the mocked-clock hang). **Short-circuit:** a synchronous
target skips this phase and that file entirely.

- Use the framework's async test setup (per stack rules); don't block the loop.
- Subscriber/callback failure is isolated — the engine/orchestrator must not propagate it.
- Cancellation propagates: a cancellation signal must never be swallowed by a bare
  catch-all `except`/`catch`.
- Parallel fan-out: one task's failure must not kill its siblings (collect, don't crash).
- Ordering invariants: state is persisted **before** events are emitted to subscribers.
- No real sleeps/timers — inject or mock the clock; real `sleep` makes tests slow and flaky.
- A **mocked** sleep/clock returns instantly, so an unbounded retry/poll loop under test spins at
  full speed (a runaway CPU/memory hang). Guard such tests with the framework's per-test timeout
  and a real termination condition (e.g. a call-count ceiling) — never `sleep(0)`, which is
  mocked too.

---

## Phase 6 — Refactoring existing tests

Audit the target and produce a severity-ordered findings table. Severities:
- **CRITICAL** — false confidence (passes regardless of behavior), crashes, or masks bugs.
- **STRUCTURAL** — maintainability/clarity failures that make tests hard to change safely.
- **STYLE** — minor; fix while touching the file, not a standalone change.

| Antipattern | Severity | Fix |
|-------------|----------|-----|
| Test with no assertion / no expected-exception | CRITICAL | Add a real assertion or delete it — it proves nothing |
| Mocks the unit's own domain logic / same-module internals | CRITICAL | Remove the mock; exercise the real implementation |
| Assertions weakened to make a flaky test pass | CRITICAL | Restore the real expectation; fix the code or premise |
| Trivial/always-true assertions (`is not None`, `len > 0`) | CRITICAL | Assert the actual expected value |
| Setup hides the Arrange (shared mutable setup assigning state) | STRUCTURAL | Extract to a fixture or local builder; keep Arrange visible |
| Order-dependent / shared module-level state | STRUCTURAL | Each test builds its own state in Arrange |
| Real sleep / real clock / real network in a unit test | STRUCTURAL | Mock the boundary or mark as integration |
| Hardcoded temp/output paths | STRUCTURAL | Use the framework's temp-dir helper |
| Unseeded randomness | STRUCTURAL | Seed it for repeatability |
| Loop over cases inside one test | STRUCTURAL | Extract to parametrized/table-driven cases |
| Same complex object built inline in many tests | STRUCTURAL | Move to the project's factory location |
| Legacy xUnit assert style where the stack prefers plain asserts | STYLE | Convert per stack rules |

When converting, split merged assertions into focused tests and replace per-case copies with
one parametrized test. Mock only at the external boundary; keep the domain real.

**Load on demand:** a multi-line conversion (xUnit class style → plain assertions, parametrize
extraction) → read [`reference/writing-patterns.md`](reference/writing-patterns.md)
§Refactoring conversions. A one-line severity fix needs no reference file.

### F.I.R.S.T. audit (refactor mode only)

Principle definitions live in `rules/_generic/testing.md`. What this phase adds is that four of
the five are **mechanically greppable** — run them over the target instead of eyeballing, using
the project's own paths and idioms (`PROJECT.md` → Stack, test layout):

| Principle | How to find violations | Fix |
|-----------|------------------------|-----|
| **Fast** | the runner's slowest-tests report (`--durations`-style flag) | mock at the boundary, use in-memory data, or move it to the integration lane |
| **Independent** | grep the target for class/module-level state assigned outside a test body, and for the framework's module-level setup hooks | build the state inside each test's Arrange |
| **Repeatable** | grep for RNG calls without a seed argument, and for reads of the real clock (`now`, `today`, monotonic timers) | seed the RNG; freeze or inject the clock |
| **Self-validating** | grep for tests whose only output is printing/logging, with no assertion or expected-exception | every test asserts, or it proves nothing |

**Timely** is a process principle, not a greppable one: new functions arrive with their tests.
It shows up here only as a gap in Phase 2's inventory, never as a finding in an existing file.

Report each hit as a Phase 6 finding with its severity, not as a silent fix — an unseeded RNG in
a test that has never flaked is still CRITICAL-adjacent, and the user decides whether it is worth
touching now.

---

## Phase 7 — Self-review checklist

- [ ] Every test name follows `test_<unit>_<scenario>_<expected>` (or stack idiom).
- [ ] No test without at least one real assertion / expected-exception.
- [ ] No domain logic or same-module internals mocked — boundaries only.
- [ ] Randomness seeded; time frozen/injected; no hardcoded paths; no real sleeps.
- [ ] Floats compared with tolerance; exceptions assert type + message.
- [ ] Reusable fixtures and object builders live in shared/factory locations, not inline.
- [ ] Tests that touch IO boundaries are marked/categorized per stack convention.
- [ ] **Mutation thinking:** for each critical-path test, name one plausible bug that would
      still pass it (off-by-one, wrong branch, swallowed error). If such a bug survives, the
      assertion is too weak — assert exact values, resulting state, or the side effect itself.

---

## Phase 8 — Coverage verification

Run via PROJECT.md → Commands — never hardcode commands:

- [ ] Run the **targeted** test command on the new/changed tests first; all pass.
- [ ] Run the **full** test command; no new failures.
- [ ] Check coverage for the target if the project defines a coverage command.

Coverage is a **floor, not a goal** — a passing suite with no real assertions is worthless.
Prioritize: correctness of existing tests > coverage of new critical paths > style.

---

## Output

```
## Test Design — <target>
| Unit | Scenario | Expected | Type | Mock boundary |   (the Phase 3 table)

## Refactoring Actions   (omit if target = new code)
| Antipattern | File:Line | Severity | Fix |

## Files
- written:  <paths>
- changed:  <paths>

## Test Run
<targeted result> · <full-suite result> · <coverage before→after if available>

## Remaining Gaps
<units/paths still untested and why, or "none">
```

## See also

- `test-gap-finder` agent — enumerate and rank untested paths before designing tests.
- `/tdd` — build NEW code test-first (red → green → refactor); this skill covers/refactors
  tests for code that already exists.
- `/code-review` — quality pass on the new tests and the code under test.
- `/diagnose` — for a reported bug, root-cause it there; reproduce with a **failing test
  first**, then return here to lock the fix in.
