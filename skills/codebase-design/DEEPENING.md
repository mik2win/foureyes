# Deepening: shallow-module smells and the moves that fix them

**Gate:** read when hunting for deepening opportunities — `/codebase-design` §Finding deepening
opportunities, `/arch-health` Phase 0, `/refactor` D2. A run that only needs the vocabulary
(depth, seam, interface) gets it from `SKILL.md` and skips this catalog.

A codebase becomes a ball of mud one shallow module at a time. "Deepening" is the work of turning
a shallow module (interface nearly as complex as its implementation) into a deep one (a lot of
behaviour behind a small interface). Use the [SKILL.md](SKILL.md) vocabulary — *depth, interface,
seam, leverage, locality* — to name what you find.

## Smells (where to look)

| Smell | What it looks like | Why it's shallow |
|-------|--------------------|------------------|
| **Pass-through method** | `doX()` just calls `other.doX()` and returns it | Adds interface, hides no complexity |
| **Leaky interface** | Callers must call `a()` then `b()` then `c()` in order, or set a flag before a method works | The invariant lives in the caller, not the module |
| **Temporal coupling** | "Remember to `init()` before `use()`" | The interface doesn't enforce its own ordering |
| **Information leakage** | The same design decision (a date format, a wire schema) is known in several modules | No single module owns it; change touches all of them |
| **Config-by-caller** | Many parameters / option flags pushed onto every caller | Complexity pushed *up* to callers instead of down into the module |
| **Conjoined methods** | Two methods only ever make sense used together | They're really one operation split in two |
| **Special-purpose-itis** | A new near-identical method per caller (`getUserByEmail`, `getUserByName`, …) | A slightly more general interface would serve all of them |
| **Exception soup** | Callers wrap every call in error handling for errors the module could have prevented | Errors not defined out of existence |
| **Mock-the-internals tests** | Tests can only be written by patching the module's private collaborators | The seam is in the wrong place / too deep |
| **Divergent change** | One module's history shows several unrelated reasons to change (bucket the commit subjects) | Two or three modules living as one; split along the reasons |
| **Shotgun surgery** | One reason (a new currency, a new provider) forces edits across many modules | The decision has no owner; gather it — *Own the decision* |
| **Reaching chain** | `a.b.c.d()` hops across several types, repeated at many call sites | The caller knows its collaborator's collaborators; the concept the chain fetches was never named |
| **Ambiguous choice point** | Two modules plausibly serve the same call and an engineer given the concrete situation cannot say which to reach for; a new package the profile does not name fails the same reader test | Overlapping responsibility — the boundary is wrong, not the documentation |

## Moves (how to deepen)

- **Absorb the order.** Fold a required call sequence into one method, or make later methods
  no-ops/auto-init when the precondition isn't met — *define the error out of existence*.
- **Pull complexity down.** Move a detail every caller handles (formatting, retry, validation)
  inside the module so callers stop knowing about it.
- **Collapse the interface.** Merge conjoined methods; replace N special-purpose methods with one
  general-purpose one whose parameters express the variation — a variation the *domain* names, or
  a lookup key of one kind (`getUser(field, value)`). A parameter that exists so one caller can pick
  its branch is the first step of a wrong abstraction, not depth: ask what it would be called if
  that caller did not exist. Nor is a shared call site shared behaviour — callers often invoke one
  abstraction in name while each runs a nearly unique path, visible only once it is inlined.
- **Own the decision.** Give one module sole knowledge of a leaked design decision; everyone else
  goes through its interface. That's locality — change it once.
- **Move the seam.** Put the interface exactly where behaviour must vary, so a fake satisfies it
  for tests without reaching inside. A module testable through its seam is, by construction, deep.
- **Delete the wrapper.** A pure pass-through earns its keep only if it *will* hide variation
  soon; if not, remove it and let callers use the real interface.
- **Cut by field use.** To split an oversized unit, map which fields each method touches and cut
  where the clusters are: the edges the cut crosses are the new unit's interface, and a cut that
  crosses many is wrong however good its name sounds. Draw the map in the transcript, don't commit it.
- **Break the cycle.** Two modules that import each other are one module: extract the shared part
  into a third, add a coordinator, or invert one dependency — never hide the import inside a function.
- **Name what the caller wanted.** Replace a reaching chain with a method on the immediate neighbour
  named for the need, not a forwarder named after the path; judge a chain by the types it hops
  across, not by its dots, and never wrap it: a delegator hides the coupling without removing it.

## Not deepening

Don't manufacture depth where there's no behaviour to hide. A genuinely simple leaf (a value
object, a one-line pure function) is *correctly* shallow — wrapping it adds interface for nothing.
Depth is justified by hidden complexity, never by indirection for its own sake.

## In the kit

- **`/arch-health`** runs this hunt across the whole codebase and ranks the opportunities.
- **`/refactor`** applies these moves to the changed code (D2 architecture hygiene).
- **`/prepare`** uses the smells to decide whether a change needs a *prefactor* (deepen first,
  then build) before the feature work.
