---
description: Stack-agnostic clean-code rules — function size, naming, parameters, composition. Loaded on file read (code work).
paths:
  - "**/*"
---

# Code quality (generic)

Language-neutral defaults. Stack packs may tighten these; they never relax safety.

## Function size

- Domain/business function: ≤ 25 lines soft, 40 hard.
- Orchestration/glue function: ≤ 40 lines soft, 60 hard.
- Size is three numbers, not one: add branches (start at 1, +1 per if/loop/case/ternary — ≤7)
  and variables in play (locals + parameters + fields the body touches — ≤7).
- A limit is a tripwire, not a verdict: past it, look for a seam where meaning and mechanics
  part ways; no seam → keep the long function and say why. Never extract to satisfy a number.
- Litmus: describe what the function does in one sentence without "and". Can't → extract.

## Naming

- Functions are `verb + object` (`load_config`, `build_query`), not nouns.
- Names state intent, not type (`active_users`, not `users_list`).
- Booleans read as predicates (`is_valid`, `has_access`, `can_retry`); collections are plurals.
- `first`/`last` inclusive, `begin`/`end` half-open — not `start`/`stop` for both; units in names.
- One word per concept, project-wide: pick one of `fetch`/`load`/`get`, one of
  `compute`/`calculate`, and stick to it.
- No noise words (`data`, `info`, `Manager`, `Helper`, `Utils`) — name by what it does.
- No redundant context: `order.total()`, not `order.order_total()`.
- Short names for short scopes; long, descriptive names for long-lived scopes.
- No abbreviations that aren't already domain vocabulary (keep the project's accepted
  list in `PROJECT.md`).
- Name an option by its effect, not its usual use; a name covering two behaviours is two options.

## Parameters

- More than 3 positional params → introduce a parameter object / struct / options
  hash, named per the project's stack.
- A flag argument is one where every caller passes a literal AND the body branches on it —
  enums and strings count, not only booleans; split into named functions. A value computed or
  threaded from config is not a flag. Two flags in one signature: split the function, don't
  name four combinations.
- Mirror on exit: >3 returned values → a named result; same-typed tuple slots swap silently.

## Composition

- One function = one level of abstraction. Don't mix high-level orchestration with
  low-level detail in the same body.
- Guard clauses with an early return when one leg is the unusual case; both legs normal → keep
  `if/else`, equal weight is the point. "One exit point" is not a rule; clarity is.
- `&&` mixed with `||`, or a buried call/negation → name one value per idea, then test the names.
- A second fix to one condition → restate it (write the negation, invert it), never a third patch.
- Command/query separation: a function either does something or returns something,
  not both (exception: atomic get-and-set style operations where splitting would race).
- Extract when logic is reused, worth testing alone, or needs a sentence to be understood —
  a comment inside a body is an extraction address; name it from the comment. Not
  single-caller blocks with obvious logic. Split test: the piece reads without its caller,
  the caller without opening the piece or redoing its work (return the parsed value, not a bool).

## Pure core, thin shells

- Domain logic is pure: no I/O, network, clock, or global state — same input, same output.
  I/O lives in thin shells at the edges: load → compute → save.
- Entry points (CLI command, HTTP handler, job) are thin wrappers that delegate to the
  layer owning the logic.
- Pass configuration explicitly to what needs it — never a module-level mutable global. Inject
  only the seam a named test or variant needs; derive the rest, or injected inputs can disagree.

## Dead code

- No dead code, no commented-out blocks, no debug prints left behind.
- But "unused" ≠ "legacy" — classify before deleting. An unwired, not-yet-used feature
  should be wired in or raised with the user, not deleted; only confirmed legacy is
  removed (together with its shims). Can't tell which? Ask rather than delete.
- Removing an override or shadowing field reroutes calls to the base, builds green: not cleanup.

## Module depth

- Prefer **deep modules**: a lot of behaviour behind a small interface. A wrapper that
  only forwards, or an interface nearly as complex as its implementation, is shallow —
  earn the indirection or delete it.
- When *designing or restructuring* a module's interface or seam, invoke `/codebase-design`
  for the vocabulary (depth, seam, adapter, leverage) and the deepening moves.
