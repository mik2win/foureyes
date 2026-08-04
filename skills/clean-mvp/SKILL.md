---
name: clean-mvp
disable-model-invocation: true
description: >-
  Whole-codebase cruft-removal sweep — find and DELETE dead code, unused symbols and files,
  legacy/back-compat shims, YAGNI abstractions, stale TODOs, and commented-out code. Every
  deletion is backed by a Proof-of-Deadness evidence checklist and gated by batched user
  confirmation, then verified via format + test.
  TRIGGER when: the user wants to "clean up the codebase", "remove dead code", "delete unused
  stuff", "strip legacy shims", a post-refactor lean-down, or a periodic MVP-discipline sweep.
  DO NOT TRIGGER when: the user wants to clean up the current diff or specific changed files
  (use /refactor — it improves code, this sweeps it away), rank architecture-level rot and
  ball-of-mud hotspots (use /arch-health — proposes only), or hunt correctness/security bugs
  (use /code-review).
allowed-tools: Read, Grep, Glob, Bash, Edit, AskUserQuestion
effort: high
---

# Clean MVP: $ARGUMENTS

MVP-stage discipline: if code is not reachable from a live entry point, delete it. No
back-compat shims, no deprecated aliases, no "just in case" abstractions — anything needed
later can be recovered from git history. This skill SWEEPS and APPLIES deletions; it does not
redesign what stays (`/refactor`) and does not judge architecture (`/arch-health`).

`$ARGUMENTS` optionally scopes the sweep to a file, directory, or module; empty = the whole
source tree per `PROJECT.md` → Architecture.

