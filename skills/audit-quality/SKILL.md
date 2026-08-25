---
name: audit-quality
disable-model-invocation: true
description: >-
  Scoped architectural quality audit of a module or changeset — classifies each file
  SOUND / SHORTCUT / HACK against THIS codebase's own architecture, with the architecturally
  correct alternative, fix effort, and blocking status, then hands back a phased refactor plan.
  Read-only: it never edits code.
  TRIGGER when: the user asks whether code is a hack or architecturally sound, wants a quality
  or architecture audit of a module/directory/changeset, says code "works but feels wrong",
  asks what the shortcuts in a just-implemented feature cost, or wants a refactor plan for an
  area before extending it.
  DO NOT TRIGGER when: the target is a diff and the question is defects (correctness, security,
  performance) — that is /code-review; the target is the whole repository and the question is
  where the debt is concentrated — that is /arch-health; the user wants the cleanups applied
  rather than assessed — that is /refactor; the target is dead code — that is /clean-mvp.
allowed-tools: Read, Grep, Glob, Bash, Write
context: fork
effort: high
---

# Architectural Quality Audit: $ARGUMENTS

Target: a file, directory, changeset, or commit range. Empty `$ARGUMENTS` → audit the files
changed on this branch, and say that is what you scoped to.

**Read-only.** This skill classifies and recommends; it never edits code. The deliverable is a
written report plus a refactor plan, not a set of fixes.

## Principle

**Architecturally correct, even when longer, beats a quick hack that "just works".** Every piece
of code should be what you would design knowing the requirements will change. Where it is a
shortcut, say so plainly and show what SOUND would have looked like *here* — a verdict without
the correct alternative is a complaint.

"Correct" means correct **for this codebase**: the layer map, the canonical patterns, and the
sanctioned exceptions all come from the profile, never from a generic notion of good design.

## Phase 0 — Load the architecture you are auditing against

- [ ] `PROJECT.md` → **Architecture**: the layer/module map, the dependency direction, where
      logic belongs and where it must not go. This is the layer map for Check 2 — do not invent
      one.
- [ ] `PROJECT.md` → the **canonical exemplars** it names (the factory, the registry, the entry
      shape) — these are the "canonical example" column of Check 3.
- [ ] `.claude/rules/_generic/*.md` and every `.claude/rules/` file whose `paths` frontmatter
      matches the target. Project rules and `CONTEXT.md` carry the **sanctioned exceptions** —
      a documented, blessed deviation is not a finding.
- [ ] `CONTEXT.md` for domain vocabulary, so findings are named in the project's own terms.
- [ ] **No profile yet?** If `PROJECT.md` is missing or still `TEMPLATE`, do not stop: prefer any
      architecture the root `CLAUDE.md` carries, else infer the intended structure from the tree
      and the target's siblings. State the assumption at the top of the report and proceed — an
      audit against an inferred architecture is worth having, an audit that pretends to a profile
      it doesn't have is not.

## Phase 1 — Read before judging

Read every file in scope **fully**, plus enough surrounding code to judge *pattern conformance,
not style*: the callers, the module's siblings, the interface or factory it should conform to.

**The evidence gate — before any HACK or SHORTCUT verdict.** A pattern that looks wrong and has
a logged reason is intent, not a hack. Prove it, or the file stays SOUND:

1. `git log -p -5 -- <file>` — was this shape introduced deliberately, and does the message say
   why?
2. The callers (`grep` the imports/uses) — does the "wrong" shape exist because of a real
   constraint at the call site?
3. The **sanctioned exceptions** in the project rules / `CONTEXT.md` — a blessed seam is legal by
   definition.
4. Prior settled decisions (ADR / decision log / the plan that shipped it) — re-litigating a
   decision the project already made is out of scope here; route it to `finding-verifier`.

Only after those four does a finding get a HACK or SHORTCUT verdict.

## The checks

Run all ten over the scope. A check that does not apply to this stack (9, for a project with no
database) is stated as not-applicable, not silently dropped.

### Check 1 — Abstraction quality

- Is there polymorphism expressed as type-switching (`isinstance` chains, `if kind == "…"`)
  where the language's interface/protocol mechanism belongs?
