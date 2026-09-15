---
name: implement
disable-model-invocation: true
description: >-
  Execute a prepared plan or subtask file with quality gates. Reads the plan,
  builds a verbatim step ledger, implements each step with real-time deviation tracking,
  routes every finding (adapt / fix-and-log / file-as-card / STOP), spawns an audit
  subagent (counter-bias), runs tests, drives its slice of the epic's E2E block, and
  ends with a MANDATORY formatted report (Changes, Architecture Audit, Deviation
  Report, Cross-Session / Out-of-Scope Findings, Test Results, Commit Message).
  TRIGGER when: the user wants to carry out an existing plan
  or subtask file. DO NOT TRIGGER when: there is no plan yet — route to
  /prepare (to write one) or /analyst (to investigate) first; or the work is a new
  module/component/command modelled on an existing one that must be registered in an
  extension point — route to /scaffold.
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, AskUserQuestion, Agent
effort: high
---

# Implement Plan: $ARGUMENTS

This skill carries ONLY invariant workflow logic. Every project-specific fact
(commands, paths, architecture, integrations, deploy mapping) is read at runtime
from `.claude/PROJECT.md`.

---

## Phase 0 — Load profile

**Tooling preflight — one call, before anything else.** Some tools this skill relies on are
**deferred** by the harness: the session lists them by name only and loads their schemas on
demand, so calling one before it is fetched fails. Listing a tool in `allowed-tools` does **not**
un-defer it. Issue a single `ToolSearch` up front covering the whole run —
`select:SendMessage,TaskOutput` (continuing the *same* auditor in the Architecture Audit,
collecting a backgrounded drive) — instead of one round-trip per discovery. A name already
loaded costs nothing to include; a schema discovered missing mid-run costs a turn.

Then load context:

1. Read `.claude/PROJECT.md`. If it is missing, or still contains TEMPLATE /
   placeholder markers, fall back to the root `CLAUDE.md` (always in context) when it
   carries the commands/architecture/integrations below — proceed on it, noting you're
   running without a kit profile. Only if *neither* has those facts, **STOP** and tell
   the user: "Profile not configured — run `/bootstrap` to generate `.claude/PROJECT.md`,
   then re-run `/implement`."
2. Read the plan / subtask file passed as `$ARGUMENTS`. If `$ARGUMENTS` is a free-text
   description with no file, note that there is no plan file (the implementation
   log + archive steps below will be skipped).
   - **The plan is authoritative** (Artifact-Continuity Contract,
     `rules/_generic/planning-artifacts.md`): open every **cross-linked report** in its header
     (spike / grill / review verdicts) and the epic overview's "Reviews & decisions — READ
     FIRST" index before editing — decisions were folded into the plan, not this chat.
   - **Check the file's shape before executing it.** `00-overview.md` is `/prepare`'s reserved
     name for a **≥2-subtask index** (Phase 6.3), but plans written before that rule sometimes
     carry it over a step list. Decide by content, not by name: look for a step list
     (`## Steps`, `### S1…`, numbered steps). **Steps present** → it is a single-session plan;
     execute it exactly as written. **No steps** → it is an index; do not implement it — list the
     `NN-<subtask>.md` files it indexes with their statuses and ask which to run, or route to
     `/epic-status`.
3. Read applicable `.claude/rules/*` (conventions, patterns) that bear on the plan. If
   `CONTEXT.md` exists, read it and use the project's domain vocabulary in code, names, and the
   implementation log; respect ADRs in `docs/adr/` touching the area.
4. **Parent RUN-ORDER — look, never require.** Walk up from the plan path toward the program
   directory looking for a `RUN-ORDER.md` (the artifact is described in
   [`skills/prepare/reference/parallel-wave-execution.md`](../prepare/reference/parallel-wave-execution.md)).
   **Found** → it is the execution truth for this run: read this plan's row and honor its `Owns`
   set, its `∥` mark, and its Mode/Model over a stale plan header, plus any inline note about
   collisions with sibling rows. **Never write into it** — it has exactly one writer; your row's
   Status update goes into the final report as a proposal, and the operator (or the wave
   coordinator) applies it. **Not found** → proceed as without one, create nothing, say nothing about its
   absence; for a standalone epic that is the normal case, not a gap.

