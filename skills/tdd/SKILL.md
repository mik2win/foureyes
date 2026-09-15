---
name: tdd
disable-model-invocation: true
description: >-
  Drive a feature or bug fix TEST-FIRST with a red-green-refactor loop in vertical slices — one
  failing test → minimal code to pass → refactor → repeat. Tests verify behaviour through public
  interfaces, not implementation details, so they survive refactors. Distinct from /test (which
  authors/audits a suite) and /implement (which executes a prepared plan as written).
  TRIGGER when: the user wants to build or fix something test-first, mentions "red-green-refactor"
  / "TDD" / "write the test first", or wants the safety of a failing test before each change.
  DO NOT TRIGGER when: the user wants to add/audit tests for existing code (use /test), debug a
  specific failure (use /diagnose, then return here to lock the fix), or execute a plan verbatim
  without test-first (use /implement).
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, AskUserQuestion
effort: high
---

# Test-Driven Development: $ARGUMENTS

Build the feature or fix the bug **one vertical slice at a time**, test-first. Each cycle: write
ONE failing test (RED), write the minimal code to pass it (GREEN), then clean up (REFACTOR). The
rate of feedback is your speed limit — small deliberate steps beat big leaps.

This skill carries only the invariant TDD loop. The test/run commands, test layout, and where code
lives are read at runtime from `.claude/PROJECT.md`. The concrete framework, assertion style, and
fixtures come from the installed stack rules — never hardcode them here.

---

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` — **Commands** (`test`, `test:targeted`), **Stack**, and
   **Architecture** (test layout: where tests, fixtures, factories live). If it's missing or still
   `TEMPLATE`, fall back to the root `CLAUDE.md` (always in context) when it carries the
   commands/test layout — note you're running without a kit profile; only if *neither* has them,
   **STOP** — run `/bootstrap` first.
2. Read `.claude/rules/_generic/testing.md` and every stack testing rule whose `paths` match the
   target. These define good/bad tests for this stack — this skill does **not** restate them.
3. If `CONTEXT.md` exists, read it so test names and interface vocabulary use the project's
   **ubiquitous language**; respect any ADRs in `docs/adr/` touching the area you're changing.
4. If `$ARGUMENTS` is empty, ask what behaviour to build or fix, then stop.

---

## Philosophy

**Tests verify behaviour through public interfaces, not implementation details.** Code can change
entirely; tests shouldn't.

- **Good tests** are integration-style: they exercise real code paths through public APIs and read
  like a specification — *"user can checkout with valid cart"* tells you what capability exists.
  They survive refactors because they don't care about internal structure.
- **Bad tests** couple to implementation: they mock internal collaborators, test private methods,
  or verify through side channels. The warning sign — a test breaks when you *refactor* but
  behaviour hasn't changed. If renaming an internal function fails a test, that test tested
  structure, not behaviour.

Design the unit under test as a **deep module** (small interface, behaviour exercised through a
seam) so it's testable without mocking internals — invoke `/codebase-design` for that vocabulary
and the testability checks.

---

## Anti-pattern: horizontal slices

**DO NOT write all the tests first, then all the implementation.** Treating RED as "write every
test" and GREEN as "write every line of code" produces **crap tests**: written in bulk they test
*imagined* behaviour and the *shape* of things, go insensitive to real changes, and commit you to
a test structure before you understand the implementation.

```
WRONG (horizontal):          RIGHT (vertical / tracer bullets):
  RED:   test1..test5          RED→GREEN→REFACTOR: test1 → impl1
  GREEN: impl1..impl5          RED→GREEN→REFACTOR: test2 → impl2
                               ...
