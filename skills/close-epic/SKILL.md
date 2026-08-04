---
name: close-epic
description: >-
  Terminal epic-close checklist over a wave-structured decomposition (one epic =
  one <backlog>/<task-name>/ directory from /prepare Phase 6): verify every plan is
  terminal, execute the epic's declared E2E-verify block (or derive a battery from the
  surfaces its diff touched) plus ONE integration test pass, run plan↔code conformance on
  deviated plans, detect docs drift the epic caused, promote flagged findings to follow-up
  cards, draft the ledger/changelog row, and EMIT a copy-paste archive command.
  Never flips statuses, never runs git.
  TRIGGER when: a multi-session epic looks finished and should be settled and archived —
  "close the epic", "settle and archive this", "finalize the epic", or right after its
  last wave merges. TRIGGER ALSO on the same request phrased as plain work, with this skill
  unnamed — "run the verification steps from the overview", "can this be archived" — a
  task-shaped ask for an epic's end-to-end verification IS this skill.
  A bare progress/completion question about an epic is NOT: that is `/epic-status`, a cheap
  read-only look, and routing it here buys a full close-out contract nobody asked for.
  DO NOT TRIGGER when: snapshotting an UNfinished session (use /handoff), checking progress /
  next-wave (use /epic-status), executing a wave (use /implement), or grooming single issues
  (use /triage).
allowed-tools: Read, Grep, Glob, Bash, Edit, Agent
effort: high
---

# Close Epic: $ARGUMENTS

The **terminal** counterpart of `/epic-status` (which reports progress) and `/handoff` (which
snapshots an *unfinished* session). This closes the loop **plan → code → ledger** so settled work
is never re-researched, and nothing is archived half-verified. It reports, verifies, drafts, and
**emits** — it does not flip statuses and it never runs git.

This skill carries only invariant close-out logic. The backlog/archive locations, the integration
test command, the drive commands for each surface, and the ledger location all come from
`.claude/PROJECT.md`. `Bash` is for the verification runs and read-only inspection (`git log`,
`git status`, `ls`) — never mutation.

**Verification adapts to what the epic was about.** A test suite plus a docs grep proves almost
nothing about a chart that renders an interpolated line across a data gap, or a route that 200s on
malformed input. Phase 2 executes the checks the epic declared for its own surfaces — and derives
them from the diff when it declared none.

## Phase 0 — Load profile & resolve the epic

**Tooling preflight — one call, before step 1.** Some tools this skill relies on are **deferred**
by the harness: the session lists them by name only and loads their schemas on demand, so calling
one before it is fetched fails. Listing a tool in `allowed-tools` does **not** un-defer it. Issue
a single `ToolSearch` up front covering the whole run — `select:SendMessage,TaskOutput,Monitor`
(continuing a `plan-verifier` or a delegated drive agent, collecting a backgrounded verification
run, waiting on a long one) — instead of one round-trip per discovery. A name already loaded
costs nothing to include; a schema discovered missing mid-run costs a turn.

1. Read `.claude/PROJECT.md`. If missing or `profile_status: TEMPLATE`, fall back to the root
   `CLAUDE.md` (always in context) when it carries the backlog/archive locations and test command —
   note you're running without a kit profile — and only **STOP** → run `/bootstrap` first if
   *neither* has them. Resolve and hold:
   - **Plans / backlog location** and the **Archive on done** location (PROJECT.md → Plans / backlog).
     If there is no archive convention, note it — the archive command in Phase 7 degrades to a plain
     `mv`/left-in-place suggestion.
   - **Integration/full test command** (`test`, PROJECT.md → Commands) — run **once** at close.
   - **Drive commands per surface** (PROJECT.md → Commands: how to start the app, drive a browser,
     probe the deployed instance, invoke the CLI, query the store). Phase 2 needs these; a surface
     whose drive command the profile does not define is reported as **undrivable here**, not
     improvised with a guessed tool or host.
   - **Ledger / changelog** — the record of settled epics, if the project keeps one (PROJECT.md →
     Plans / backlog, or Conventions notes). If none is defined, Phase 6 emits the row as copy-paste
     text instead of appending it.
   - **Artifact git policy** — whether backlog docs are committed or local (governs the archive
     command in Phase 7).