- Is construction direct where the codebase has a factory, and dispatch hardcoded where it has a
  registry?
- Are string literals doing the job of an enumerated type?
- Are there magic numbers that belong in named constants or config?

### Check 2 — Layer placement

Against the layer map from `PROJECT.md` → Architecture. The recurring red flags, expressed
layer-neutrally:

- A **domain/core** module doing I/O.
- A **service** module doing presentation/formatting.
- An **infrastructure** module carrying business rules.
- An **entry-point** module (CLI command, controller, handler) doing anything beyond building
  config and delegating — see `rules/_generic/service-layer.md`.
- A module importing a **sibling in the same outer layer** where the profile says bounded
  contexts must not know each other.

### Check 3 — Pattern conformance

Does new code follow the established pattern, or introduce a one-off? Build the table from the
profile's exemplars — one row per pattern the codebase actually has:

| Pattern | Canonical exemplar (from the profile) | Red flag |
|---------|---------------------------------------|----------|
| <how this codebase constructs the thing> | `<path>` | <the hand-rolled alternative> |
| <how it registers a new variant> | `<path>` | <bypassing the registry> |
| <how it emits output / formats> | `<path>` | <raw output in the wrong layer> |
| <how modules talk across a boundary> | `<path>` | <a direct import that skips the seam> |

N divergent shapes for one job in sibling files is itself a finding: which one does a newcomer
copy?

### Check 4 — Dependency direction

- Grep the imports in every target file and trace the chains: does any lower layer import a
  higher one?
- Circular-import risk, and annotation-only imports that should be guarded.
- Does this changeset **introduce** an upward dependency that did not exist before? That is the
  one worth blocking on — a pre-existing one is a finding for the plan, not a blocker for this
  change.

### Check 5 — Hack smell

For each hit, say *why* it is a hack and what the correct pattern is:

- Magic numbers in logic · string constants used as dispatch · `isinstance`/type-switch chains.
- Global mutable state; module-level state mutated at runtime.
- Runtime attribute injection / monkey-patching.
- **Defensive masking** — catch-all handlers, silent fallbacks that hide the bug instead of
  handling a real failure mode (`rules/_generic/exception-patterns.md`).
- Copy-paste: 3+ lines duplicated with minor variation where a helper belongs.
- Boolean flag parameters that select between two behaviours (should be two functions).
- Deep nesting past ~3 levels where guard clauses would flatten it.
- **Explanatory hack comments** — `# workaround for …` is the code telling you the finding.

### Check 6 — Composition over inheritance

- Inheritance used for anything other than a true IS-A relationship.
- Mixins (usually a hack — prefer composition through an interface plus delegation).
- Inheriting from a **concrete** class rather than an interface.
- `super()` chained through several levels — fragile; prefer explicit delegation.

### Check 7 — Extensibility

If the requirements shift slightly, how much has to change?

- Are the extension points **explicit** (interfaces, registries, factories, plugin hooks), or
  does extending mean editing existing code?
- Count it: **how many files change to add one more variant** of the thing this module is about?
  The healthy answer is usually two — the new file, and the registry that lists it.
- Would swapping one external dependency touch more than its adapter?

### Check 8 — Error handling

- Handled at the right level — not swallowed at the boundary, not propagated past the layer that
  can act on it.
- Domain errors distinguished from infrastructure errors.
- Recovery paths explicit and tested, not hoped-for.
- Silent swallows, and error handling that masks a bug rather than handling an expected failure.
- Retries on non-idempotent operations (see Check 10).

### Check 9 — Data-access patterns *(where the project has a datastore)*

Per the stack rules for the actual engine. Engine-neutral shape of the check:

- Indexes present for the columns the queried code filters, joins and orders on.
- No unbounded column selection in production paths.
- No N+1 access pattern — a query inside a loop over rows.
- **The client's commit/transaction semantics are the ones the code assumes** — an async or
  autocommit-off client that the code treats as autocommit is a silent data-loss bug.
- Multi-step writes that must be all-or-nothing are inside one transaction.
- Connection-time settings applied where the engine requires them.

### Check 10 — Write-path idempotency **(mandatory, and it can block a SOUND verdict)**