From PROJECT.md, resolve and keep handy these keys (names are profile-defined):
- **Commands** — `test`, `test:targeted`, `lint`, etc.
- **Plans/backlog location** and **Archive location**.
- **Architecture** — layers, module map, where code lives.
- **Integrations** — external APIs and where their docs are.
- **Deploy mapping** — changed-path → deploy action.

---

## Pre-Implementation Gate (MANDATORY)

Before writing code, confirm context is gathered. Skip rows that don't apply.

- [ ] **External APIs** (per PROJECT.md → Integrations): docs fetched, schema verified.
- [ ] **Bug fixes**: related tests + doc comments read and understood.
- [ ] **Features**: existing patterns in the target module reviewed.
- [ ] **Depending on untested code**: for each unit the plan's steps *call*, check for tests; with
  none, pin only the behaviour this change depends on — direct callees, one level deep, never
  transitive. Unreachable without a seam change, or >2 units → a *Flagged — NOT fixed* row.
- [ ] **Runtime/ops issues**: logs read, the error identified.
- [ ] Check the **Archive location** (PROJECT.md) for prior plans on related work.
- [ ] **Plan stage gate** (`rules/_generic/planning-artifacts.md` → Stage gates): every step
      answers WHERE + WHAT + HOW + VERIFY, and material assumptions are confirmed / verified /
      routed to `/spike`. A plan failing its gate goes back to `/prepare` with the gaps
      named — do not improvise the missing decisions mid-build.
- [ ] **Complex plans: challenge verdict present.** A Complex-tier plan should carry
      `/prepare`'s plan-challenge record ("Challenged: N findings → …", from
      `plan-challenger`). If absent, flag it and recommend running the challenge before
      building — an unchallenged complex plan is where mid-build surprises live. Proceed
      only if the user accepts the risk explicitly.

If any applicable gate is missing, gather that context FIRST — do not start editing.

---

## Build the step ledger

1. **Plan Step Extraction (MANDATORY):** extract EVERY numbered step or bullet from the
   plan into a **step ledger** — **one named file in the session scratchpad directory**,
   `<scratchpad>/implement-ledger-<slug>.md` (slug from the plan file's name, or from the task
   focus when there is no plan file). One row per step carrying the step's **EXACT text**, no
   paraphrasing, plus a `Status` column (`todo` / `done` / `deviated` / `skipped`). State the
   total step count in the ledger header; the final report accounts for every row against it.
   **Print the ledger's full path in the chat when you create it**, and re-read the file — not
   your memory of the run — whenever you need its contents.

   Verbatim extraction is the point, not bookkeeping: a numbered item copied out of the
   middle of a long plan becomes its own beginning and stops losing attention to the plan's
   first and last steps (`docs/agent-failure-modes.md` → middle-loss). The *named file* is the
   other half — a harness-side task list is not guaranteed in the session that runs this skill and
   cannot be read back in any case (`rules/_generic/delegation.md` § Deferred tools), and a
   checklist that lives only in the reply is gone at the next compaction, taking the unwritten
   deviations with it and leaving persistence nothing to copy from.
2. Classify the task:
   - **Code changes** — edits to source under the Architecture map (PROJECT.md).
   - **Non-code** — configs, rules, skills, docs.
3. Append conditional rows at the end of the ledger:
   - If code changes: `Architecture audit`, `Run tests`, `Behavior check`.
   - Always (when a plan file exists): `Write Deviation Report into plan`, `Archive plan`.
   - If tracked files changed: `Generate commit message`.
   - If deploy-relevant paths changed (PROJECT.md → Deploy mapping): `Suggest deploy`.

---

## Parallel-wave awareness

