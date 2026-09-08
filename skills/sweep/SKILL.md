---
name: sweep
disable-model-invocation: true
description: >-
  Mass mechanical migration across many files — rename an API, swap a library, apply a codemod
  pattern: build a COMPLETE site inventory first, prove the recipe on a pilot batch, then
  transform in verified batches until a re-scan finds zero leftovers. Coverage is explicit —
  every site transformed, deferred with a reason, or flagged for judgment; nothing silently
  skipped. TRIGGER when: the user wants the same change applied everywhere ("rename X to Y
  across the repo", "migrate all call sites", "replace library A with B", "update every
  usage"). DO NOT TRIGGER when: the work is a feature or redesign (use /prepare → /implement),
  deleting dead code (use /clean-mvp), or cleaning one diff (use /refactor).
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, AskUserQuestion, Agent
effort: high
---

# Sweep: $ARGUMENTS

A migration is not a feature: the steps repeat, the risk is the **tail** — the sites your
first search didn't find — and "done" is a property of the whole set, not of any one edit.
So the discipline inverts the feature pipeline: inventory before any edit, a pilot before
scale, verification per batch, and a final re-scan that must come back empty.

`$ARGUMENTS` describes the transform ("rename `fetchUser` → `getUser`", "replace moment with
date-fns"). If empty, ask what to migrate and stop.

---

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` — **Commands** (`test`, `test:targeted`, lint), **Architecture**
   (scope: which trees are app code vs vendored/generated). If missing or `TEMPLATE`,
   fall back to the root `CLAUDE.md` (always in context) when it carries the commands/architecture —
   note you're running without a kit profile; only if *neither* has them, **STOP**: run
   `/bootstrap` first.
2. Read the `.claude/rules/*` whose `paths` cover the touched trees — transformed code must
   land in house style, not just compile.

## Phase 1 — Define the transform (before searching)

Pin the recipe as a contract:

- **FROM → TO** — one worked example pair (real code, before and after), the way a reviewer
  would want to see it. Ambiguity here multiplies by the site count.
- **Mechanical vs judgment** — state the rule for which sites are pure substitution and which
  need a human-style decision (changed semantics, error handling differences, incompatible
  signatures). Judgment sites are *flagged and proposed*, never auto-applied.
- **Out of scope** — generated files, vendored code, lockfiles, the old library's own tests.
- **Stored as data?** If the old name also lives outside the repo — status strings in rows, event or
  message type names, discriminators, routing keys, graph edge types — that half is a data migration,
  not a rename: route it to `/rollout` (expand/contract), and a clean re-scan does not close it.

Confirm the recipe with the user via `AskUserQuestion` if any of the three is uncertain.

## Phase 2 — Inventory EVERY site (no edits yet)

Multi-modal, like `/discover` — one search angle always misses:

- Grep the symbol **and its aliases** (imports-as, re-exports, destructuring).
- Grep **strings**: log messages, config keys, docs, comments, test names mentioning it.
- Grep **dynamic uses**: reflection, string-built calls, serialized names in fixtures/data.
  Each dynamic site is a judgment site by definition *and* a `rules/_generic/code.md`
  finding — the migration is the moment to make it static.
- Glob file patterns the migration implies (e.g. every file importing the old library).
- In a typed stack, break it on purpose: rename or remove the old symbol and let the compiler
  enumerate the call sites grep missed, then restore. Untyped → say so and stay with search.

Produce the **site inventory** — the sweep's single source of truth. **Write it to a file**
(scratchpad, or alongside the report at the Plans location) rather than only into the reply:
it is the sole record of which of N sites are done, and a migration outlives the context
window that held the chat. Each row carries its own status, so the table *is* the progress
tracker — there is no second one to keep in sync.

| # | `path:line` | Kind (mechanical / judgment / string-doc) | Batch | Status (todo / done / judgment / deferred / exception) |

**State the total count.** If you bound the inventory in any way (scope, sampling), say what
was excluded and why — a truncated inventory that reads as complete is how migrations ship
half-done. For a large repo, delegate discovery angles to parallel read-only **Explore**
agents over disjoint subtrees and merge their citations.

## Phase 3 — Pilot batch (prove the recipe)

Transform **3–5 representative mechanical sites** (include the ugliest one, not just the
cleanest). Run `test:targeted` on the touched modules. Show the user the pilot diff and
confirm the recipe holds. A recipe correction here rewrites the plan for hundreds of sites —
that's the point of piloting. Do not proceed past a failing or unconfirmed pilot.

## Phase 3½ — Write the tool, not the edits (large sweeps)

When the mechanical inventory exceeds **~30 sites**, stop hand-editing: express the recipe
as a **codemod** and let the pilot prove the *program*, not the prose.

- Prefer AST/structure-aware transformation over regex — whatever tool the stack rule
  packs or `PROJECT.md` name for this language (codemod frameworks, structural
  search-and-replace tools); regex only for trivial token renames with zero syntactic
  ambiguity.
- Build it in the scratchpad; run it against the Phase-3 pilot sites first and diff-review
  exactly as before. Use the tool's dry-run/diff mode as the review surface.
- Why this beats N hand edits: hand-editing has a **per-site error probability that
  compounds over the tail** — the 180th edit gets less attention than the 5th (allocation,
  not motivation — `core.md`). A codemod has ONE error surface, reviewed once,
  applied uniformly — and is **re-runnable**: after a rebase, after the re-scan finds
  stragglers, in the sibling repo.
- The codemod is a migration artifact: save it alongside the report (Plans location) and
  cite it in the output. It touches mechanical sites only — judgment sites stay out of its
  reach.
- The tool changes nothing else about the discipline: inventory first, pilot proves it,
  batches still verify with targeted tests, the re-scan must still come back empty.

## Phase 4 — Batched execution

Work the inventory in fixed batches (~10–20 mechanical sites, grouped by module so targeted
tests cover each batch):

1. Transform the batch (matching each file's local idiom, not just the recipe literal).
2. Run `test:targeted` for the touched modules — green before the next batch.
3. Tick the batch's rows in the inventory file — `done`, or `deferred` / `judgment` with the
   reason — **before** starting the next batch. A row still reading `todo` is an untouched
   site, whatever the chat remembers.
4. **Judgment sites**: batch them separately — for each, show the site + your proposed
   change + the semantic difference, and apply only what the user confirms.
5. After each batch, output the suggested `git add <paths> && git commit` command (the user
   commits; batch-sized commits keep the migration bisectable). Never run it.

If the same class of failure appears in two batches — stop, fix the recipe, and re-check the
already-done batches for the same defect (the two-strikes rule at migration scale).

## Phase 5 — Zero-leftover verification

The sweep is done when **re-discovery returns empty**, not when the checklist does:

1. **Re-run the full Phase 2 discovery** (all angles). Every hit is: transformed ✓, deferred
   (with reason + owner), or a named intentional exception. Anything else → back to Phase 4.
2. Run the **full** test suite + lint (PROJECT.md → Commands).
3. If the old symbol/library should now be gone entirely: assert its absence (grep clean;
   dependency removed from the manifest — suggest the removal command).

## Output

```markdown
## Sweep — <transform>

### Coverage
- Sites found: N (angles: symbol / strings / dynamic / files)
- Transformed: X · Judgment-confirmed: Y · Deferred: Z (each with reason) · Exceptions: W
- Re-scan: CLEAN | <remaining hits>

### Verification
<targeted per batch: green> · <full suite: result> · <old-symbol absence: clean/n-a>

### Suggested commits
<the per-batch git commands, or "already output per batch">

### Deferred / follow-ups
- `path:line` — <why deferred> → <route: /prepare | owner>
```

## Hard rules

- **Inventory before any edit.** No transform until the site table exists **in a file** with a
  total count — and every batch updates it in place before the next one starts.
- **No silent truncation.** Every bound on coverage is stated; every inventory row ends as
  transformed / deferred-with-reason / named exception.
- **Pilot before scale.** An unconfirmed recipe never touches the long tail.
- **~30+ mechanical sites → codemod.** Hand-editing a long tail is a compounding error
  surface; write the tool, prove it on the pilot, keep it as the artifact.
- **Judgment sites are proposed, never auto-applied.** Semantic changes get user confirmation.
- **Done = re-scan clean.** The finish line is empty re-discovery + green full suite, not an
  inventory with every row ticked.
- **Never commit.** Output batch-sized commit commands; the user runs them.
- **Facts from PROJECT.md.** Commands and scope boundaries come from the profile.

## Cross-reference

- **`/clean-mvp`** — removal of dead things (this skill changes live things).
- **`/refactor`** — one-diff cleanups; **`/prepare` → `/implement`** — when the "migration"
  turns out to need design (a judgment-site majority is that signal).
- **`/discover`** — the multi-modal search discipline Phase 2 reuses.
- **`/retro`** — after a large sweep, feed what the inventory missed on the first pass back
  into the kit.