The invariant is already a write-rule (`rules/_generic/resilience.md` → Idempotency); this is its
**read-side obligation**. The audit must *open* the write-path, not infer health from structure.

For every state-mutating path in scope (persist, accumulate, finalize, publish, notify):

- **Fires twice** — replay, restart, retry, a re-delivered event: same end state, or a doubled
  one? A blind `+=` on a counter or a balance with no processed-id guard is the canonical defect.
- **Two racing paths reach the same write** — a normal path and its timeout/cleanup twin, a
  reconciliation loop overlapping the live handler.
- **The guard is real, not conventional** — a predicate in the UPDATE, a unique constraint, an
  upsert on a stable key, a deterministic idempotency key, a processed-id set. **"The caller only
  calls it once" is not a guard.**
- **The transaction boundary matches the invariant** — a multi-step write that commits per step
  is a partial apply on crash.

**Verdict consequence.** A module that writes state and whose write-path you did not open
**cannot be classified SOUND** — either open it, or name the gap in the verdict line itself
(`core.md` → *verdicts carry denominators*: "sound across the read-paths I opened; write-path
unread"). A structural audit that never opens the write-path can say "the structure is sound",
never "sound". A double-apply found here is a **correctness bug** → Phase 0 of the refactor plan,
not structural debt.

## Verdict rubric

Classify **each file** by the worst thing in it:

- **SOUND** — architecturally correct for THIS codebase: right layer, right seam, conforms to the
  pattern its siblings established, invariants respected, tested where the profile expects tests.
  Would survive a requirements change. No action.
- **SHORTCUT** — works, but takes a debt-generating shortcut: duplicated logic instead of reusing
  the existing seam, a bypassed abstraction, a missing test for behaviour the profile classes as
  critical, a hardcoded value that belongs in config, divergence from the sibling pattern.
  Bounded fix; schedule it before building dependent features.
- **HACK** — violates the architecture or plants a trap: logic in a forbidden layer, an
  upward/sibling dependency the profile forbids, a design decision leaked across modules,
  swallowed errors or fail-open paths, an unguarded state mutation two paths can reach
  (double-applies on replay or a race), fake conformance (implements the interface, breaks its
  contract). Must be fixed before building on top.

A "cleaner would be nicer" observation with no concrete harm scenario — a failure, a newcomer's
confusion, a future extension cost — is not a finding. Drop it.

## Completeness pass (multi-file targets)

Run this against the draft audit, on yourself, before writing the verdict — the scope being more
than a couple of files is what makes it mandatory:

- **Every file in scope got a row.** Rebuild the scope list from the target (glob or `git diff
  --name-only`), diff it against the table, and name any file that has no row.
- **Every SOUND verdict rests on cited evidence**, not on the file having been skimmed.
- **Every check ran or was declared not-applicable** — layer placement, data access, and
  **write-path idempotency** especially. A SOUND row on a state-writing file with no Check-10
  evidence is exactly what this pass exists to catch.

A gap found here is closed before reporting, not footnoted.

**Why this is a self-check and not the `completeness-critic` agent.** Neither context this rubric
runs in can spawn: in a fork the spawn tool stays listed but returns an error instead of launching,
and preloaded into `quality-auditor` it is a subagent, where `Agent` is stripped outright
(`rules/_generic/delegation.md` § Tools an agent will not get). Either way a fan-out here would
read on the way out as a failed phase rather than as a configuration mistake. The independent
critic is not lost — it moves one layer up: the run hands its report back, so the **caller** can
run `completeness-critic` over the written file (its input contract takes a path), which is a
stronger check anyway — a genuinely separate context, reading the artifact rather than the draft.
Recommend it in the return line when the scope was large.

## Report format

```markdown
## Quality audit: <target>

| File | Verdict | Key finding (path:line) | Correct alternative | Effort | Blocking? |
|------|---------|-------------------------|---------------------|--------|-----------|

### Overall — SOUND | NEEDS WORK | ARCHITECTURAL DEBT
<1–3 lines: is this safe to build on?>

### Coverage
write-paths opened: <paths> · read in full: <paths> · read by diff or window only: <paths, or
"none"> · unread: <paths, or "none in scope">

### Priority fixes
1. <most impactful — file, what, why>
2. …

Architectural debt estimate: N files need refactoring before this area can be safely extended.
```

Every finding is anchored to `path:line` **as the code exists now**, and only in files you
actually opened.

**The Coverage line is not optional**, and it names the **route**, not just the set — "read in
full" is checkable against your own tool log and is routinely false. Measured over a 146-run
subagent corpus (2026-07-26..28): of 10 reports asserting the whole changed set was read in full,
**6 were contradicted by their own calls** — three had windowed every read of a changed file, and
three had run only a diff. Splitting the line makes the honest answer sayable: "read by diff
only" is a legitimate coverage level; claiming it as a full read is not.

## Refactor plan (REQUIRED — findings alone are half the job)

An audit that stops at a list hands back unordered work. After the verdict, produce a
**prioritized, ready-to-work** plan:

1. **Separate bugs from refactoring.** A HACK that *misbehaves at runtime* (wrong result, silent
   no-op, corrupted state) is a correctness bug, not structural debt. Bug fixes go in **Phase 0** —
   an independent first phase that ships before any restructuring and does not depend on it.
2. **Phase the rest by risk and dependency.** Each phase states what it changes, why, and its
   **reversibility** (easy-undo vs one-way). Pure relocations and extractions with no behaviour
   change are grouped and labelled as such — that is the safe bulk.
3. **Name the invariants that must not break** across the refactor: the behavioural contract the
   module guarantees today. These are the regression guardrails.
4. **Say what NOT to do.** Explicitly decline work that is not worth it — a facade worth keeping,
   a file worth leaving alone. A plan that refactors everything is as wrong as one that refactors
   nothing.
5. **Untested surfaces.** Flag touched code with no test coverage: that is where the plan is
   riskiest, and a characterization test goes in before the change.

```markdown
| Phase | Type (bug/structure) | Changes | Reversibility | Invariants at risk |
|-------|----------------------|---------|---------------|--------------------|
| 0 | bug | <correctness fixes, independent, ship first> | — | <what must still hold> |
| 1 | structure | <relocations / extractions> | easy-undo | |

**Do NOT touch:** <what to deliberately leave, and why>
**Test-first:** <untested surfaces the plan hits — characterization test before changing>
```

## Write the report to a file (REQUIRED)

This skill runs in a **fork**, so a result left only in the conversation is lost. Write the full
report — per-file table, Overall, Coverage, Priority fixes, Refactor plan — to the plans/backlog
location from `PROJECT.md` (else offer a path and confirm):

`<plans>/<target-slug>-audit.md`

where the slug is the audited path. If that file exists, write `-audit-2.md` — **never overwrite
a prior audit**; the old one is the evidence that a finding is a repeat. Then return, in the
conversation, a **short summary plus the file path** — not the whole report. When the scope ran
past a handful of files, add one line recommending the main thread run `completeness-critic`
over that file: the fork cannot spawn it, the thread that receives the path can.

**Exception — preloaded into `quality-auditor`.** That agent carries this file as its rubric
(`skills:` frontmatter) and `/implement` spawns it *synchronously*, collecting its reply and
continuing it by `SendMessage`. No fork, no notification to lose: there the final message **is**
the deliverable (`agents/quality-auditor.md` → Output), the agent declares no `Write`, and no file
is written. The obligation above is for the `/audit-quality` run.

## Hard rules

- **Read-only on app code.** Report, never fix. The only file you write is the audit report.
- **Evidence before verdict.** The four-step gate in Phase 1 runs before any HACK/SHORTCUT.
- **Every architecture fact from the profile.** Layer maps, canonical patterns, and sanctioned
  exceptions are read, never assumed.
- **Check 10 gates SOUND.** A state-writing file with an unopened write-path gets a named gap,
  not a clean verdict.

## See also

- **`/code-review`** — defects in a diff (correctness, security, performance). This skill asks
  whether the design is right; that one asks whether the code is wrong.
- **`/arch-health`** — the whole repository, ranking where debt is concentrated. This skill is
  scoped to a module or changeset.
- **`/refactor`** — applies quality cleanups. This skill produces the plan those fixes follow.
- **`quality-auditor`** agent — the same rubric as a fan-out unit over a disjoint file list, for
  when an orchestrating skill needs per-file verdicts rather than a report.