2. `$ARGUMENTS` names the epic — a directory under the backlog location, or its name. If empty, glob
   the backlog location for directories containing a `00-overview.md`, list them, and **ask** which
   epic to close. Do not guess. See `skills/prepare/reference/parallel-wave-execution.md` for the
   wave layout and `/epic-status` for how per-subtask status is derived.

   **One invocation may span several epic directories.** An observed close-out covered 7 plans
   across 5 backlog directories because a RUN-ORDER wave cut across them — "close wave 4" is a
   legitimate ask, and "the epic" is then a *set*. Resolve that set up front and name it in the
   output. The contract then holds **per directory**: each epic's own `## E2E verify` block is
   executed separately, each gets its own ledger row and its own archive command. The tier
   (Phase 1) is computed **once over the union** — a wave spanning five directories is not Small.
   Never silently treat the first directory as the whole job.
3. **Parent RUN-ORDER — look, never require.** Walk up from the epic directory toward the program
   directory for a `RUN-ORDER.md`. **Found** → it is the execution truth: read this epic's row, and
   hold it for Phase 5 (follow-up rows are *proposed* into its Follow-ups section) and Phase 6
   (its Status cell is where predicted-vs-actual lands). **Not found** → proceed exactly as without
   one, create nothing, and say nothing about its absence — for a standalone epic that is the
   normal case, not a gap.

## Phase 1 — All plans terminal?

Read every `NN-<subtask>.md` and `00-overview.md` in the epic (same evidence `/epic-status` reads:
`status` frontmatter, Implementation Log sections, archived files). A subtask is **terminal** when
its status is `DONE` or `PARTIAL` (or the file has been moved to the archive location). It is
**non-terminal** when it is `BLOCKED`, in-progress (log but no final status, or uncommitted work on
its `Owns` files), or not-started.

- Any non-terminal subtask → **list the stragglers with citations and STOP.** The user decides per
  straggler: finish it (`/implement`), fold/drop it, or accept-as-is. Do **not** flip a status
  yourself — if a subtask is done in fact but unstamped, propose the exact `status:` edit and let the
  user confirm. Closing requires every subtask terminal.
- All terminal → continue.

### Tier gate — computed once, here

