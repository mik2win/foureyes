---
name: codebase-design
disable-model-invocation: true
description: >-
  Shared vocabulary and discipline for designing deep modules — a lot of behaviour behind a
  small interface, placed at a clean seam, testable through that interface. The design lens the
  kit's planning and quality skills reach for.
  TRIGGER when: the user wants to design or improve a module's interface, decide where a seam
  goes, make code more testable or AI-navigable, weigh two designs, OR another skill (/prepare,
  /tdd, /refactor, /arch-health) needs the deep-module vocabulary.
  DO NOT TRIGGER when: the user wants to run tests, hunt for correctness bugs (use /code-review),
  or do a mechanical rename with no design question.
allowed-tools: Read, Grep, Glob
---

# Codebase Design

Design **deep modules**: a lot of behaviour behind a small interface, placed at a clean seam,
testable through that interface. Use this language and these principles wherever code is being
designed or restructured. The aim is **leverage** for callers, **locality** for maintainers, and
**testability** for everyone — including the agent navigating the codebase next session.

This skill is **reference vocabulary**, not a workflow. It carries no project facts — read
`.claude/PROJECT.md` → Architecture for where this project's seams and layers actually live, and
`rules/_generic/code-quality.md` for the size/naming/composition floor this builds on.

## Glossary

Use these terms exactly — don't substitute "component," "service," "API," or "boundary."
Consistent language is the whole point (and feeds the project's own `CONTEXT.md`).

- **Module** — anything with an interface and an implementation. Deliberately scale-agnostic: a
  function, class, package, or tier-spanning slice. _Avoid_: unit, component, service.
- **Interface** — *everything* a caller must know to use the module correctly: the type
  signature, but also invariants, ordering constraints, error modes, required configuration, and
  performance characteristics. _Avoid_: API, signature (too narrow — type-level surface only).
- **Implementation** — what's inside a module, its body of code.
- **Depth** — leverage at the interface: how much behaviour a caller (or test) exercises per unit
  of interface they must learn. **Deep** = large behaviour behind a small interface; **shallow** =
  interface nearly as complex as the implementation.
- **Seam** — a place where you can alter behaviour **without editing in that
  place**; the *location* where a module's interface lives. Where to put the seam is its own
  design decision, distinct from what goes behind it. _Avoid_: boundary (overloaded with DDD).
- **Adapter** — a concrete thing that satisfies an interface at a seam. Names a *role* (what slot
  it fills), not substance. A small adapter can wrap a large implementation (a Postgres repo); a
  large adapter can wrap a small one (an in-memory fake).
- **Leverage** — what callers get from depth: more capability per unit of interface learned. One
  implementation pays back across N call sites and M tests.
- **Locality** — what maintainers get from depth: change, bugs, knowledge, and verification
  concentrate in one place instead of spreading across callers. Fix once, fixed everywhere.

## Deep vs shallow

**Deep** = small interface + lots of implementation (aim for this):

```
┌─────────────────────┐
│   Small interface   │  ← few methods, simple params
├─────────────────────┤
│  Deep implementation│  ← complex logic hidden
└─────────────────────┘
```

**Shallow** = large interface + thin implementation (avoid): the interface is nearly as costly to
learn as the code it hides, so it buys the caller almost nothing — a pass-through wrapper, a
"manager" that just forwards, getters/setters with no invariant.

When designing an interface, ask:
- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity *inside*?

## Principles

- **Pull complexity downward.** It's better for the *implementer* to suffer than every *caller*.
  A messy detail handled once inside the module beats the same detail handled at every call site.
- **Make modules somewhat general-purpose.** A slightly more general interface is often *simpler*
  than a special-purpose one and serves more callers. Don't gold-plate — aim for "general enough."
- **Define errors out of existence.** The best error handling is an interface where the error
  can't arise (an operation that's a no-op on the empty case beats one that throws on it).
- **Put the seam where behaviour must vary.** Place the interface exactly at the point you'll need
  to swap implementations (real vs fake, prod vs test, vendor A vs B) — not one layer off.
- **Design it twice.** The first design that works is rarely the best. See
  [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md).
- **Testable through the interface.** A deep module is tested by exercising its interface with a
  fake at the seam — not by reaching into its implementation. If a test must mock internals, the
  seam is in the wrong place. This is why `/tdd` and `/test` lean on this vocabulary.

## Finding deepening opportunities

Shallow modules, leaky interfaces, and misplaced seams are where a codebase rots into a ball of
mud. [DEEPENING.md](DEEPENING.md) lists the smells and the moves that deepen a module. `/arch-health`
runs that hunt across a whole codebase; `/refactor` and `/prepare` apply it to the change at hand.

## How the kit uses this

- **`/prepare`** — borrow this vocabulary when weighing design alternatives and checking SOLID; a
  "new-abstraction" approach should be justified as a *deeper* module, not just more files.
- **`/tdd`** — use the depth/seam language when confirming the public interface before the first
  test; tests go through the seam.
- **`/test`** — a unit that needs internals mocked has its seam in the wrong place; this vocabulary
  names why and where to move it so tests exercise the interface.
- **`/refactor`** — D2 (architecture hygiene) is deepening work; name the smell from DEEPENING.md.
- **`/arch-health`** — the whole scan is "where are the shallow modules and bad seams?".

## See also

- [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md) — generate two genuinely different designs, compare, synthesize.
- [DEEPENING.md](DEEPENING.md) — shallow-module smells and the moves that fix them.
- `rules/_generic/code-quality.md` — the size/naming/composition floor this design lens sits on.