---

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` — **Commands** (`test`, `lint`, `format`), **Architecture**
   (source layout, layers, entry points), and **Conventions notes**. If missing or still
   `TEMPLATE`, fall back to the root `CLAUDE.md` (always in context) when it carries the
   commands/architecture — note you're running without a kit profile; only if *neither* has them,
   **STOP** and tell the user to run `/bootstrap` first.
2. Read the installed rules in `.claude/rules/*` whose `paths` match the sweep scope — they
   define the stack's idioms (module-export conventions, DI/registry patterns, intentional
   extension points). Use them; never assume a stack.
3. If `CONTEXT.md` exists, read it so findings are named in the project's vocabulary.

---

## Phase 1 — Sweep categories

Scan the scope for each category. Grep-driven; read a file in full before judging its symbols.

1. **Unused imports/symbols** — run the `lint` command from PROJECT.md if it detects unused
   imports; otherwise grep per symbol.
2. **Dead functions/classes/types** — definitions with zero call sites outside their own file.
   A test-only caller means: check whether the tested behavior still matters; if not, both go.
3. **Back-compat shims & legacy wrappers** — `deprecated`/`legacy`/`compat` markers, old-name
   aliases, thin wrappers that only forward to a newer unit, re-exports kept "for
   compatibility", deprecation-warning calls, `_old`/`_legacy` names.
4. **Stale TODO/FIXME/HACK/XXX/TEMP** — done → delete the comment; actionable now → fix or
   file to the backlog location in PROJECT.md; the hack itself removable → remove code + comment.
5. **Commented-out code** — delete; git history is the archive.
6. **YAGNI abstractions** — single-use helpers → inline; single-implementation interfaces →
   concrete (unless a documented extension point per the rules/ADRs); never-varied config
   options → hardcode; feature flags pinned to one value → remove flag + dead branch.
7. **Unreachable code** — statements after return/throw/break, branches that can never run,
   handlers for errors the guarded block cannot produce.
8. **Empty & pass-through files** — value-free re-export files (per the stack's module-export
   idiom in the installed rules), empty modules, 100%-delegating wrappers, empty test files.

**Loop until dry.** Dead code has no known count, and each deletion can orphan more code (the
sole caller of X was itself dead). So the sweep iterates: after applying a batch (Phase 5),
re-run the categories over the affected areas — freshly orphaned symbols are new findings.
Stop when **2 consecutive passes surface nothing new**. Dedup each pass against everything
already **seen** (including findings refuted by the Proof-of-Deadness gate or by the user) —
not just against deleted items, or refuted candidates re-surface every pass and the loop never
converges. Track the seen-set as `symbol@file` in a scratch list.

---

## Phase 2 — Proof of Deadness

Nothing counts as dead until **ALL** of these pass. Record the evidence per finding:

- [ ] **Zero references**: grep the symbol/file name across the whole source tree — no call
  sites, imports, or mentions outside the definition itself.
- [ ] **Not an entry point**: not registered as a CLI command, route, job, handler, or plugin
  per the entry points named in PROJECT.md → Architecture.
- [ ] **Not dynamically referenced**: grep for the name as a *string* — reflection/dynamic
  dispatch, DI-container or registry keys, config/serialized-data keys, template references.
- [ ] **Not exported surface**: not part of the module's public export per the stack's
  export idiom (installed rules) with plausible external consumers.
- [ ] **Not fresh WIP**: `git log --oneline -10 -- <file>` shows no recent work suggesting the
  code is mid-flight rather than abandoned.

Any box unchecked → the finding is at best **Medium/High risk** and must pass the Decision
Gate; if evidence is genuinely ambiguous, keep it and note why.

---

## Phase 3 — Findings table (before ANY deletion)

Present the full table BEFORE editing anything — evidence first, deletions second:

| # | Category | File:Line | What | Evidence (proof summary) | Action | Risk |
|---|----------|-----------|------|--------------------------|--------|------|

Risk levels:
- **Low** — zero references anywhere, all proof boxes checked → may proceed after the table.
- **Medium** — referenced only by tests, or indirectly via string/dispatch patterns.
- **High** — user-visible (command, endpoint, documented behavior), exported surface, or
  plausibly referenced dynamically/by config.

## Phase 4 — Decision Gate

For every **Medium/High** finding, confirm via `AskUserQuestion` **before** deleting —
**batched** (one question per group of related findings, options like "delete all / keep
these / review one by one"), never one prompt per item. Low-risk findings may proceed without
a prompt, but only after the Phase-3 table was shown. Never auto-delete anything user-visible.

## Phase 5 — Apply & verify

1. Apply approved deletions with Edit (whole files: remove via Bash), smallest safe batches
   first.
2. Run the `format` command from PROJECT.md (skip and note if `n/a`).
3. Run the `test` command from PROJECT.md. Failures mean the "dead" code was live — restore
   the offending batch, mark the finding refuted, and investigate before continuing.
4. **No test command (`n/a`)**: say so explicitly — nothing pins behavior, so EVERY batch
   (including Low-risk) needs the user's explicit go-ahead via the Decision Gate, and
   recommend `/test` to add coverage first.
5. Sanity check: the diff should be **net-negative** lines; a sweep that grows the codebase
   went wrong.

Finish with a copy-paste commit suggestion for the touched files — explicit paths only (never
`-A`, `.`, or a directory; a path stages its deletion too). Never run `git add`/`commit`/`push`
yourself; the user runs it.

---

## Hard rules

- **Evidence before edits.** The Phase-3 table with per-item Proof-of-Deadness comes BEFORE
  any deletion; an unproven finding is a guess, not a candidate.
- **Gate the risky ones.** Medium/High findings require batched `AskUserQuestion` confirmation
  — never one-by-one spam, never silent deletion of user-visible or exported surface.
- **Verify, never publish.** Run `format` + `test` from PROJECT.md after applying; never
  `git add`/`commit` — suggest the command as text.
- **Facts from PROJECT.md.** Commands, layout, entry points, and idioms come from the profile
  and installed rules — never assume a stack.
- **Delete, don't improve.** Restructuring survivors is `/refactor`'s job; this skill only
  removes what's dead.

## See also

- **`/refactor`** — cleans and improves the current diff (includes small-scale dead-code
  removal within changed files); this skill sweeps the whole tree and only deletes.
- **`/arch-health`** — ranks architecture-level rot (shallow modules, layer violations) and
  proposes; run it when the problem is design, not cruft.
- **`/code-review`** — hunts correctness/security bugs in a diff; this skill never judges
  correctness of what remains.
