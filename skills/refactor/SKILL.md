---
name: refactor
disable-model-invocation: true
description: >-
  Clean up and improve already-written code — simplification, reuse/DRY extraction,
  efficiency, language modernization, and architecture/layer hygiene. QUALITY-ONLY: this
  skill does NOT hunt for correctness bugs — use /code-review for that. It applies edits
  then verifies via format + test.
  TRIGGER when: the user wants to tidy, simplify, modernize, de-duplicate, or make changed
  code more reusable or efficient.
  DO NOT TRIGGER when: the user wants to hunt correctness/security/crash bugs (use
  /code-review), scan the WHOLE codebase for rot/ball-of-mud hotspots (use /arch-health),
  or design a module's interface from scratch (use /codebase-design).
allowed-tools: Read, Grep, Glob, Bash, Edit, Agent
effort: high
---

# Refactor

Improve the quality of changed code WITHOUT changing its behavior. Pure refactor: same
inputs produce the same outputs. This skill APPLIES the cleanups, then runs the project's
`format` and `test` commands to confirm nothing broke. It does NOT look for bugs — for
correctness/security/crash analysis run `/code-review`.

---

## Phase 0 — Load profile

Read these before touching any code. They define every project fact this skill needs:

1. `.claude/PROJECT.md` — Commands (`format`, `lint`, `test`), Architecture (layers,
   boundaries, composition root), and any project-specific conventions.
2. `.claude/rules/_generic/*` — stack-agnostic rules (code quality, comments, naming). If
   `CONTEXT.md` exists, align names toward its ubiquitous language (a rename to the canonical
   term is behaviour-preserving and in scope).
3. Stack rule packs in `.claude/rules/*` whose `paths` (front-matter glob) match the
   target files. These carry the language- and framework-specific modernization and
   anti-pattern checks — do not hardcode any here; defer to them.

If `PROJECT.md` is missing or still `TEMPLATE`, fall back to the root `CLAUDE.md` (always
in context) when it carries the commands/architecture above — proceed on it, noting you're
running without a kit profile. Only if *neither* has those facts, tell the user to run
`/bootstrap` first, then stop.

---

## Phase 1 — Resolve target

`$ARGUMENTS` selects what to refactor:

- **file path** — that file.
- **directory** — all source files under it.
- **`staged`** — `git diff --cached --name-only` files.
- **range** (e.g. `main..HEAD`) — `git diff --name-only <range>` files.
- **(empty, default)** — changed files: `git diff --name-only` plus
  `git diff --cached --name-only`. If none, ask the user what to refactor.

Read every target file in full before judging it. Match each file against the rule packs'
`paths` so you apply the right stack-specific checks per file.

---

## Phase 2 — Refactor dimensions

Apply these in order. Each is QUALITY-only; never alter observable behavior.

### D1 — Language modernization (per installed rules)
Apply the modern-idiom and anti-pattern checks defined in the matched stack rule packs
(control flow, data containers, I/O, exception/error handling, etc.). Do not invent
idioms — use only what the installed rules prescribe for this stack.

### D2 — Architecture & layer hygiene (per PROJECT.md)
- **Boundaries**: imports point inward only; no sibling-to-sibling coupling; cross-boundary
  wiring lives in the composition root named in PROJECT.md.
- **SRP**: each unit has one reason to change. If describing it needs "and" → split.
- **Layer purity**: domain/business logic stays free of I/O, rendering, and framework calls
  per the layering in PROJECT.md; orchestration and presentation stay in their layers.
- **Boundary conversion**: external/raw responses are mapped to domain types at the adapter
  edge, not passed raw into inner layers.

### D3 — Function quality (per code-quality rule)
- **Size**: extract when a function exceeds the limits in the code-quality rule, or when
  it operates at more than one level of abstraction (SLAP).
- **Naming**: names state intent; rename the unclear.
- **Parameters**: 0–2 ideal; 3 acceptable; 4+ → group into a parameter object. Replace
  behavior-switching boolean flags by splitting the function.
- **Guard clauses**: flatten nesting with early returns.
- **Command/Query separation**: a unit either does something or returns something.