```

Each cycle responds to what you learned from the last. Because you just wrote the code, you know
exactly what behaviour matters and how to verify it.

---

## Phase 1 — Plan the slices (before any code)

- [ ] Confirm the **public interface** the change needs (signatures + the invariants/errors behind
      them). Ask: *"What should the interface look like?"*
- [ ] List the **behaviours** to test, as capabilities — not implementation steps, in `CONTEXT.md`
      vocabulary. Seed the list with three kinds of row: an example of every operation the feature
      needs, the degenerate variant of every operation that does not exist yet (empty input, zero,
      null, the no-op call), and the refactorings this session already owes.
- [ ] **Prioritize what stays; order by cost.** Confirm which behaviours matter most — that decides
      the list, not its sequence. Run the degenerate slice first: it answers only *where does this
      operation live* and gets to green in minutes. Take each next slice on two conditions at once
      — it teaches you something and you are sure you can pass it; if none does, one is missing.
- [ ] Identify **deep-module opportunities** (small interface, deep implementation) via
      `/codebase-design` — a testable seam now saves mock-heavy tests later.
- [ ] Get the user's approval on the slice list, then **write it to a scratchpad file** — one
      row per slice, status `todo` / `done` / `dropped` — and update the row at the end of each
      cycle. The loop below runs one slice at a time over many turns; a slice list held only in
      the conversation is a slice list that quietly loses its tail. Keep the file open through the
      loop — a case or a refactoring that surfaces mid-cycle is appended as a row, never chased now.

For a bug fix, the first slice is a test that **reproduces the bug** (RED for the right reason)
before any fix — see `/diagnose`, then come here to lock it in.

---

## Phase 2 — The loop (one slice at a time)

Repeat per slice, in order:

### RED — write one failing test
Write a single test for the next behaviour, through the public interface. Run `test:targeted`
(PROJECT.md → Commands) and **watch it fail for the right reason** — a wrong-reason failure (typo,
import error) proves nothing. See [tests.md](tests.md) for what a good test looks like and
[mocking.md](mocking.md) for the boundary-only mock rule.

### GREEN — minimal code to pass
Write the **least** code that makes the test pass — even something blunt. Blunt means shamelessly
concrete: spelled-out cases and duplicated strings are a deliverable at this step, not a draft, and
a first version caches nothing and shares no mutable state. Don't build for tests you haven't
written yet (that's outrunning your headlights). Re-run `test:targeted` → green.

GREEN has two gears. Default to typing the real code when you know what to type; **the moment a red
bar surprises you, do not guess again** — back the change out to the last green and downshift to
returning the constant the test expects, then let REFACTOR eat it.

### When the bar stays red — pick the move
Never write a new test while the bar is red, and never change production code that no currently-red
test authorises. **Two consecutive failed GREEN attempts on one slice** is the counter that stops
you editing: repeated struggle is design feedback, not a call to try harder. Before a third attempt
answer which is true — wrong structure, wrong slice, or breakage piling up underneath — then pick
the move by what is actually broken.

- **You need a production change no test covers** → revert to the last green, write that test
  there, make it pass, then replay the original change. Never stack a second unverified change on
  a failing one.
- **The slice will not go green in one small change** → revert the edits, record why it was too big
  in the slice list, park its test with the stack's skip idiom and leave the row `todo`, then take
  a smaller slice for the part that is actually broken green before restoring the parked test. A
  parked test is a blocking debt: the suite is not green and Phase 3 is closed while one exists.

### REFACTOR — clean up, stay green
Now improve the design with the test as a safety net: deepen the module, remove duplication, apply
`code-quality.md`. Re-run after each change. See [refactoring.md](refactoring.md). Refactor the
*test* too if it's coupling to internals.

Then move to the next slice — but the row moves to `done` only after REFACTOR, once the duplication
this slice's fake introduced between the test's data and the code is gone (`refactoring.md`). A row
closed on a green bar alone is how a temporary constant becomes permanent. Commit-sized increments;
keep the suite green between slices.

---

## Phase 3 — Finish

1. Run the **full** `test` command (PROJECT.md → Commands) — no new failures.
2. **Play devil's advocate before calling the tests sufficient.** In a scratch buffer you never
   save, write the dumbest wrong implementation that still passes every test of this feature —
   branch on a literal, return the first element, hard-code the answer — then restore the real one
   before anything else. A cheat that survives means the suite is underspecified: add the slice
   that kills it, where its false premise lives. Stop when the surviving cheat is one that
   generalising the code defeats rather than another test.
3. **Re-aim at where the code turned out hard.** The slice list was written before the code existed
   and covers intended usage, not actual difficulty — re-read what you wrote and add a slice
   wherever it got complex: a branch you had to think about, an interaction the list never named.
4. Self-review against `rules/_generic/testing.md`: every test asserts real behaviour, no domain
   logic mocked, names say what broke, no implementation-coupled tests.
5. If new domain terms or a design decision surfaced during the loop, hand off to `/domain-model`
   to record them in `CONTEXT.md` / an ADR.
6. **Handed a plan or card file?** Append `## TDD Log — <date> — <verdict>` to it, following
   [`../implement/reference/work-log.md`](../implement/reference/work-log.md). Its `### Result` is
   the slices table plus any surviving devil's-advocate cheat. Put the file in the commit suggestion.

---

## Output

```
## TDD — <target>

### Slices (red→green→refactor)
| # | Behaviour (what) | Test name | Status |
|---|------------------|-----------|--------|
| 1 | <capability>     | test_...  | done   |

### Files
- tests:  <paths>
- code:   <paths>

### Test Run
<targeted per slice> · <full suite: pass/fail>

### Follow-ups
<deferred refactorings, /domain-model terms to record, or "none" — a slice you can name and
suspect will fail is not a follow-up; it runs in this session>
```

---

## Hard rules

- **One slice at a time.** One failing test → minimal code → refactor. Never bulk-write tests then
  bulk-write code.
- **Fail for the right reason** before writing the fix/feature code.
- **Behaviour, not structure.** Test through public interfaces; mock only external boundaries
  (`mocking.md`). A test that breaks on a pure refactor is wrong.
- **Facts from PROJECT.md + stack rules.** Commands, test layout, framework idioms — never
  hardcoded here.
- **Don't hack tests green.** A failing test means the code is wrong (fix the code) or the test
  asserts the wrong thing (fix the assertion) — never weaken it to pass.

## Cross-reference

- **`/test`** — author tests for *existing* code, or audit/refactor a suite. TDD *drives new code*;
  /test *covers written code*.
- **`/implement`** — executes a prepared plan; it may **delegate a slice to `/tdd`** when the user
  wants that slice built test-first.
- **`/diagnose`** — root-cause a bug there and reproduce it with a failing test, then return here.
- **`/codebase-design`** — deep-module/seam vocabulary for a testable interface.