Close-out must be proportional to the epic. Two measured close-outs of a 4-plan and a 3-plan epic
ran **39 min / 8 agents** and **34 min / 6 agents** — each more expensive than a typical
*implementation* session on the same epic (~24 min), and one of them died mid-spawn without
finishing. `/prepare` has carried a proportionality gate for a while ("Simple: 1-2 files, <200 LOC →
skip Phase 5 … keep it proportional"); this is its missing counterpart at the other end.

Compute the tier **once**, right here, from evidence Phase 1 already holds (the per-plan statuses)
plus one `git diff --stat` over the epic's commits. Later phases **read** it; none of them
recomputes or re-argues it.

**Small** — all four hold:

- **≤3 plans** in the epic;
- **≤1 drivable surface** among the changed paths — count *distinct drive mechanisms*, not files
  and not source directories. Two paths are one surface when a single drive exercises both: a
  serializer whose only consumer is the UI you are already driving is that UI's surface. They are
  two when each needs its own drive (a route with an independent contract, a CLI verb, a store
  query) — that is the count Phase 2b would have to run separately;
- **no live-signal path and no deployed/remote surface** among the changed paths;
- **no plan stamped with a deviating terminal status** (`PARTIAL`). A plan that landed `DONE` *and*
  logged deviations is **not** the signal — a logged deviation is the healthy case, and treating its
  mere presence as a flag is precisely the degeneracy Phase 3's filter used to carry.

**Standard** — everything else. A condition you cannot settle from evidence resolves to Standard.

| Phase | Standard | Small |
|---|---|---|
| 2 — drive the E2E battery | one agent per browser scenario / remote probe / log sweep | **inline**, behind a **2-failure tripwire** — delegate a scenario only after its *second* failed round |
| 3 — plan↔code conformance | one `plan-verifier` per deviated plan, batches of 3–4 | **one** `plan-verifier` for the whole epic; **inline** at ≤2 deviated plans |
| 4.5 — completeness critic | always | only when Phase 2 or Phase 3 found something, **or** the epic has ≥4 plans |
| 2c — integration pass | always | **always — unchanged.** Cheap, and the one check that catches breakage *between* plans |
| 5 · 6 · 7 — follow-ups · ledger · archive | always | always — unchanged |

**`Standard` carries its own caps — the tier switch is not the whole of proportionality.** Four
consecutive measured closes all landed `Standard` (4, 6, 5 and 7 plans): the gate computed
correctly every time and changed nothing, because real epics are rarely ≤3 plans. So the expensive
branch gets bounded too:

- **Drive agents: at most 3**, batching scenarios by *surface* rather than one agent per E2E row.
  An observed run spawned 5 for a single epic's block.
- **`plan-verifier`: batches of 3–4** over the Phase 3 *anchored* deviated set — never one agent
  per plan in the epic.
- **`completeness-critic`: exactly one**, launched alongside the last verifiers rather than after
  them.
- At every tier, **do independent work while the fan-out runs** — see *Waiting is not a tool call*
  in Phase 2.

**The tier is a reported row, not a private decision.** It goes into the Output table with the
counts that produced it. A silent downgrade *is* the failure this gate exists to prevent: without
the row, nobody can tell "thin verification because the epic was Small" from "a step got skipped".

## Phase 2 — Verify the epic end-to-end

The battery fits the epic, not a fixed checklist: 2a when the epic declared its own checks, 2b when
it did not, and 2c always.

### 2a — Execute the declared `## E2E verify` block

An epic prepared under the current contract carries one in `00-overview.md` (`/prepare` Phase 6.4;
template in `skills/prepare/reference/parallel-wave-execution.md`). Execute it **row by row**:

- **Record observed values, not verdicts.** `cold deep-link paints at 0.135 s` and
  `Σ bars[].count + off_range = 135,562 == total`, never "fast" and "reconciles". A number is
  re-checkable a quarter from now; an adjective is not.
- Append `## E2E results — <YYYY-MM-DD> (close-out pass)` beneath the block in `00-overview.md` —
  one row per check: observed value, verdict, and the exact command that produced it. This is one of
  the two files the skill edits (the other is the ledger).
- **A blocking row fails → STOP.** The epic does not close.
- **A non-blocking row fails →** it becomes a follow-up card (Phase 5), not a blocked close.
- **Never invent the baseline at close.** The baseline was captured at prepare time, before the
  change destroyed the thing it measured. If the block has none, report the delta as *unmeasurable —
  no baseline captured*: a stated gap, not an estimate.
- **A live-signal path is not driven to "verify" it.** State the blast radius and leave the call to
  the operator — the one surface where the check itself is the risk.

### 2b — No block? Derive the battery from what the diff touched

Older epics, and any prepared before this contract, have no block. Do not fall back to the test
suite alone. List the paths the epic actually changed (Implementation Logs + `git log`/`git diff
--stat` over its commits), map them to surfaces via `PROJECT.md` → Architecture, and run the
mandatory battery for each surface present:

| Surface the changed paths land in | Mandatory battery |
|---|---|
| **UI** (templates, client scripts/styles, static assets) | Start the app; drive the real flow with the profile's browser-drive command; assert on **rendered state**, not on source. Capture a screenshot of the changed surface. |
| **HTTP API** (routes, handlers, serializers) | Live server: happy path, not-found, malformed input, and one **timing** measurement against the baseline. |
| **Deployed / remote surface** (per PROJECT.md → Deploy) | Probe the deployed instance with the profile's remote-probe command — or state explicitly that it was unreachable and the check is **outstanding**. Never infer remote health from local. |
| **CLI** | Invoke each changed verb once with real arguments; capture stdout. |
| **Data ingest / persistence** | Query the store directly and compare it against the invariant the epic claims (row counts, null/sentinel ratios, uniqueness). |
| **Live-signal path** | Do **not** drive. Report the blast radius; require an explicit operator decision. |
| **Pure library / docs / config** | Full suite + an explicit "no runtime surface" row. Do not manufacture a drive. |

Then add the checks **specific to this epic's own claims** — that is where the value is; the table
only guarantees the floor. Say so in the report: **"battery derived from changed paths, not
declared at prepare time."** A derived battery is the weaker artifact — it is written by someone who
already knows what the code does, which is exactly the reverse-planning bias the prepare-time block
exists to avoid.

### 2c — One integration pass

Run the **full** test command (PROJECT.md → Commands → `test`) **once**, at close — the documented
post-wave integration step (`skills/prepare/reference/parallel-wave-execution.md`), not a per-session
run. Never hardcode the command. It is **one row of the verification, not the verification**.

- Green → record the result and continue.
- Red → **report the failures verbatim and STOP.** The epic does not close on a failing suite.

### Driving is delegated; the verdict is not

Browser scenarios, remote probes, and wide log sweeps produce large low-value output (page HTML,
traces, retry noise) and return a small answer — the delegation boundary in
`rules/_generic/delegation.md`. The measured cost of keeping them inline: one observed close-out
burned ~8 consecutive failed browser rounds in the main thread, and every stack trace landed in the
context that then had to write the report.

- **Delegate** — one agent per browser scenario, per remote probe, per wide log sweep. Each returns
  `{check_id, drove, observed, verdict, evidence}` and nothing else.
  **On a `Small` epic (Phase 1's tier gate) drive inline behind a 2-failure tripwire:** delegate a
  scenario only once it has failed **twice**. Read the measurement above precisely — what burned the
  context was a *repeating* failure, ~8 consecutive failed rounds, not a first attempt. A drive that
  works costs one screenshot and one number, and an agent spawned for it costs more than it saves.
  Hence a threshold, not unconditional delegation. Once the tripwire fires, delegate exactly as
  Standard does — the fallback is the old behaviour, in full.
- **Keep in the main thread** — the verdict on whether the epic closes, the ledger row, and every
  edit to a plan or overview file.
- **Spot-check — mandatory, not a habit.** Re-derive **at least one load-bearing number yourself**
  from the raw evidence, without reusing the agent's arithmetic. Reports are claims
  (`delegation.md`). The output names which number you re-derived and whether it matched.

**Waiting is not a tool call.** The harness re-invokes you when a delegated agent finishes — the
notification arrives on its own. Never build a wait loop. Measured: one close-out spent **250 of
its 317 tool calls (79%) on `sleep` + `ls` polling** — 126 backgrounded sleeps and 124 directory
listings inside 16 minutes — while this skill's own preflight had already loaded `Monitor` and
`TaskOutput` and called neither. Three correct shapes, in order of preference:

- **Do independent work.** The follow-up inventory, the ledger format, the docs-drift grep, the
  integration pass — none of it depends on the verifiers. A close-out that worked this way
  finished in 25 min / 107 calls; the polling one took 41 min / 317 for a comparable epic.
- **Need one agent's output** → `TaskOutput` on its task id. **Need to block until a condition
  holds** → `Monitor`. Never `sleep`, never a repeated `ls` over the tasks directory.
- **Nothing to do and nothing to collect** → say what you are waiting on and end the turn. The
  notification brings you back; a polling loop only burns the context that has to write the report.

> **Collect before you conclude — the notification is not a promise.** Doing independent work is
> right, but it is exactly what makes the notification miss: a completion notification is *queued*
> and becomes a turn only after the current turn ends, so a run that keeps working, writes its
> verdict and finishes never drains the queue. Measured 2026-07-29 over two runs of this skill:
> 6 agents spawned, all 6 finished before the parent ended, all 6 notifications queued, **2
> delivered**. Lost: both `plan-verifier` reports (10 543 + 15 347 chars — the Phase 3 conformance
> this closure rests on) and a 21 175-char probe. Both runs declared the epic closed having read
> none of them, and neither transcript admits it. So before writing the Phase 3 verdict or the
> ledger row: for every agent you spawned, either its report is in your context, or you call
> `TaskOutput` on its task id. **An outstanding verifier is a Phase 3 result of "not verified",
> never a pass** — and if you spawned it to decide something, `run_in_background: false` is the
> cheaper contract than remembering to collect.

## Phase 3 — Plan ↔ code conformance (deviated plans only)

Not every plan needs verifying — only those that recorded a **deviation**. Find them:

```bash
grep -lE '^#{2,4} +(Deviations|Plan Deviation Report) *$|^status: +PARTIAL' <backlog>/$ARGUMENTS/*.md
```

**The pattern is anchored to a section heading on purpose — an unanchored one is still
degenerate.** Two things must stay out of it:

- **`Implementation Log`.** `/implement` appends one to *every* plan it runs, by contract, so any
  filter containing it selects 100% of plans and the phase heading's "deviated plans only" becomes
  decorative.
- **A bare `Deviation` substring.** It matches prose anywhere in the file — "no deviations", a
  narrative "deviation from the plan copy", a template line — not an actual deviation section.

Measured over **105 plans across 24 epics**: the `Implementation Log` pattern selected 97% (102
plans), the substring pattern still selected 84% (88), and the anchored pattern above selects
**41%** (43) — the plans
that genuinely carry a deviation section or a `PARTIAL` stamp. That halves this phase's fan-out,
and the halving lands on `Standard`-tier epics, which is where the agent cost actually sits.
If a project's plans record deviations under a different heading, widen the alternation — but keep
it anchored to the heading, never to a word that can appear in a sentence.

For each such plan, launch the **`plan-verifier`** agent (one per plan, in parallel batches of 3–4)
to check that the code matches the plan as amended by its logged deviations. **Small tier** (Phase 1)
→ **one** `plan-verifier` over the whole epic instead of one per plan, and at ≤2 deviated plans do
the conformance read **inline**. Any
`deviated-UNLOGGED` (code diverged with no log entry) or `step-missing-from-code` finding →
**surface it; the user decides fix-vs-accept before closing.** A clean conformance across all
deviated plans is required to proceed.

**Optional upgrade the *user* can run: this sweep as a deterministic `Workflow`.** N plans through
a verify pipeline with Phase 4.5's completeness critic as the final stage, every verdict returned
against a `schema` — the same shape, journaled and resumable, instead of hand-managed batches.
Two limits, both hard: (1) **user-opt-in only** — it runs on the user's explicit ask, never
launched from this skill, so offer it in one line and run the batches above when they don't;
(2) **read-only fan-out only** — it qualifies because the verifiers read plans and code and return
*verdicts*, editing nothing; the fix-vs-accept call on every finding, and the decision to close,
stay here. See `rules/_generic/delegation.md` → *Deterministic fan-out*.

## Phase 4 — Docs drift the epic caused

Detect references broken by renames / moves / splits **this epic performed** (not pre-existing rot):

1. From the epic's Implementation Logs and `git log`, list files this epic **renamed, moved, or
   deleted**.
2. `grep -rn` the docs/code for lingering references to those old paths/names.
3. Dead refs **caused by this epic** → offer to fix inline, or delegate the pass to the
   **`docs-writer`** agent. Unrelated, pre-existing dead refs → just report them; they are not this
   epic's job to fix.

## Phase 4.5 — Completeness critic (what would closing miss?)

**Standard tier → always. Small tier → only when Phase 2 or Phase 3 actually found something, or
the epic has ≥4 plans.** A clean 3-plan, single-surface epic does not earn a dedicated absence hunt;
if either check surfaced anything at all, it does.

Before drafting the ledger row, launch the **`completeness-critic`** agent over the epic
directory + this close-out's evidence so far, with the scope "everything `00-overview.md`
promised". It hunts absences the phase-by-phase checks can't see: an overview requirement
no subtask ever owned, a wave listed but never executed, a cross-linked review whose
verdict was never folded back, a follow-up the Implementation Logs deferred that landed
nowhere (no backlog issue, no ledger note). Each gap → the user decides: reopen (back to
`/implement` or `/triage`), or record it explicitly in the ledger row as known-undone.
Closing with silent gaps is the failure this phase exists to prevent; closing with *named*
gaps is a legitimate outcome.

## Phase 5 — Promote flagged findings to follow-up cards

The epic's sessions recorded findings they were **right not to fix** — out of scope, or needing a
decision the plan never made (`/implement` files these as *Flagged — NOT fixed*, alongside its
STOP-and-flag notes and deferred Implementation-Log items). A close that leaves them where they are
turns them into silent TODOs; this phase is where they become work with a position.

Sweep three sources: the epic's Implementation Logs, Phase 2's failed **non-blocking** rows, and
Phase 4.5's named gaps. For each finding:

1. **Draft a card** — the problem, the recommended fix, the file(s) it lands in, and a one-line
   size estimate. Silent TODOs and bare "should probably" notes are not an outcome.
2. **Give it a follow-up id and a position** — `F<wave>.<n>`, plus a one-line **"why here"** that
   says what was discovered and why it sits at that spot. A row without a position and a reason
   does not get filed: that is how "file a card" becomes a way to defer real work indefinitely.
3. **Record cross-card file collisions inline** — *"F2.7 and F2.8 both edit `<file>` — run them in
   order, or merge them."* Two follow-ups on one file is a serialization fact, not a footnote.

**Where the rows go.** Parent `RUN-ORDER.md` found in Phase 0 → **propose** the rows for its
Follow-ups section, formatted per the companion's template; never write them yourself, it has
exactly one writer. No RUN-ORDER → emit the cards as copy-paste text and name where you would file
them. **Do not create a RUN-ORDER as a side effect of closing an epic.**

## Phase 6 — Draft the ledger / changelog row

Close the loop per the Artifact-Continuity Contract (`rules/_generic/planning-artifacts.md`): a
settled epic's outcome is **persisted**, so the decision is never re-litigated from chat memory.
Draft one row:

- **topic** — the epic name / what it delivered.
- **verdict** — e.g. `shipped` · `superseded` · `dormant` · `dropped` (project's own vocabulary).
- **summary** — one line: what changed and why it mattered.
- **link** — relative path to the epic's authoritative doc (`00-overview.md` or the archive path).
- **predicted vs actual** — one line: waves planned vs run · subtasks planned vs shipped ·
  follow-ups spun out (Phase 5) · any re-pricing the epic discovered ("effort was M, not S — 7
  files across backend + frontend"). This is the only place an epic's **real cost** stays visible.
  Without it nobody can tell a healthy discovery rate from systematic under-scoping at `/prepare`,
  and it is precisely the signal `/retro` and `/revisit` need and currently cannot see. If a parent
  RUN-ORDER exists, the same line belongs in this epic's Status cell — **propose** it, don't write it.

**Show the row for approval.** Append it to the ledger/changelog (Phase 0) **only after the user
approves** — that plus the `## E2E results` block in `00-overview.md` (Phase 2a) are the only files
this skill edits. If the project defines no ledger, emit the row as copy-paste text for the user to
file wherever they keep settled-work records.

## Phase 7 — Emit the archive command (never run it)

The kit never runs git. Emit a **copy-paste** block using the Archive-on-done location and the
project's convention; the user runs it. Follow the **Commit Message** pattern in `/implement`:
explicit paths only (never `git add -A` / `.` / a bare directory), no `Co-Authored-By` trailer.

```
# move the settled epic into the archive (preserve the sub-path)
git mv <backlog>/$ARGUMENTS <archive-location>/<YYYY>/<MM>/<DD>/$ARGUMENTS
# stage the approved ledger row too, if one was appended
git add <ledger path>
git commit -m "chore(backlog): close $ARGUMENTS — archive + ledger row"
```

If backlog docs are **local** (gitignored, per Artifact git policy), swap `git mv` for a plain `mv`
and skip the commit — say so. If there is no archive convention, leave the epic in place and note
that closing is bookkeeping-only.

## Output

```
## Close Epic: <task-name>

| Step | Result |
|------|--------|
| 1 All terminal        | PASS (N/N terminal) / STOP (stragglers: …) |
| **1 Tier**            | **Small** (N plans · 1 surface: <ui> · no live-signal · no PARTIAL) / **Standard** (<which condition failed>) — drove inline / delegated · conformance: per-plan / one-agent / inline · critic: run / skipped (Small, nothing found) |
| 2a E2E block          | PASS (N/N blocking) / STOP (row K: expected …, observed …) / **no block — battery derived (2b)** |
| 2b Derived battery    | surfaces: <ui · http-api · remote · cli · data> — driven / undrivable (<why>) |
| 2c Integration pass   | PASS / FAIL (verbatim failures) |
| — Number re-derived   | <which one>: agent said X, I got Y — match / MISMATCH |
| 3 Plan↔code conformance | PASS (M deviated plans clean) / attention (…) |
| 4 Docs drift          | none / fixed / reported (pre-existing) |
| 4.5 Completeness      | no gaps / N gaps (reopened: …, recorded known-undone: …) |
| 5 Follow-ups promoted | N cards drafted (F2.1–F2.N) / none |
| 6 Ledger row          | drafted — awaiting approval / appended |

### E2E results — <date>
| # | Check | Drove | Observed | vs expected | Verdict |
|---|-------|-------|----------|-------------|---------|
(the same rows written back into `00-overview.md`; baseline stated or declared missing)

### Conformance summary
<per-plan plan-verifier verdicts>

### Follow-up cards (for the RUN-ORDER's Follow-ups section, or to file as-is)
| # | Card | Mode | Why here |
(plus any cross-card file collisions, inline)

### Ledger / changelog row (for approval)
<the drafted row, including predicted-vs-actual>

### Archive command (copy-paste — run it yourself)
<the block from Phase 7>
```

Every claim is citable to a file+line or a command's output.

## The tier trade-off, stated plainly

The `Small` tier **weakens verification on small epics**. That is the deal, not a side effect: fewer
independent readers means a real defect is likelier to survive the close. It is taken because the
opposite failure was measured and is worse — a close-out costing more than the work it closes gets
skipped, run half-way, or killed mid-run, and an epic that never closes is verified by nobody.

Three things bound the downside, and none of them is optional:

- **The tripwire reverses the choice on contact with reality.** A drive that fails twice is
  delegated exactly as Standard would delegate it. Inline is the bet; failure cancels the bet.
- **`make test` and the E2E block run at every tier.** The floor does not move. `Small` changes
  *who executes* a check, never *whether* it runs.
- **The tier row makes the trade visible.** It is printed with the counts that produced it, so a
  thin close-out is legible as a deliberate `Small` run rather than mistaken for a thorough one.

If any of the three is missing from a run, the trade is not being made — corners are.

## Hard rules

- **Never runs git.** `git mv` / `git add` / `git commit` are emitted as copy-paste text only —
  the user runs them.
- **`git mv` is git.** It reads as moving a file and it is not: it stages a rename in the index.
  Archiving an epic directory yourself is the rule most likely to be broken here — an observed
  close-out session ran `git mv backlog/<epic> backlog/realised/…` on its own. Emit it; never run it.
- **Never downgrades silently.** The tier is computed once in Phase 1 and printed as its own Output
  row with the counts behind it. A `Small` run that does not say it is `Small` is indistinguishable
  from a skipped step, which is the whole failure mode the gate was added to close.
- **Never flips a status.** Non-terminal stragglers stop the close; propose exact status edits, the
  user confirms completion. Done-in-git-history alone is not proof — confirm with the user.
- **Never closes on red.** A failing **blocking** E2E row, a failing integration pass, or an
  unexamined `deviated-UNLOGGED` finding halts the close. A failing *non-blocking* row does not —
  it becomes a follow-up card.
- **Never invents a baseline, never fakes a drive.** A baseline not captured at prepare time is
  reported missing; a surface with no drive command in the profile is reported undrivable. Neither
  is estimated, and neither is inferred from a different environment.
- **Never authors a RUN-ORDER.** Follow-up rows are *proposed* into an existing one; absence of one
  is not a gap and not something to fix while closing.
- **Facts from PROJECT.md.** Backlog/archive locations, the test and drive commands, and the ledger
  location come from the profile — never hardcoded.
- **Evidence only.** Every terminal/conformance/E2E claim comes from disk or from a command's output
  (frontmatter, logs, git, observed values), never conversational memory. Observed values, not
  adjectives.

## See also

- **`/epic-status`** — read-only progress dashboard over the same epic (its non-terminal
  counterpart), and the right home for a bare progress/completion question — that asks for a look,
  not a close-out.
- **`/prepare`** — creates the wave-structured decomposition this skill closes, and writes the
  `## E2E verify` block Phase 2a executes (Phase 6.4; `reference/parallel-wave-execution.md` holds
  the canonical layout, the RUN-ORDER and E2E templates, and the post-wave integration step).
- **`/implement`** — runs one subtask; stamps `status`, writes the Implementation Log this skill
  verifies, and files the *Flagged — NOT fixed* rows Phase 5 promotes. Mirrors its **Commit
  Message** pattern for the emitted git block.
- **`/triage`** — the natural inbox for the follow-up cards Phase 5 drafts (a card with
  `Mode: P → I` is a `/prepare` request, not a bug report).
- **`/handoff`** — snapshot an *unfinished* session (this skill settles a *finished* epic).
- **`plan-verifier`** / **`docs-writer`** agents — plan↔code conformance and docs-drift fixes.