If the plan/subtask declares a **file-ownership scope** — a `Wave` / `Owns` block, or
a "YOU OWN ONLY … / DO NOT TOUCH …" instruction — this run is one of several parallel
sessions sharing one working tree. There is no merge safety net; editing a file outside
your scope silently clobbers a sibling session. Follow any `.claude/rules/*` parallel-wave
guidance, plus these invariants:

- Edit **only** files in your `Owns` scope (+ their tests). Shared files: **append-only**,
  minimal edits. A step needing any other file → classify it before touching anything:
  concurrent-sibling and serialization-point files are a **hard STOP and flag**; sequenced and
  unowned files may take a minimal logged fix. The full table is in
  [`reference/parallel-wave-execution.md`](../prepare/reference/parallel-wave-execution.md) →
  *When a necessary fix lands outside `Owns`*.
- Run **only targeted tests** for your owned modules (PROJECT.md → `test:targeted`).
  Never run the full suite mid-wave — the coordinator runs it at the wave boundary.
- **Never edit the RUN-ORDER mid-wave.** It is a serialization point with exactly one writer:
  concurrent sessions **propose**, the coordinator commits. Your row's Status update — what
  landed, what spun out, what re-priced — goes into your final report as a proposed row, never
  into the file. This holds even when the row is obviously yours and the edit is obviously right;
  two sessions writing one table is how a wave loses a row.
- **Emit a per-session commit command** — `git add` of this session's own files by explicit path
  (created / modified / deleted, plus the plan file if you appended an Implementation Log) and a
  commit message, as copy-paste text; **never run it**. One commit per session. Explicit paths are
  what make this safe alongside concurrent siblings: they stage your files and nothing else, even
  when the shared tree holds their uncommitted work. Do not archive the plan — that is the
  coordinator's step, not this session's.
- Still write the Deviation Report into the plan file and set its status frontmatter.
- In the final report: list owned files touched, flag any shared-file edits, and note
  "Part of Wave W — commit this session's files only (explicit paths, never `-A` / `.`)."

---

## Implement each step (with real-time deviation tracking)

For each step, in order:

1. Quote the step text from the plan.
2. Implement it. If the step carries a `Verify:` line (from `/prepare`), run that check now —
   the step is done when the check passes, not when the edit is saved. Set the ledger row's
   status as you go — before starting the next step, not in a batch at the end.
3. **Tighten the feedback loop.** After each step (or small coherent group), run the fastest
   applicable signal — typecheck/lint/`test:targeted` from PROJECT.md → Commands — rather than
   batching all verification to the end. A mistake caught one step later costs one step of
   rework; caught at the end, it can cost the session. Never start a step on a red bar, and when
   one reddens the suite without an obvious cause, revert to the last green and redo it smaller
   rather than debugging forward — naming the abort condition first (`docs/decision-craft.md` §1).
4. **Track deviations at the moment of decision — not retrospectively.** The instant your
   actual action differs from the plan (different approach, skipped item, extra action),
   append a row to the **ledger file's** `## Deviations` section — the file named above, on
   disk, not a line in the reply — with four fields: `Plan said` (verbatim), `What was done`,
   `Reason`, `Decided by`, and set the step's status to `deviated`. Write it before you move to
   the next step: a compaction between the decision and the report takes the unrecorded row with
   it. That section is the raw material for the Deviation Report. Do NOT reconstruct deviations
   at the end.

   **`Decided by` is `[AGENT]` unless you can paste the user's own words.** When a STOP-and-ask
   or `AskUserQuestion` answer is what changed the course, copy the reply **verbatim** into the
   cell, in the language the user wrote it, at the moment they answer: `[USER] "<quote>"`. That
   quote is the only thing a later reviewer has — review runs on the diff, in a fresh session
   where this conversation no longer exists, and a *remembered* user decision is indistinguishable
   from the agent's own (`/code-review` Phase 1 → provenance). Paraphrase, translation, or
   "the user approved this" is `[AGENT]`.