- A new member gets the narrowest visibility; export it only for a caller outside the module
  that needs it now (name it). Widening later is additive; narrowing is a break.
- Modularity is a property of the import graph, not the folder tree: mutual imports = one module.

## Constants & magic values

- No magic numbers/strings in logic — name them (const / enum) near their meaning.
- Prefer enums/typed dispatch over chains of string/type-check comparisons.

## Algorithmic sizing

- Before choosing a data structure or algorithm, write three numbers: realistic **N**,
  ceiling **N** (the size at which someone would call this broken), and how often the
  operation runs. The numbers pick the structure — not the instinct to be clever.
- O(n²) at n ≤ 100 forever is a fine answer — *say the bound* next to the choice so the
  next reader knows it was priced, not missed. Conversely, anything user-facing that scales
  with unbounded data (rows, files, requests) gets the honest structure from day one —
  "we'll optimize later" on an unbounded N is a scheduled incident.
- No speculative cleverness: an optimization without a measurement or a stated bound is
  complexity spent on a guess (`performance-analyzer` exists for measured work).

## Pattern choice

Name the **problem** first, the pattern second — a pattern reached for by name ("let's use
Strategy here") instead of by pressure (three interchangeable algorithms actually exist) is
ceremony. A pattern must delete net complexity, and half a pattern is fine: take the part
that pays, skip the scaffolding. Before any pattern-shaped structure, name the language
feature that already does it (a function, a closure, a dict of callables, a protocol) and ship
that if it covers the case. Count the threshold on three axes — variants today, how often
they change, whether a hierarchy already exists — and below it the plain construct is clearer:

| Pattern | Use when | Not when |
|---|---|---|
| Strategy | 3+ interchangeable algorithms | 2 options — if/else is clearer |
| Factory | construction varies by type/config | a plain constructor call would do |
| Observer / events | many decoupled reactions to one fact | one known caller — call it directly |
| Singleton | genuinely global state | you just want easy access |
| Repository | a mapping layer already exists below it, plus many domain types × heavy querying or a second object source (in-memory for tests, a feed) | three `find_by` over one ORM — that is the mapper twice; one primary mechanism per table |

## Duplication

- Two copies is a signal, three is a rule — for base classes and shared modules too: two cases
  don't show the axis of variation. Extract only what changes for the same reason: identical
  code encoding two rules is coincidence, not duplication; one rule in code and in a schema,
  doc or fixture is duplication with no matching line. Lowest layer both reach (`PROJECT.md`).
- Extract toward existing utilities before writing new ones — search first.
- "Reuse" is a guess, not an outcome: name what it buys (speed, cost, consistency) and measure that.
- **An exemplar you copy is a hypothesis, not a template.** Before templating new code on an
  existing site, corroborate that the site is the convention and not an accident: a second
  independent site that agrees with it, or the declared convention (`PROJECT.md`, stack pack).
  One hack propagated once becomes the pattern. Preservation-in-place (`core.md` →
  rewrites regress to the mean) never licenses propagation — leave the surprising site alone
  *and* don't copy it until its reason is known.

## The diff

How a change should read, not just what the code should be:

- **Read the neighborhood before writing.** Match the file's idiom, naming, comment density,
  and error style — the diff should read as if the file's author wrote it. Where local style
  contradicts these rules, flag the conflict; don't silently freelance a third style.
- **Smallest diff that fully solves, judged by the state it leaves.** No drive-by refactors,
  renames or reformatting of untouched lines — cleanup is its own pass (`/refactor`) — and,
  symmetrically, a move-or-rename diff carries no behaviour change; where they meet, the second
  starts a new diff. Insertion pushing nesting past ~3 levels → flatten to guards in that diff.
- **No defensive bloat.** Don't guard against states the system cannot reach — an
  impossible-case handler is noise that obscures the real contract. Validate at trust
  boundaries (`code.md`); inside them, trust the types and invariants.
- **Right altitude.** Solve the instance you were asked about; solve the general class only
  when the class demonstrably recurs (see Duplication). An abstraction built for one case is
  speculation wearing a design pattern.
- **Capability is liability.** Code nobody asked for — extra options, "while I'm here"
  features, configurability without a second config — ships with a permanent maintenance
  bill. If it wasn't requested and isn't required, it's scope creep, not generosity.
