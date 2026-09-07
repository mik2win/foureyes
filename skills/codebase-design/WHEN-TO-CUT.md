# When to cut: is the seam due, and along which axis

**Gate:** read when a plan proposes a new module, seam or abstraction, or asks whether an existing
coupling should be broken — `/prepare` Phase 2.5.1 ("New seam → design first"), `/codebase-design`
§Finding deepening opportunities, `/arch-health` Phase 0, `/decompose` Phase 0. Skip it when the
seam exists and the work is filling it in: `SKILL.md` says *where* and *how deep*, this file *when*.

## Is it due, and along which axis

- **Readiness test.** Write the interface the boundary would expose: a few calls that hide the messy
  part entirely mean the cut is visible; a paragraph of conditions means not yet — keep the code
  together, add behaviour, cut later, and record that as the decision. When the full seam is too
  dear now, name the partial form you take instead and how it decays if the full one never arrives.
- **Rate of change is the second placement criterion**, beside "where behaviour must vary": daily
  (data, config, policy), per release (application code), yearly (framework, schema, contract) drift
  apart on their own. Verify against churn, discounting age, renames and generated files.
- **Different rates AND different reasons AND a different actor** — the role who would ask for each
  change — earn a boundary; one of the three alone is decoration. Where partial service is
  meaningful, also cut on what fails together, so one leg can fail while the others serve.
- **Fan-in × churn decides placement and direction.** Depend on what changes less often than you.
  Before adding logic to a module, say how many things depend on it and how often its rules change;
  many dependents and likely change → the volatile part lives in its own module *above* the stable one.
- **Name the growth axis.** More types → behaviour on the type; more behaviours over a few stable
  types → a module per behaviour dispatching over them. Say which addition you are making expensive.
- **Cut by knowledge, not by execution order.** "Read, then transform, then write" puts one piece of
  knowledge on both sides; write what each module owns — two owners of one piece are one unit.
- **Diagnose before you move.** Several unrelated reasons in one module → split it; one reason
  across many modules → gather it (`DEEPENING.md` names both smells).

## Prove the boundary is real

- **A seam needs an enabling point** — a place outside the code in question where the
  implementation is chosen (a constructor argument, composition-root wiring, config). An
  implementation constructed at the call site is not a seam.
- **The caller owns the interface.** Declare the port in the module that calls it; a port in the
  adapter's package renamed the dependency, it did not invert it. Of two modules, the one farther
  from I/O is higher and must not name the other.
- **Deletion test.** Name the infrastructure library that could be removed wholesale with the unit
  tests still passing. No such library → no port; say so instead of naming layers.
- **Say what enforces the direction.** Which language mechanism (visibility, exports, a private
  module) makes the forbidden dependency fail? None → the layering is advisory; name the lint rule,
  don't install it.
- **DI is gated on a count.** One adapter needs none; several passed by hand → explicit DI and one
  composition root; a DI framework only for dependencies chained across levels. State the count.
- **Two cheap probes.** Name one plausible requirement change and count the modules it touches —
  more than one means the seam is elsewhere. Then stand up a unit test for the module alone: what
  it must import or mock to run is the coupling measurement.
- **Next-feature test.** Name the next plausible feature (new kinds of component, or the existing
  kinds reused?) and count the units it changes — "all of them" means the split follows function,
  not an axis of change. A structure with no named change that would cut across its grain is a
  preference, not a decision.
- **Writer census.** A seam is not designed until you have said who writes each table behind it; the
  writer owns it. Several writers → route them through its interface, else it is a naming convention.
- **When the change crosses a deployment** (new service, synchronous call into a neighbour, shared
  table or transaction), answer in writing: testable without an integrated environment? deployable
  alone? A "no" is a cost.

## Name the price before the benefit

- **Open every proposal with the change it makes cheap and the change it makes expensive**, and say
  which change it does *not* remove — usually "buildable in either order", not "decoupled".
- **Semantic vs implementation coupling.** Semantic: what the problem requires; no layout reduces
  it, and "inherent" needs a requirement you can quote. Implementation: what your layout adds on
  top. Attribute the weight before defending a design.
- **A module lowers the peak and raises the total.** Its interface is a new concept charged to the
  owner and to every caller; name both halves. Small unrelated clusters in one module is not a
  smell — that is what `utils` legitimately buys.
- **Localise the invocation, not the implementation.** Depth hides the body, never the call: grade
  by distance (a page, another file; no visible call site is `code.md` §Greppability's end), exempt
  declared framework idioms, and count the files a reader opens to answer "what does this do".

## When not to cut

- **Co-location is a real move.** When two things change together and you cannot afford to
  separate them, put them next to each other — adjacent functions, one directory, one repository —
  one element at a time, saying what they are coupled with respect to.
- **A pattern belongs to a module, not to the repository.** Modules of different kinds want
  different shapes; a pattern that differs between modules is not convention drift. Hexagonal,
  onion, ports-and-adapters and clean architecture are one pattern under four names.