### What you CAN adapt (record as a deviation)
- Implementation details when the code differs from the plan's assumptions.
- Exact paths/names when files moved or were renamed.
- Minor technical adjustments (imports, types, error handling).

### Choosing what the plan left open
- **Where an error is handled.** Count the sites before choosing how — a declared error is part of
  the interface. In order: restate the operation so the condition is normal ("ensure X is absent",
  not "delete X"); mask it inside the module when callers can do nothing with it; let it reach one
  handler at the top of the request loop, carrying its own message. Throwing to the caller is last.
  Sites, not `try`-block width: `exception-patterns.md` §Scope still wants the smallest block.
- **Any schedule many processes share.** Jitter is not only for retries: a cron on the round hour,
  TTLs written in one burst, reconnects after a deploy, a fixed poll interval — all fire as one
  pulse and make you provision for a peak you created. Add a random offset, or hash a key in.
- **Two implementations that pass the same tests.** The shorter does not win on length: say what
  each asserts about the domain, and reject one that works only by knowing its caller's shape.

### What you CANNOT do without asking FIRST (use AskUserQuestion)
- Skip any step (even one that looks unnecessary).
- Change the business logic or core idea of a step.
- Remove functionality, or merge steps in a way that loses functionality.

### When to STOP and ask
- You want to skip a step; a step is impossible/contradictory; the plan assumes code
  that doesn't exist and you find no alternative; implementing as written would break
  existing functionality.
- **The third deviation row of one run.** Resistance is feedback about the design, not about your
  effort: files the plan never named, your own edits reverted, mocks piling up for one test. Before
  step N+1 answer which is true — wrong structure, wrong slice, accumulating breakage — or stop.

### Classify every finding before you act on it

A **finding** is anything reality hands you that the plan did not: an audit note, a failing test,
a defect you tripped over on the way past, a wrong assumption. There are **four** answers, not two
— "adapt and continue" vs "STOP the build" leaves no room for the case that is real, out of this
session's scope, and too big to fix inline.

| The finding is… | Action |
|---|---|
| **Tactical** — the plan's intent survives, only details shift | Adapt, log the deviation row, continue. |
| **Out-of-scope but small and unowned** — a one-line fix in a file no concurrent sibling owns | Fix it, and log it under *Applied — out-of-`Owns` fixes* so the operator can re-sequence it if it belongs elsewhere. |
| **Out-of-scope and large** — needs its own analysis or a decision, or lands on a serialization point / live-signal path | **Do not fix it here, and do not STOP the build for it.** File it: a *Flagged — NOT fixed* row now with a recommended fix and a named owner, promoted to a card + follow-up row at close-out. Never a silent TODO. |
| **Structural** — the plan's own approach doesn't fit reality | **STOP** and route to `/prepare` (below). |

The distinguishing question between the two middle rows is not size but: **would fixing it require
a decision the plan never made?** If yes, it is a card, not an edit.

**Two axes, and a finding must clear both:** *should this be fixed here at all* (this table) and
*may this file be touched right now* (the ownership classification in
[`reference/parallel-wave-execution.md`](../prepare/reference/parallel-wave-execution.md)).
A tactical fix in a concurrent sibling's file is still a hard stop.

Both middle rows surface in the final report's **Cross-Session / Out-of-Scope Findings** section —
flagged-and-unfixed in one table, applied-and-logged in the other. A finding that reaches neither
table was dropped, and dropping is not one of the four answers.

#### Tactical vs structural — never invent architecture mid-build

- **Tactical** — the plan's intent survives, only details shift (moved path, renamed
  symbol, an extra import, a different-but-equivalent call). → Adapt, log the deviation
  row, continue.
