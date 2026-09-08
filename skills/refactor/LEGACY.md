# Refactoring code that will not go under test

Read this when `/refactor` or `/implement` meets a unit that cannot be instantiated in a test
harness, so "write tests first" has nothing to attach to. Everything here is a fallback; the
main line stays `skills/refactor/SKILL.md`.

## The deadlock, and the order out of it

"No tests, so write tests first" deadlocks when pinning the behaviour itself requires an edit —
the dependency has to be broken before anything can observe the unit. Name the loop out loud,
then break it in this order:

1. Apply ONLY conservative dependency-breaking transformations, with no tests, purely to make
   the unit reachable: narrow the parameter, extract an interface, pass in what is actually
   used. Do not change a non-public signature in uncovered code while doing it — the caller you
   did not enumerate is the failure mode, and preserved signatures are what keep step 1
   conservative.
2. Write characterization tests: what the code does today, not what it should do.
3. Make the real change.

Step 1 may leave the design uglier. Say so, and record the scar as work to heal once coverage
exists. Never widen step 1 into the change you actually want.

## Before you extract or move anything

- Cover the exact lines that will change, not the whole unit.
- Verify two things separately: the behaviour still exists, AND it is still wired to the caller.
- Choose inputs that exercise every type or format conversion on the path — a value that
  survives truncation, rounding or coercion unchanged makes a broken extraction look green.
- For each branch you rely on, ask whether the test could pass without entering it.

## Partial coverage is a plan, not a failure

When a unit is too tangled to characterize whole:

- Rank its behaviours by how long an error would stay hidden — a wrong pixel shows up today, a
  wrong write shows up in a quarter. Test the slow-to-surface ones, restructure the rest
  uncovered, and say in the report which parts moved unprotected.
- Pick extractions by coupling count: the number of values crossing in and out, field access not
  counted. Prefer 0, then 1–2 — the failure mode of extraction here is a silent type conversion.
- Start with chunks of two to five lines you can name, not with the "right" boundary.
- A variable added purely to observe a condition is scaffolding: mark it, keep it for the whole
  session so extractions stay undoable, and delete it — with its tests, or rewritten onto the
  extracted units — before you finish.

## When the harness is not reachable at all

First actually TRY to instantiate the unit: it is cheaper than it looks, and the compiler or the
first failure names what blocks it. Only then attach the change as new, test-driven code instead
of editing inline:

- **Sprout method / sprout class** — write the new behaviour as its own tested unit and call it
  from the old code. Use the class form when the host will not instantiate at all.
- **Wrap method** — rename the old body, give its old name to a wrapper that calls both. The
  only one of the four that does not grow the existing method.
- Write the call site first and comment it out, so you see how it reads in context.

Name the price every time: the call site stays untested, the host unit is given up on for now,
and logic duplicating something in the untested region will rot there unnoticed. Report each
sprout as debt naming the unit it gave up on.

## Encapsulation loses to coverage

When breaking a dependency to get code under test conflicts with hiding, choose the coverage: a
characterization test buys the same reasoning the hiding was buying, and coverage usually lets
you restore the encapsulation later. Say which invariant you loosened and leave a note to heal
it. The reverse holds too — a unit so hidden that nothing can observe its behaviour is not well
encapsulated, it is unobservable.
