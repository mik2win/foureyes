# Shape: function, class or transform — and what a pattern costs

**Gate:** read when the open question is the *form* of a module — function or class, transform or
mutable object, inheritance or delegation, a pattern or plain code — `/codebase-design` once
`WHEN-TO-CUT.md` has said a seam is due, `/prepare` Phase 2.5.1 when alternatives differ in shape,
`/tdd` before the first test fixes an interface. Skip it when the codebase's convention already
gives the form: `SKILL.md` says how deep, this file says what shape.

## Function, class or transform

- **Default to a function.** A one-method `…Handler` / `…UseCase` / `…Service` class must name
  the capability a function cannot give: undo, parameters gathered in stages, a hook a subtype
  overrides, or shared fields needed to split one genuinely complex computation. "It is the
  pattern" is not a capability; a class with none of these is refactored back into a function.
- **Class or transform, decided by mutability.** Derived values over a source that is mutated
  in-process live on a class that computes them on read; over an immutable source, or when the
  derived data is short-lived, a transform (source in, enriched record out) is simpler. Storing
  derived fields on a record whose source keeps changing is the inconsistency bug you chose.
- **Decide, then do.** Compute the whole plan as inspectable data first and execute it in a
  separate step: the plan is what tests and dry runs assert against, and the executor stays trivial.
- **Bind at boot, read-only after.** Wiring, patching and configuration belong to the setup phase;
  after it nothing still adds or replaces methods, constants or registry entries. Expose the shared
  structure read-only and make a late write fail loudly — except the registries you name as live.

## Inheritance

- **Two conditions, both required.** Inheritance is legal when every method of the supertype
  applies to the subtype *and* every subtype instance is valid wherever the supertype is used
  (Liskov substitution, the `/prepare` SOLID row). Either fails, a second axis of variation
  appears, or one class models both a type and its instances → delegate instead. "Composition
  over inheritance" is not a reason; name the condition that breaks.
- **Say the relation before you subclass:** is-a (both conditions hold), behaves-like-a (a role —
  share an interface, not a parent), has-a (own it and delegate). A subtype added because its
  neighbours are subtypes is the wrong one of the three.

## Objects and their interface

- **Messages before classes.** List what must be asked and answered, then ask of each message
  "who should receive this?" — not "what should this class do?". A message that reads right but
  has no correct receiver is an object you have not named yet: name it rather than forcing it onto
  the nearest class. If your object list equals the requirement's noun list, there is no design yet.
- **The metaphor decides the structure.** Before committing to a model, name two or three
  metaphors for the central abstraction and say what each makes awkward — a bag of items merges
  like terms on every operation, a tree of expressions defers it to one reduction. Design B in
  `DESIGN-IT-TWICE.md` is often the other metaphor, not a re-plumbed A.
- **Named in the domain's words, or too abstract.** A name absent from the project's vocabulary
  (`PROJECT.md`, `CONTEXT.md`, the spec, the user's own phrasing) — `ThingElement`, a `typeName`
  field standing in for real types — is too abstract however many sites it would serve.
- **Two lists before the shape:** what matters here — one decision that settles many others, one
  invariant that explains many behaviours — and what does not. The second list is an instruction:
  default it, derive it, or hide it behind the interface; it is not a feature to design.
- **The interface comment is a measurement.** Write it before the body: caller-visible behaviour,
  every argument and result with its constraints, side effects, errors. Cannot be short *and*
  complete → the interface does too much; must restate the body → shallow. Change the interface.
- **An owned collection is not handed out.** Return a copy or a read-only view and keep add/remove
  on the owner: what leaves is a handle to read, never membership to edit.
- **Depth has a second currency when the caller is an agent:** the tokens it must read to reach
  the answer. A full list, a raw log or an id-only reply passing through the caller is shallow
  however few methods it exposes — push the filtering into the call; say which currency each pays.

## Price the pattern

- **Cost in the benefit's units.** Propose a pattern with what it adds (lines, files, one more
  indirection hop) against what it deletes (conditionals, call sites), the count next to the
  choice. Costs no line count shows still get named: an abstraction that lies about the domain,
  one that defeats call tracing, an adapter per independent vendor — a bill every new vendor
  re-issues, so say who writes each implementation. Count against the pattern → say so, drop it.
- **A centraliser says what it is not for.** Anything designed for three or more callers — an
  orchestrator, a core, a registry, a facade — opens with one line: "not here: X; the test: Y".
  Without it every later caller is a legitimate resident.

## Test and failure are design verdicts

- **"How would I test this?" before any test exists.** Global state to reset → unclear side
  effects; heavy scaffolding for external parts → fragile dependency web; tolerance for flakiness
  → hidden nondeterminism. Change the shape, not the test. Then sketch the in-memory fake: if it
  is not a few one-line methods over a dict or a set, the interface is too wide — narrow it.
- **Out-of-process call inside a decision: keep two.** Controller simplicity, domain testability,
  performance — one is given up. Default: split the decision into steps and pay in controller
  complexity. Never inject the out-of-process dependency into the domain to keep the other two.
- **Will the shape say which part broke?** Ask it of every design; "no" is a boundary defect, not
  a logging gap — move the boundaries before adding signals.

## In the kit

`/prepare` 2.5.1 reaches here when alternatives differ in shape, not only in scope; `/tdd` when the
first test fixes an interface; `/refactor` D2 runs the reverse moves — a one-method class back to
a function, delegation for a subtype that fails a condition.
