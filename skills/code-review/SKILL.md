---
name: code-review
disable-model-invocation: true
description: >-
  Structured review of changed or specified code against this project's rules,
  plus real correctness/security/performance problems.
  TRIGGER when: the user asks to review changes, a PR, a branch, a diff, staged
  work, or named files ("review my changes", "code review this PR", "check this
  branch", "review the diff").
  DO NOT TRIGGER when: the user only wants to understand how code works or learn
  a flow (exploration/explanation, not review).
allowed-tools: Read, Grep, Glob, Bash, Edit, Agent
effort: high
---

# Code Review

Review-only. Find problems; do not fix them. Every finding traces to a documented
rule OR a real correctness / security / performance defect — never to taste.

**Evidence-gate every finding — the false-positive guard.** Before you flag something,
prove it isn't intentional: read the callers (`grep -rn` the symbol) and the change's
history (`git log -p -- <file>`), and check it isn't a **sanctioned exception** — an ADR /
decision record, or a `paths`-matched rule that explicitly blesses the pattern. A pattern
with a logged reason is intent, not a defect. No evidence, no finding.

## Phase 0 — Load profile

**Tooling preflight — one call, before step 1.** Some tools this skill relies on are **deferred**
by the harness: the session lists them by name only and loads their schemas on demand, so calling
one before it is fetched fails. Listing a tool in `allowed-tools` does **not** un-defer it. Issue
a single `ToolSearch` up front covering the whole run — `select:SendMessage,TaskOutput`
(continuing the same `deep-analyzer` / `finding-verifier` agent instead of respawning, collecting
a backgrounded pass) — instead of one round-trip per discovery. A name already loaded costs
nothing to include; a schema discovered missing mid-run costs a turn.

1. Read `.claude/PROJECT.md` — stack, architecture, dependency direction, commands. If
   `CONTEXT.md` exists, read it too — judge naming against the project's ubiquitous language.
2. Always read `.claude/rules/_generic/`: `code-quality`, `exception-patterns`,
   `testing`, `comments`, `boundary-validation`, `external-api-integration`.
3. After resolving the target (Phase 1), read every `.claude/rules/*` whose `paths`
   frontmatter matches a changed file. These stack/domain packs carry the framework-
   and library-specific checks — never hardcode such checks here. If `PROJECT.md` is
   missing or still `TEMPLATE`, fall back to the root `CLAUDE.md` (always in context) for
   stack/architecture/commands; note that you're running without a kit profile and that
   stack/library-specific checks are unavailable until `/bootstrap` runs, and review
   against the generic rules only. Only if *neither* carries the project's facts, say so.

## Phase 1 — Resolve the target

From `$ARGUMENTS`, in order:

- **A file or directory path** → review those files.
- **`staged`** → `git diff --cached --name-only`.
- **`HEAD~N`** (or a commit/branch ref) → `git diff <ref>...HEAD --name-only`.
- **Nothing** → working-branch diff: `git diff --name-only` (uncommitted). If empty,
  fall back to `git diff --cached --name-only`, then to the branch's merge-base diff.

Skip binary, lock, and generated files. Read each surviving file in full **and** its
diff hunks, so you judge both the change and its context. Note each file's layer/module
from `PROJECT.md` → Architecture.

**If the diff does not fit, stop and narrow — never truncate.** A truncated read loses coverage
silently while the report still looks complete. Narrow explicitly instead: `git diff --stat` for
the map of changes, then whole files one at a time, and name in the summary what stayed unread
(`core.md` → *verdicts carry denominators*).

**Collect the change's decisions — the provenance block.** List the decisions the diff embodies
before judging any of them, each tagged:

- **`[AGENT]`** — decided by an agent while building. Every row of the plan's **Deviation
  Report** (`Plan said` / `What was done` / `Reason`) is one of these, automatically.
- **`[USER]`** — decided by the user, and only with the user's **verbatim quote** from the
  conversation, in its original language, unparaphrased. **No quote, no `[USER]` tag — it is
  `[AGENT]`.** An agent that "remembers" a user decision is precisely the mechanism this tag
  exists to catch.

An empty block is a normal outcome (the plan held, nothing was quoted) — never invent decisions
to fill it. The block is context for *why the code looks like this*, never established truth:
press `[AGENT]` decisions hardest, because an agent's own choice re-labelled "the requirement"
is how a review walks past its own author. A `[USER]` decision that looks wrong is not silently
accepted either — raise it for discussion rather than reviewing around it.

## Phase 2 — Review workflow

Examine every changed file in this focus order; stop chasing once a category is clean.

1. **Correctness** — does it do what it claims? Trace the happy path and one failure
   path. Edge cases (empty, boundary, null/NaN, off-by-one), error paths and their
   safety, type/conversion hazards, concurrency (races, shared mutable state), and
   side effects reaching outside the change.
2. **Security** — untrusted input reaching a sink, injection, unsafe deserialization,
   missing authorization/scoping, secrets or PII in code or logs, fail-open where it
   should fail-closed. Apply the `paths`-matched stack security rules.
3. **Performance** — repeated I/O or queries in loops, unbounded fetches, missing
   batching/streaming, needless allocation on hot paths. Apply stack rules for the
   framework's specific anti-patterns.
4. **Readability / convention** — naming, function size, duplication, dead code,
   wrong-layer logic and dependency-direction violations, magic values. Judge against
   `code-quality.md` and the matched stack packs.

**Mandatory when the change writes state: the write-path check.** For every state-mutating
path in the diff (persist, accumulate, finalize, publish), check idempotency and races
*before* any verdict: can two paths reach the same write? does a retry or replay
double-apply? is there a guard (`status='open'`, unique constraint, upsert, processed-id
set) or only the caller's discipline? The invariant is already a write-rule
(`.claude/rules/_generic/resilience.md` → Idempotency); this is its read-side obligation. A
double-apply is CRITICAL, not a smell. If the write-path is out of the diff and you did not
open it, say so in the summary rather than letting the review imply coverage
(`core.md` → *verdicts carry denominators*).

**The verification question.** One lens over the change, not a separate pass: *if the
behaviour this change exists to produce broke where it is actually used, would verification
fail?* Trace that behaviour to its consumers (`grep -rn` the symbol) instead of measuring the
module's coverage, and state the concrete regression that would ship green — no demonstration,
no finding, the same evidence gate as everything else. Tests that do not answer the question:
ones that never executed (`testing.md` — unregistered, filtered out, skipped, disabled),
assertions on source text rather than behaviour, no-throw and snapshot-only checks, and
mock-only paths that never reach the changed code. Report a gap as *missing tests for changed
behaviour* (STRUCTURAL).

**Mandatory: comment-quality check.** Audit every added/changed comment against
`.claude/rules/_generic/code.md` — restating the code, commented-out code,
debug/TODO leftovers, wrong language, multi-idea or unterminated comments. Report each
as STYLE.

For a complex or high-risk module (intricate logic, security-sensitive, large refactor),
delegate a deeper pass to the **`deep-analyzer`** agent (or the **`security-reviewer`**
agent when the risk is security-sensitive) and fold its findings in.

## Phase 2.5 — Adversarial verification (CRITICAL findings)

Before reporting, run every **CRITICAL** candidate through the **`finding-verifier`** agent
(batches of 3–4 in parallel; its job is to KILL the finding — ambiguity defaults to REFUTED).
Then:

- **CONFIRMED** → stays CRITICAL.
- **REFUTED** → dropped, with a one-line reason in a "Dropped after verification" note.
- **STALE / UNVERIFIED** → downgraded to STRUCTURAL with the uncertainty named.

This is the same evidence gate `/arch-health` applies before its ranked table: a
plausible-but-wrong CRITICAL costs the user more than a missed STYLE nit ever will. Skip this
phase only when there are no CRITICAL candidates, or the target is a plan/epic doc (see below).

## Phase 3 — Output

Group findings by severity. Each finding: `file:line` — the problem — the rule it
violates **or** the concrete correctness/security/performance risk — a concrete fix.
Do not apply any fix.

- **CRITICAL** — correctness bugs, security holes, data-integrity or missing-authz risks.
  Must fix before merge.
- **STRUCTURAL** — wrong-layer logic, dependency/convention violations, duplication,
  performance smells, missing tests for changed behaviour.
- **STYLE** — naming, comment-quality violations, minor readability nits.

**CRITICAL findings carry their code; STRUCTURAL and STYLE carry `path:line`.** For each
CRITICAL, quote the 2–3 lines around the problem so the user decides with the code in front of
them instead of blind. This applies **only to this report** — ephemeral output, read once, where
a line anchor plus a snippet is the cheapest proof. It does **not** reach durable artifacts: plan
files, decision records and the plan write-path below keep citing symbols, not line-anchored
snippets (`rules/_generic/code.md` → *durable text cites symbols, ephemeral output cites lines*).

````
## Code Review — <target>
### CRITICAL
- `path:line` — <problem>. Violates <rule|risk>. Fix: <concrete change>.
  ```<lang>
  <the 2–3 lines around the problem>
  ```
### STRUCTURAL
- ...
### STYLE
- ...
````

End with one line: `X critical, Y structural, Z style.`

When the ask is architectural (a refactor, a new module, "is this safe to build on?"),
you may additionally label the changeset with the shared quality verdict — **SOUND /
SHORTCUT / HACK** as defined by the `quality-auditor` agent — mapping HACK→CRITICAL,
SHORTCUT→STRUCTURAL. Same evidence gate applies: a verdict below SOUND needs the proof above —
and **SOUND on a module that writes state needs its write-path opened**, else the label is
bounded in words ("sound across the read-paths I opened; write-path unread").

## When the target is a plan/epic (the one write exception)

Review-only forbids fixing the code — but when the review targets a **plan or epic doc** (not
app code), the Artifact-Continuity Contract (`rules/_generic/planning-artifacts.md`) applies:
**fold the findings into the affected plan(s)**, cross-link this review from each plan's header
(and the overview's "Reviews & decisions — READ FIRST" index), and **sweep** siblings the
findings touch. This updates the plan **DOC only** — never the application code, which stays
review-only.

## Siblings

- To **apply** quality cleanups (style/structural fixes), point to `/refactor`.
- To **debug a specific failure**, point to `/diagnose`.
- To **close test-coverage gaps**, point to `/test`.
