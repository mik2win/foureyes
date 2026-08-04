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
- Past the hard limit, extract — don't add a comment apologising for length.
- Litmus: describe what the function does in one sentence without "and". Can't → extract.

## Naming

- Functions are `verb + object` (`load_config`, `build_query`), not nouns.
- Names state intent, not type (`active_users`, not `users_list`).
- Booleans read as predicates (`is_valid`, `has_access`, `can_retry`); collections are plurals.
- One word per concept, project-wide: pick one of `fetch`/`load`/`get`, one of
  `compute`/`calculate`, and stick to it.
- No noise words (`data`, `info`, `Manager`, `Helper`, `Utils`) — name by what it does.
- No redundant context: `order.total()`, not `order.order_total()`.
- Short names for short scopes; long, descriptive names for long-lived scopes.
- No abbreviations that aren't already domain vocabulary (keep the project's accepted
  list in `PROJECT.md`).

## Parameters

- More than 3 positional params → introduce a parameter object / struct / options
  hash, named per the project's stack.
- No boolean flag parameters that switch behaviour — split into two functions.
  (A flag for a minor variation of the same behaviour is fine; one that selects a
  different code path is not.)

## Composition

- One function = one level of abstraction. Don't mix high-level orchestration with
  low-level detail in the same body.
- Guard clauses over nested conditionals. Return early.
- Command/query separation: a function either does something or returns something,
  not both (exception: atomic get-and-set style operations where splitting would race).
- Extract when logic is reused, complex enough to deserve a name, or worth testing in
  isolation. Don't extract trivial one-liners or single-caller functions with obvious logic.

## Pure core, thin shells

- Domain logic is pure: no I/O, network, clock, or global state — same input, same output.
  I/O lives in thin shells at the edges: load → compute → save.
- Entry points (CLI command, HTTP handler, job) are thin wrappers that delegate to the
  layer owning the logic.
- Pass configuration explicitly to what needs it — never a module-level mutable global.

## Dead code

- No dead code, no commented-out blocks, no debug prints left behind.
- But "unused" ≠ "legacy" — classify before deleting. An unwired, not-yet-used feature
  should be wired in or raised with the user, not deleted; only confirmed legacy is
  removed (together with its shims). Can't tell which? Ask rather than delete.

## Module depth

- Prefer **deep modules**: a lot of behaviour behind a small interface. A wrapper that
  only forwards, or an interface nearly as complex as its implementation, is shallow —
  earn the indirection or delete it.
- When *designing or restructuring* a module's interface or seam, invoke `/codebase-design`
  for the vocabulary (depth, seam, adapter, leverage) and the deepening moves.

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
that pays, skip the scaffolding. Reach for one only past its threshold — below it, the
plain construct is clearer:

| Pattern | Use when | Not when |
|---|---|---|
| Strategy | 3+ interchangeable algorithms | 2 options — if/else is clearer |
| Factory | construction varies by type/config | a plain constructor call would do |
| Observer / events | many decoupled reactions to one fact | one known caller — call it directly |
| Singleton | genuinely global state | you just want easy access |
| Repository | isolate/swap persistence | one trivial query site |

## Duplication

- Two copies is a signal, three is a rule: extract shared logic to the lowest layer
  both callers can reach (per the project's dependency direction in `PROJECT.md`).
- Extract toward existing utilities before writing new ones — search first.
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
- **Smallest diff that fully solves.** No drive-by refactors, opportunistic renames, or
  reformatting of untouched lines — they bloat review and hide the real change. Cleanup is
  its own pass (`/refactor`), on its own diff.
- **No defensive bloat.** Don't guard against states the system cannot reach — an
  impossible-case handler is noise that obscures the real contract. Validate at trust
  boundaries (`code.md`); inside them, trust the types and invariants.
- **Right altitude.** Solve the instance you were asked about; solve the general class only
  when the class demonstrably recurs (see Duplication). An abstraction built for one case is
  speculation wearing a design pattern.
- **Capability is liability.** Code nobody asked for — extra options, "while I'm here"
  features, configurability without a second config — ships with a permanent maintenance
  bill. If it wasn't requested and isn't required, it's scope creep, not generosity.