- **Structural** — the plan's *approach* doesn't fit reality: the assumed seam/abstraction
  is missing or wrong, an interface mismatch ripples across more than one step, a new
  architectural decision would be needed to proceed. → **STOP. Do not improvise the
  architecture inside this session** — a mid-build design invented under
  close-the-task pressure is exactly what the audit later corrects. Report the evidence
  (`path:line`, what the plan assumed vs what exists) and route per
  `rules/_generic/core.md`: back to `/prepare` for a re-plan of the affected steps,
  or `deep-analyzer` for a bounded recommendation the user approves, or AskUserQuestion
  when it changes scope. Mark the plan `BLOCKED`/`PARTIAL` honestly — a stopped build with
  a named structural gap is a *successful* outcome; a finished build on an improvised
  architecture is deferred rework.

The test: could the deviation change how *other* steps should be done, or what a reviewer
would call the design? Then it's structural, regardless of how small the edit looks.

### Hack tripwire — declared, never silent

The moment you notice the change about to land is a **shortcut over a deeper cause** — a special
case where the general fix belongs, a swallowed error, a widened type, a value hard-coded past the
real branch — **stop before it lands** and pick ONE out loud
(`rules/_generic/core.md` → the hack tripwire):

- **(a) Fix the cause now** — the real fix is in scope and bounded; do that instead of the patch.
- **(b) Ship the symptom patch DECLARED** — only when (a) is out of scope: name the cause at
  `path:line`, say why the patch is a stopgap, and file it as a *Flagged — NOT fixed* row so it
  is not lost.
- **The cheap-but-correct choice is the same move.** Name the input at which it stops working and
  write the condition beside it — *fine while N < X, because <the limit and where enforced>*;
  that line is also the revisit trigger. No nameable input, no comment — then it is just correct.
- **(c) Escalate** — the cause is structural (needs a new seam, or ripples across steps): route
  per the tactical-vs-structural rule above.

Shipping the shortcut **silently** is not on the menu. When unsure which one you are holding,
spawn a subagent: *"Is this fix architecturally correct, or a hack to make it pass?"* This fires
during implementation and during test-fixing alike — see Test Verification.

### Verify before you deviate (read the evidence — don't patch blind)
Before you record a deviation, declare a step impossible, or "fix" a surprise, gather the
evidence first — a wrong assumption here corrupts the rest of the run:
- **"Plan assumes code that doesn't exist"** → `grep`/`Glob` for it under a new name, and
  `git log`/`git blame` the area — it may have moved or been renamed, not deleted.
- **"Step contradicts what I see"** → re-read the plan step verbatim and the file it names;
  the mismatch is often a stale path the plan already anticipated.
- **A test or command fails** → read the FULL failing output (not just the last line) before
  changing anything; reproduce once if the cause isn't in the trace.
Only with the evidence in hand do you choose adapt-and-log vs. STOP-and-ask.

---

## Architecture Audit (after code changes)

You have a bias to "close the task". To counter it, spawn a **separate subagent**:

```
Use Agent (subagent_type: "quality-auditor") with prompt:
"Review the change at these paths: [paths + changed line ranges].
Task context: [one line — what the plan/change was]."
```