### D4 — Duplication extraction (DRY)
Same logic, computation, or construction in 2+ places → extract to one shared unit placed
per the architecture in PROJECT.md. Do not over-abstract incidental similarity.

### D5 — Dead-code removal
Delete unused imports/symbols, unreachable branches, commented-out code, and stale
TODO/FIXME/legacy/back-compat shims (MVP-stage projects keep no re-export stubs). Replace
magic numbers with named constants. Delete comments that merely narrate the code; keep only
non-obvious WHY. Confirm before deleting anything that could be a public/exported symbol or
a back-compat shim callers may rely on — never remove user-visible behaviour silently
(Phase 3 rule 2 applies).

### D6 — Stack-specific dimensions
Apply every additional check defined in the installed stack rule packs matched in Phase 0
(framework patterns, data/ORM patterns, concurrency, domain invariants, etc.). These are
the source of truth for stack specifics — reference them generically, never duplicate them.

---

## Phase 3 — Apply & verify

0. **Confirm before writing.** Phases 1–2 produce a *proposed* cleanup list; this phase is the
   first that touches files. Show the list — file, what changes, why — and get the user's go
   before the first `Edit`. A refactor is a multi-site, judgment-bearing edit whose diff the user
   is expected to review as a whole, so the gate is *"apply these N?"*, not a per-edit prompt.
   Skip it only when the user's own request already named the exact change ("rename X to Y here").
1. **Apply** the cleanups with Edit, smallest safe steps first.
2. **Stay pure**: if a change could alter behavior, is ambiguous, or needs a judgment call
   (e.g. removing code that might be used by reflection, changing a public signature),
   STOP and ask the user instead of guessing. Defer rather than risk semantics.
3. **Format**: run the `format` command from PROJECT.md. If `format` is `n/a` (no
   formatter), skip and note it in the output.
4. **Test**: run the `test` command from PROJECT.md (scope to affected tests when the
   project supports it). If tests fail, the refactor changed behavior — revert the
   offending edit and report it. If a risky refactor lacks coverage, suggest `/test` first.
   If `test` is `n/a` (no suite at all), say so and lean harder on staying pure —
   recommend `/test` before any non-trivial refactor, since nothing else pins behavior.

For large or multi-file targets, fan out reading/analysis with the Agent tool, then apply
edits yourself so changes stay coordinated.

---

## Output

Report concisely:

- **Changes by dimension** — what was cleaned up under each of D1–D6 (one line each).
- **Files touched** — absolute paths.
- **Verification** — `format` result and `test` result (pass/fail + summary).
- **Deferred** — anything skipped as risky/ambiguous, with the reason and what to ask.

---

## Hard rules

- **Behaviour-preserving only.** Same inputs → same outputs. If a change could alter
  observable behaviour or is ambiguous, STOP and ask — defer rather than guess.
- **Never hunt bugs here.** Correctness/security/crash analysis is `/code-review`'s job.
- **Confirm destructive removals.** Don't silently delete exported symbols or back-compat
  shims callers may rely on.
- **Verify, never publish.** Run `format` + `test`; never `git add`/`commit` — suggest the
  command, the user runs it.

---

## Cross-reference

- **`/code-review`** — finds correctness, security, and crash bugs. This skill does NOT;
  run it for bug hunting. The split mirrors the built-in taxonomy (`/code-review` = bugs,
  built-in `/simplify` = quality-only): this skill is the kit's PROJECT.md-aware
  counterpart of `/simplify`. When both passes run on the same diff, quality findings
  belong HERE and correctness findings there — never report the same issue from both.
- **`/test`** — add coverage BEFORE attempting a risky refactor so behavior is pinned.
- **`/arch-health`** — scans the WHOLE codebase for shallow modules & ball-of-mud
  hotspots and routes the one you pick here; this skill cleans the current diff on demand.
- **`/codebase-design`** — the deep-module vocabulary D2's architecture hygiene draws on
  when a boundary needs redesigning, not just tidying.
- **`/clean-mvp`** — whole-codebase cruft sweep (dead code, unused files, legacy shims);
  this skill's D5 removes dead code only within the current target.
- **`/distill`** — mines the whole repo's implicit conventions into project rules; this
  skill then *applies* those installed rules to the target diff (D1/D6 read them).
