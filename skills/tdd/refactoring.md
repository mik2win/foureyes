# Refactoring (the third step of TDD)

**Gate:** read at `/tdd` REFACTOR, once the slice is green. Skip it while RED or GREEN is
outstanding — refactoring without the safety net is the thing this step exists to prevent.

REFACTOR is not optional cleanup you do "later" — it's the step that keeps the design from rotting
as features pile on. With the test green, you have a safety net; use it to improve the code *now*,
while you still remember why.

## What "refactor" means here

Change the code's **structure** without changing its **behaviour**. The tests that were green stay
green. If a change makes a test fail, you altered behaviour — that's not a refactor, back it out.

## What to do in the green window

- **Deepen the module.** Apply the moves in `/codebase-design` → DEEPENING.md: collapse a leaky
  interface, pull complexity down, own a leaked decision, move a seam. The test you just wrote
  proves you didn't break anything.
- **Remove duplication.** The third copy of a thing is the rule — extract it to the lowest layer
  both callers reach (per `PROJECT.md` → Architecture).
- **Clean to the floor.** Apply `rules/_generic/code-quality.md`: function size, guard clauses,
  intent-revealing names, no dead code or magic values.
- **Refactor the test too.** If the test couples to internals, fix it now — move it to the right
  seam, drop a needless mock (`mocking.md`). A test is code; it gets refactored like code.

## Discipline

- **Re-run after every change.** Small steps; the suite is green between each. Don't batch five
  refactors then run once — if it goes red you won't know which move did it.
- **Refactor on green only.** Never refactor with a failing test on the board; get to green first,
  then clean up.
- **Don't gold-plate.** Refactor toward the design the *current* behaviour needs, not toward
  imagined future features. Generality is justified by real callers (`/codebase-design`), not by
  speculation.

## Where the bigger cleanups go

This step handles the design of the code *you just wrote*. For a quality pass over a broader set of
already-written files, that's `/refactor`. For a whole-codebase architecture-health scan, that's
`/arch-health`. TDD's refactor step is the *innermost* loop of the same discipline.