(`quality-auditor` is the kit's purpose-built post-implementation auditor: it classifies each
file SOUND / SHORTCUT / HACK as a counter to the implementer's close-the-task bias, and reads
`.claude/rules/` + PROJECT.md → Architecture itself — its verdicts feed the Architecture Audit
table directly. `deep-analyzer` / `code-reviewer` stay available for a second opinion. Name the
diff by path and range, never as work of your own — #23 in `docs/agent-failure-modes.md`.)

If the audit flags issues:
1. **Route each one through the finding table above** before touching anything — an audit finding
   is a finding. In-scope → fix it, refactoring to a sound solution (research a better pattern if
   unsure). Out-of-scope-and-small in a file no sibling owns → fix and log it. Out-of-scope-and-large,
   or in a concurrent-sibling / serialization-point file → *Flagged — NOT fixed*, with the owner
   named. "The auditor said so" does not widen your `Owns` set.
2. Re-audit the files you touched — **continue the SAME auditor agent** (send it a
   follow-up: "I fixed X and Y — re-check those files") rather than spawning a fresh one.
   The continuation already holds the first audit's context, so re-verdicts stay consistent
   and cost a fraction of a cold re-read; a fresh spawn may re-litigate files it already
   passed. Spawn fresh only if the original agent is no longer available.
3. **Cap the loop at 3 fix-and-re-audit rounds.** "Re-audit until everything passes" has no
   stopping condition when auditor and implementer simply disagree, and round after round of
   rewriting working code to please a reviewer is thrash (`docs/agent-failure-modes.md`).
   **At the cap, stop — a silent fourth round is the failure this cap prevents.** Instead:
   - list **every still-open finding by name** in the report's Architecture Audit table, one row
     per finding: the file, the auditor's last verdict marked open-at-cap, and in `Reason` what
     you tried and why it is still open (concrete — not "auditor disagreed");
   - set the plan status to `PARTIAL`, say in the report that the audit hit its cap with N
     findings open, and hand those findings to the user to decide — fix now, defer with a
     ticket, or accept.

---

## Test Verification

1. Run the **`test`** command from PROJECT.md → Commands. If that command is `n/a` (the
   project has no automated tests), say so in the report and skip to persistence — do not
   invent a runner.
   **Parallel wave:** run **`test:targeted`** for owned modules only (see above).
2. For EACH failure ask: **"Is the test correct, or is my implementation wrong?"**
   - Test wrong → fix the test to assert correct behavior (do not hack it to pass).
   - Implementation wrong → fix the implementation architecturally.
3. Re-run until green. A test fix that feels hacky fires the **hack tripwire** — same three
   choices as above (fix the cause / ship declared / escalate), and never the silent fourth.
4. **Two-strikes rule.** If the same failure survives two fix attempts, STOP patching. Write
   down the hypothesis your fixes were assuming, re-read the full evidence (trace, inputs,
   the code path), and test the hypothesis directly — or route to `/diagnose`. A third blind
   patch is thrash: it buries the real cause under noise and burns the context window.

---

## Behavior Check (drive the change, don't just compile it)

Green tests prove the units; they don't prove the feature. If the change has a runtime
surface and PROJECT.md → Commands defines a run/serve command, exercise the affected flow
**once, end-to-end** — invoke the CLI, hit the endpoint, run the job — and observe the new
behavior in real output. What was driven and what was observed goes into the final report.

Skip — and say so in the report — only when there is genuinely nothing to drive: docs/config
changes, pure library code with no entrypoint, or no run command defined in the profile.

**The epic's E2E block is the other half of this check.** If the epic's `00-overview.md` carries a
`## E2E verify` block (`/prepare` Phase 6.4), read it *before* driving and split it:

- Rows whose surface falls inside **this session's slice** are yours — drive them now and report
  the **observed values**, not verdicts, in the same form `/close-epic` will use.
- Every other row stays **outstanding for the coordinator**. List them **by number** in your
  report. That list is what tells `/close-epic` what close-out still has to execute; a wave
  session that drives its slice and says nothing leaves the coordinator re-deriving the split.
- **Never write `## E2E results` into `00-overview.md`.** The overview is a serialization point
  and the results block belongs to `/close-epic`, which executes the whole battery at close.

**Parallel wave:** drive **only your own slice** — never the combined result, which the coordinator
drives at the wave boundary — and name the outstanding epic-level rows in the report.

---

## Persist implementation log + archive (when a plan file exists)

The section list, the `Re-check later` table and the variants other executing skills use (`/diagnose`, `/test`, `/refactor`, …) are in [`reference/work-log.md`](reference/work-log.md).

1. **Append the implementation log** to the plan file at `$ARGUMENTS` (Edit, append-only —
   never overwrite). **Re-read the step ledger first** — `<scratchpad>/implement-ledger-<slug>.md`,
   the path you printed when you built it — and copy from its rows and its `## Deviations`
   section. The ledger is the record; the conversation is not, and after a compaction it holds
   only the tail of the run. Add `## Implementation Log — <today>` containing, per step: the step
   text, **What was done**, and any **Deviation + reason + `Decided by`** — the same content as
   the chat report's Changes Made + Deviation Report. Mark each step done / deviated / skipped
   (with the approval note). Parallel wave: scope the log to your session's steps only.
2. **Set the plan's status frontmatter** (`status`, `completed_at`, optional `notes`):
   `DONE` (all steps as described), `PARTIAL` (partial or meaningful deviations — Deviation
   rows mandatory), or `BLOCKED` (halted; reason in `notes`).
3. **Archive** per PROJECT.md → Archive location, only if such a convention exists AND:
   - status is DONE or PARTIAL (never BLOCKED — leave in place for retry), and
   - the plan lives under the backlog location and is not already in the archive, and
   - this is not a parallel-wave run (the coordinator archives).
   Move (preserve sub-path) with `git mv` if the file is git-tracked, else `mv` — never `cp`,
   the original MUST leave the source location. Verify the target exists and the source is gone.

---

## Deploy (suggest, do not run)

Map the changed files to a deploy action using PROJECT.md → Deploy mapping. Suggest the
command(s) in the report — **never** run a deploy or `git commit` automatically; let the
user decide. If the mapping says no deploy is needed for the changed paths, say so.

---

## Cross-reference

- **Input** comes from `/prepare` (the plan/subtask file).
- **Test-first:** for a slice the user wants built test-first, delegate it to `/tdd`
  (red-green-refactor) rather than writing the code then bolting tests on after.
- **Quality follow-ups:** `/code-review` (deeper review), `/test-spec` (tests derived from the
  plan's spec rather than from the code just written), `/test` (authoring/refactoring tests).

---

## MANDATORY FINAL REPORT

**STOP.** Before responding you MUST (a) append the implementation log to the plan file
(if one exists), then (b) print the report below. Fill every applicable section — no
"see above", no skipped sections that apply.

---

## Implementation Complete

### Changes Made
- [file](path#L1) — description

### Architecture Audit
*(Only if code changed)*

| File | Verdict | Reason |
|------|---------|--------|
| file | SOUND | reason |
| file | HACK — open at cap | tried X twice; auditor still flags Y |

*(If the fix-and-re-audit loop hit its 3-round cap, one `OPEN` row per still-open finding plus a
line "Audit capped at 3 rounds — N findings open, listed above for your decision", and the plan
status is `PARTIAL`. Never an audit that ends with unlisted open findings.)*

### Deviation Report
*(ALWAYS — even "no deviations" needs the explicit row, never an empty table.)*

| Plan said | What was done | Reason | Decided by |
|-----------|---------------|--------|------------|
| "Add field X to model Y" | Added to model Z | Y was renamed to Z | `[AGENT]` |
| "Add rate limiting" | Skipped | Deferred to the follow-up card | `[USER]` "давай без лимитера пока" — verbatim, never translated |

No-deviation form:

| Plan said | What was done | Reason | Decided by |
|-----------|---------------|--------|------------|
| — | Matches plan exactly | No deviations | — |

If you skipped a step, explain why and confirm user approval was obtained.
State the ledger count — `Steps: N/N accounted for` (done / deviated / skipped, no row
left at `todo`); a short count is an unfinished build, not a formatting slip. A minimal
edit still has a price: name which unit grew and what the change leaves untested.
Confirm this table + Changes Made were appended to the plan file, or note
"no plan file — log skipped".

### Cross-Session / Out-of-Scope Findings
*(ALWAYS when the plan declares a `Wave` / `Owns` scope; otherwise only if something landed
outside the plan's scope. Show "None" explicitly — an omitted section reads as "nothing found".)*

**Flagged — NOT fixed** — rows 3 and 4 of the finding table: concurrent-sibling and
serialization-point files, and anything needing a decision the plan never made. Each row names an
owner, so `/close-epic` can promote it to a card with a position:

| File | Finding | Recommended fix | Owner (subtask / session / follow-up) |
|------|---------|-----------------|---------------------------------------|
| path | what is wrong, with evidence | the fix, one line | subtask 02 (concurrent) |

**Applied — out-of-`Owns` fixes** — row 2: sequenced/unowned files fixed in place and included in
this session's commit, listed so the operator can re-sequence them if they belong elsewhere:

| File | What changed & why | Owning subtask (if any) |
|------|--------------------|-------------------------|
| path | one-line defect fixed, flagged by the audit (unowned) | none |

### Test Results
*(Only if code changed)*

- Total: N
- Passed: N
- Fixed: none / list

### Behavior Check
*(Only if code changed)*

- Drove: `<flow exercised — command/endpoint/action>` → Observed: `<actual behavior seen>`, or
- Skipped — `<no runtime surface | no run command>`.
- **Epic E2E rows** *(only when `00-overview.md` declares a `## E2E verify` block)*: Drove rows
  `<#…>` → observed `<value per row>`. **Outstanding for `/close-epic`:** rows `<#…>`
  `<why — other sessions' surfaces / needs the combined result>`.

### Commit Message
*(Only if tracked files changed — skip if all changes are gitignored)*

Per the user's global rule, do NOT run `git add` or `git commit` — only OUTPUT the
message and a ready-to-run command for the user to execute. Do not add a `Co-Authored-By`
trailer.

```
type(scope): description

- detail
```

Command for the user to run themselves (do not execute). Stage **only** the files this run
added / modified / deleted — list them by explicit path; never `git add -A` / `git add .` /
`git add <dir>` (the working tree may hold unrelated changes). `git add <path>` stages
deletions too, so include any deleted paths.

```
git add path/added path/modified path/deleted
git commit -m "type(scope): description" -m "- detail"
```

### Deploy
*(Only if deploy-relevant paths changed — per PROJECT.md → Deploy mapping)*

```
<deploy command from PROJECT.md>
<verification step, e.g. tail logs>
```

### Plan Status
*(Already written to the plan frontmatter before archiving — report what was set.)*

`status: DONE | PARTIAL | BLOCKED` · `completed_at: <today>` · `notes:` (optional)

- **DONE** — every step implemented as described (no/only cosmetic deviations).
- **PARTIAL** — partial, meaningful deviations, or an architecture audit that hit its 3-round
  cap with findings still open. Deviation rows mandatory.
- **BLOCKED** — halted (missing dependency/API, ambiguity). Reason in `notes`; not archived.

### Archive
*(Only if an archive convention exists and status is DONE/PARTIAL)*

- Moved: `<backlog path>` → `<archive path>` (via `git mv` | `mv`), or
- Skipped — reason (BLOCKED | outside backlog | already archived | parallel wave).

### Next: Spec-Based Tests
*(Only if code changed and a plan file exists)*

```
/test-spec <path-to-plan.md>
```

Derives tests from the plan's spec **without reading the implementation**, so a failure means the
code is wrong rather than the test. One line, and it costs nothing to decline.

---

## DO NOT

- Skip the Deviation Report — even "no deviations" needs the explicit row.
- Open a fourth architecture-audit round, or end a capped audit without naming every finding
  it left open.
- Overwrite the plan file — the log is append-only.
- Run `git add`, `git commit`, or a deploy automatically — output the message + command only.
- Mark a plan DONE if tests fail or the audit found unresolved issues.
- Archive a plan that wasn't fully verified, or one with status BLOCKED.
- Skip any plan step without asking first; merge/paraphrase steps so functionality is lost.
- Generate a commit message for gitignored-only changes.
- Run the full test suite mid-wave, or edit/commit outside your ownership scope.
- Write into a parent `RUN-ORDER.md` — propose the row in the report; it has one writer.
- Write `## E2E results` into `00-overview.md` — that block belongs to `/close-epic`.
- Implement a `00-overview.md` that carries no step list — it is an index, not a plan.
- Leave a large out-of-scope finding as a silent TODO, or drop it: it goes into
  *Flagged — NOT fixed* with an owner, or it did not happen.
