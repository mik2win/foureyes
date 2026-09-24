---
name: close-epic
description: >-
  Terminal epic-close checklist over a wave-structured decomposition (one epic =
  one <backlog>/<task-name>/ directory from /prepare Phase 6): verify every plan is
  terminal, execute the epic's declared E2E-verify block plus ONE integration test pass,
  run plan↔code conformance on deviated plans, detect docs drift the epic caused and fix
  small documentation debt inline,
  price every remaining finding (default: a named known-undone clause, NOT a card), promote only
  the survivors into a runnable follow-up board, draft the ledger/changelog row, and EMIT a
  copy-paste archive command.
  Takes ONE epic or a BATCH of them in a single invocation.
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
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, Agent
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

`$ARGUMENTS` is one epic or several (Phase 0). The card tier — worth-it gate (default: **not** a
card), the stock gate, card template, route
rubric, session packing — lives in **`reference/followups.md`**, read at Phase 5.

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

   **One invocation may name several epics — resolve the set before anything else.** Accept a space- or newline-separated list of directory names or paths under the backlog location; strip the prefix and any trailing slash, print the resolved set in the first output line, and never silently treat the first directory as the whole job. Two shapes arrive here and they price differently:

   - **Wave-batch** — one RUN-ORDER wave cutting across directories ("close wave 4"; an observed close covered 7 plans across 5 backlog directories). It is **one logical unit**: the tier (Phase 1) is computed **once over the union**, so a wave spanning five directories is never Small.
   - **Close-batch** — N independent epics handed over together, the common case for a list of paths. Each epic is priced, tiered, verified, ledger-rowed and archived **on its own**; the tier of one says nothing about the next.

   In both shapes the contract holds **per directory**: each epic's own `## E2E verify` block is executed separately, each gets its own conformance pass, its own ledger row and its own archive command. What is shared across the batch is exactly three things — the single integration test run (Phase 2, once per session and not per epic), the follow-up inventory (Phase 5, grouped by topic across epics), and the agent budget below.

   **Batch ceiling — the caps are per epic, the budget is per run.** Per-epic caps stay as the tier table sets them; on top of that a run never exceeds **8 concurrently live agents** and **~12 spawned in total**. Do the arithmetic before spawning: 5 epics × (3 drives + 1 verifier batch) is 20 agents and will not fit — so batch by *surface* across epics (one drive agent covering a surface for every epic that touched it), run the conformance verifiers in waves of 3–4, and launch **one** `completeness-critic` over the whole batch rather than one per epic. When the arithmetic still does not fit, close the batch in **two passes and say so** — a half-run close-out that dies mid-spawn is the measured failure this ceiling exists to prevent.

   **Collection is mandatory in a batch, not best-effort.** With N epics in flight the queued-notification loss (measured: 6 agents spawned, all finished before the parent ended, **2** notifications delivered) is near-certain. Either spawn with `run_in_background: false` when the next step depends on the answer, or hold a task-id list and `TaskOutput` every one of them before the conformance verdict.
3. **Parent RUN-ORDER — look, never require.** Walk up from the epic directory toward the program
   directory for a `RUN-ORDER.md`. **Found** → it is the execution truth: read this epic's row, and
   hold it for Phase 5 (follow-up rows are *proposed* into its Follow-ups section) and Phase 6
   (its Status cell is where predicted-vs-actual lands). **Not found** → proceed exactly as without
   one, create nothing, and say nothing about its absence — for a standalone epic that is the
   normal case, not a gap.

## Phase 1 — All plans terminal?

**If `PROJECT.md` → Commands carries an `epic:status` entry, run it first and quote it as the mechanical half of this phase.** A script reads row-vs-plan status drift, dangling dependencies and un-run rows deterministically, and closing an epic is exactly where a drifted status is most expensive. The kit ships one for wave-structured boards (`tools/lint-board.py lint --epic <name>`). No entry, or it fails → say so and read it all by hand; a skipped tool is never reported as a clean board.

Read every `NN-<subtask>.md` and `00-overview.md` in the epic (same evidence `/epic-status` reads:
`status` frontmatter, Implementation Log sections, archived files). A subtask is **terminal** when
its status is `DONE` or `PARTIAL` (or the file has been moved to the archive location). It is
**non-terminal** when it is `BLOCKED`, in-progress (log but no final status, or uncommitted work on
its `Owns` files), or not-started.

- Any non-terminal subtask → **list the stragglers with citations and STOP.** The user decides per
  straggler: finish it (`/implement`), fold/drop it, or accept-as-is. Do **not** flip a status
  yourself — if a subtask is done in fact but unstamped, propose the exact `status:` edit and let the
  user confirm. Closing requires every subtask terminal.
- **A plan whose status cannot be read is a straggler, not a pass.** Plan-shaped files with no
  status header at all are common in epics written before the frontmatter convention (measured in
  one 5-epic batch: two epics, 11 and 8 headerless plans). Their terminal state is *unknown*, and
  unknown never closes an epic. Read their Implementation Logs, propose the exact status header to
  add per plan with the evidence for each, and let the user confirm — writing a status where none
  existed **is** a status flip.
- All terminal → continue.

### Tier gate — computed once, here

Close-out must be proportional to the epic. Two measured close-outs of a 4-plan and a 3-plan epic
ran **39 min / 8 agents** and **34 min / 6 agents** — each more expensive than a typical
*implementation* session on the same epic (~24 min), and one of them died mid-spawn without
finishing. `/prepare` has carried a proportionality gate for a while ("Simple: 1-2 files, <200 LOC →
skip Phase 5 … keep it proportional"); this is its missing counterpart at the other end.

Compute the tier from evidence Phase 1 already holds (the per-plan statuses) plus one
`git diff --stat` over the epic's commits — **once per epic in a close-batch, once over the union in
a wave-batch** (Phase 0). Later phases **read** it; none of them recomputes or re-argues it.

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
| 5 · 6 · 7 — follow-ups · ledger · archive | gate + stock check always; a **board** only if both are green | same gates — unchanged. Zero cards filed is a normal outcome, never a skipped step |

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

## Phase 4 — Docs drift (both directions), and the small debt fixed here

Drift has two directions and they need two different checks. Most tooling covers only the first.

### 4a — Dangling refs (docs → files: something documented that no longer exists)

Detect references broken by renames / moves / splits **this epic performed** (not pre-existing rot):

1. From the epic's Implementation Logs and `git log`, list files this epic **renamed, moved, or
   deleted**.
2. `grep -rn` the docs/code for lingering references to those old paths/names.
3. Dead refs **caused by this epic** → **fix them inline** (they are on the allowlist below), or
   delegate the pass to the **`docs-writer`** agent when it is large enough to be its own task.
   Unrelated, pre-existing dead refs → just report them; they are not this epic's job to fix.

### 4b — Undocumented surface (files → docs: what the epic *added* and the profile never learned)

A reference checker cannot see this class: it verifies that mentioned things exist, so a module,
command or invariant mentioned **nowhere** is invisible to it and scores as a clean pass. This is the
drift that outlives the epic — the code is right, the map is wrong, and every later session plans
against the map. In this kit the map is `.claude/PROJECT.md`, which **every other skill reads first**:
a stale profile does not merely misinform a human, it mis-routes `/prepare`, `/implement`,
`/scaffold`, `/deploy` and this skill's own next run.

Derive the delta from **this epic's own commits**, never a repo-wide sweep — `git diff --name-status`
across them for added/renamed files, plus the new public names inside them (commands, routes, config
keys, schema tables, exported symbols). Then ask the mechanical question per name: *does any durable
doc mention it?* — `grep -rl -- "<new-name>" .claude/PROJECT.md <rules dir> <docs dir> | wc -l`.
Zero hits is a **candidate**, not proof; the thing may be documented under another name.

| What the epic added | What must know about it |
|---|---|
| a new module / package / layer, or a module that changes a layer's meaning | `PROJECT.md` → Architecture (Layers / modules, Dependency direction) |
| the first instance of a recurring shape (adapter, command, worker) | `PROJECT.md` → Canonical exemplars, and its registration/wiring point + the command that proves it |
| a new CLI verb, task-runner target, or entry point | `PROJECT.md` → Commands, and the operator docs |
| a new dependency, datastore or external integration | `PROJECT.md` → Stack / Integrations |
| a new deploy target, environment or secret | `PROJECT.md` → Deploy mapping, Security / VCS policy |
| a new invariant or threshold other code must respect | the owning project rule |
| **≥2 findings of one *silent* class** in this epic — money, time, access | a **path-scoped invariants rule**, proposed from [`assets/invariants-rule.md`](assets/invariants-rule.md) |
| a term the epic coined | the domain glossary (`/domain-model`'s `CONTEXT.md`) |
| a pattern this epic used **≥3 times** | a **candidate** rule — a card routed to `/distill`, never written here |
| a settled verdict or a dead end | the ledger row (Phase 6). A verdict is not a rule |

**The silent-class row is the one that needs a trigger, because nothing else fires for it.** A single money or timezone bug is a fixed bug; two in one epic mean the class is *shaped* by this codebase — the code has a place where wrongness does not announce itself, and the next person will land in it too. That is a rule, not a card. It is **proposed, never written here** (it is a rule, and the bucket below is explicit): hand back the filled template with the invariants the epic actually violated, each pointing at the symbol that owns it. A rule whose every line is a bug that really happened is the one kind of rule that earns its context from day one.

**Disposition — three buckets, and nothing lands in "later" by default:**

- **Applied now** — a one-line update (a module row, a Commands line, a term, a threshold inside a
  rule that already owns that subject) is on the allowlist below and just lands.
- **Proposed, not applied** — everything else this session *could* write but should not write
  unasked: a new rule or a rewritten rule section (a rule is a claim about the whole repo, argued
  from occurrences across it, and this session has read one epic), a new docs page, a `PROJECT.md`
  section that needs re-deriving rather than a line edit, or a one-liner that did not fit the budget.
  These go into the final report as **ready-to-apply edits**: target file, the exact text and where
  it goes, one line on why it did not land. **The user's go-ahead is the only unlock, and it applies
  in this same session** — do not ask preemptively, present them and continue.
- **Carded** — only what genuinely needs a *different* skill's context: a convention worth installing
  repo-wide → `/distill`, a lesson that recurred across epics → `/retro`, a profile re-derivation →
  `/bootstrap`. Those rest on occurrences this close-out never read, which is why they are not
  proposals here.

**The census is a ledger that must reconcile — this is what stops anything slipping quietly.** Every
surface the delta turned up gets **exactly one row**, including the ones that needed nothing, and the
arithmetic is stated: `N surfaces checked = applied + proposed + carded + already documented`. A count
that does not balance means a row was dropped, and a dropped row is precisely the failure this phase
exists to prevent. Report it as its own table — not scattered across the inline-fixes row, where a
profile sync is indistinguishable from a typo fix:

| Surface the epic added | Artifact that must know | What changed | Why (the claim that went stale) | Status |
|---|---|---|---|---|
| a new CLI verb | `PROJECT.md` → Commands | one row added | the profile listed N-1 of N entry points | **applied** |
| a new read module | `PROJECT.md` → Architecture | — | the layer row already covers this directory | **already documented** |
| 3× the same retry wrapper | a project rule | proposed text in the report | one epic is not evidence for a repo-wide rule | **proposed** |

**Write it into the epic's own `00-overview.md`** as `## Rules & docs sync — <YYYY-MM-DD> (close-out
pass)`, next to the `## E2E results` block (it is on the allowlist below). The chat report is
ephemeral and the epic gets archived; the record of what the close-out changed in the durable docs,
and what it deliberately did not, belongs in the artifact that survives.

**State the negative result.** "Checked N added surfaces — all present" is a reported row, and the
table is how it is reported. Silence is indistinguishable from a skipped step, which is how this drift
accumulates. Pre-existing undocumented surface the epic did not touch is reported once and left alone
— same rule as 4a.

### The inline-fix allowlist

The close-out is the last session that will ever hold this epic's full context, so trivial
documentation debt dies here rather than outliving the epic as a card nobody grabs. The boundary is
mechanical, and every fix made under it is listed in the Output with its diff size.

**Fix inline, no permission needed** — total **≤ ~15 changed lines per epic**, none behavioural:

- dead file refs and stale line anchors this epic caused (above);
- comments and docstrings this epic's own diff falsified — a comment describing the old mechanism is
  worse than no comment, and the code is in front of you;
- typos, broken links and wrong paths inside the epic's own plans / overview / spec;
- the **one-line** profile/rule syncs Phase 4b turned up — a module row, a Commands line, a coined
  term, a threshold added to a rule that already owns that subject;
- appending the `## E2E results` block (Phase 2a) and the `## Rules & docs sync` table (Phase 4b) and ticking this epic's **own** board Result cells
  with observed one-liners;
- recording a `deviated-UNLOGGED` finding the user accepted as a dated
  `### Deviations (recorded at close-out, YYYY-MM-DD)` section quoting the diff evidence — writing
  down what happened is record-keeping; deciding it is acceptable is the user's and already happened
  in Phase 3.

**Never inline — it becomes a card, however small it looks:**

- **any change to source behaviour.** A one-line bug fix is still a bug fix: unreviewed, unowned by
  any plan, and landing in a commit whose message says "close epic". This is the boundary that keeps
  a close-out from turning into an implementation session;
- anything needing a decision the epic never made;
- **authoring a new rule, or rewriting a rule or `PROJECT.md` section** — a rule is argued from
  occurrences across the repo, and this session has read one epic. It goes to Phase 4b's *proposed*
  bucket (written out in full, applied the moment the user says so) or to a card when it needs
  occurrences this session never read;
- anything past the ~15-line budget, or touching files outside this epic's blast radius;
- status flips, ledger appends, and every git verb — those stay proposals (see *Hard rules*).

## Phase 4.5 — Completeness critic (what would closing miss?)

**Standard tier → always. Small tier → only when Phase 2 or Phase 3 actually found something, or
the epic has ≥4 plans.** A clean 3-plan, single-surface epic does not earn a dedicated absence hunt;
if either check surfaced anything at all, it does.

Before drafting the ledger row, launch **exactly one** `completeness-critic` agent — in a batch,
one over the whole set and never one per epic — over the epic directory + this close-out's evidence
so far, with the scope "everything `00-overview.md` promised". It hunts absences the phase-by-phase checks can't see: an overview requirement
no subtask ever owned, a wave listed but never executed, a cross-linked review whose
verdict was never folded back, a follow-up the Implementation Logs deferred that landed
nowhere (no backlog issue, no ledger note). Each gap → the user decides: reopen (back to
`/implement` or `/triage`), or record it explicitly in the ledger row as known-undone.
Closing with silent gaps is the failure this phase exists to prevent; closing with *named*
gaps is a legitimate outcome.

**The critic hunts absences and cannot price them; pricing is Phase 5's gate, and most gaps price at
zero.** A named known-undone clause is the expected disposition for a gap carrying no consequence
class — not a consolation prize. A critic returning twenty gaps is not a mandate for twenty
dispositions above `known-undone`; it is twenty rows to price.

## Phase 5 — Findings → cards → a board someone can run

The epic's sessions recorded findings they were **right not to fix** — out of scope, or needing a
decision the plan never made (`/implement` files these as *Flagged — NOT fixed*, alongside its
STOP-and-flag notes and deferred Implementation-Log items). A close that leaves them where they are
turns them into silent TODOs; this phase is where they become work with a position — and, when they
are worth a session, a directory the next session can be pointed at.

**5a. Inventory and gate.** Sweep four sources: the epic's Implementation Logs (*Flagged — NOT
fixed*), Phase 2's failed **non-blocking** rows, Phase 3's accepted `deviated-UNLOGGED` findings,
and Phase 4.5's named gaps. **In a batch this is one inventory across all epics, grouped by topic
rather than by source epic.** Every row gets exactly one of four dispositions and appears in the
report under the one it got: **card** (confirmed, has a landing site, **and carries a consequence
sentence** — see below) · **gated card** (real, blocked on a precondition nobody here can discharge —
files with an exact trigger) · **known-undone clause in the ledger row** — **the default, not the
residue** · **dropped** (refuted or stale — with the evidence that killed it). Anything you did not
observe yourself goes through `finding-verifier` before it becomes a card. Nothing disappears
silently.

**A row leaves `known-undone` only by carrying a consequence sentence** — `<class> · <who or what
bears it> · <what goes wrong and by when>` — with the class drawn from the closed list in
`reference/followups.md` §2 (data/money loss · a wrong number on a production path · user-visible
breakage · shipped code with an unobserved verification · a blocked successor). Doc drift, stale
tallies, tooling-vocabulary gaps and rule polish argued from one epic are **never** cards, however
true. Each is then split by one test — **does the fix fit a ride-along?** ≲10 lines, written down in
full → a row in the project's **small-debt register** (`PROJECT.md` § *Plans / backlog*; create it
from `assets/small-debt-register.md` if it does not exist yet), keyed by file path, retired for free
by the next session that opens that file. Anything bigger → a **named** known-undone clause in the ledger
row. Either way it is written down by name, so nobody rediscovers it as new work. `finding-verifier`
rules on truth and never on worth — the sentence stands in for the skeptic, because the session
applying this gate is the session that authored the findings.

**Measure the open stock before adding to it** (`reference/followups.md` §2.5) and report the line
whether or not you file anything: `open boards N (M untouched >14d) · open cards C (U not started) ·
parked P`. **≥3 open boards, or any board untouched >14 days, or an epic that is itself generation
≥2** (a follow-up/residuals board, or one whose provenance names a `/close-epic` pass) → **this run
authors no new board**; survivors append to an existing board on the topic, get parked with a
trigger, or become known-undone clauses.

Every surviving row keeps its **`F<wave>.<n>` id and a one-line "why here"** — what was discovered
and why it sits there; a row without a position and a reason does not get filed, because that is how
"file a card" becomes a way to defer real work indefinitely. Cross-card file collisions are recorded
inline: *"F2.7 and F2.8 both edit `<file>` — run them in order, or merge them."*

**5b. Author the board — if 5a's stock gate is green and the operator confirmed the list.** Put the
surviving cards to the operator as **one line each** first (`NN <slug> · <consequence class> ·
<route> · <rec>`) and write nothing until they answer; an empty list after the gate is a legitimate
and common outcome, reported as such. Once confirmed, the cards are written to disk as a **runnable
epic**, not proposed as chat text — the confirmation is of *contents*, never a return to rebuilding
the board by hand — measured across close-out sessions, the operator's very next request was
usually exactly this artifact ("create a run-order/epic for the follow-ups, with prompts and cards,
so we can finish it"). Per topic (**≤3 topics per run**, ≥2 cards each): a `<topic>-followups/`
directory under the backlog location, holding the board index, one card file per work item with a
`status` header the project's tooling can read, and a session-prompts file. **Every card names its
route and its `rec: <model>/<effort>`** — the same value in all three places (card header, board
`Rec` column, session heading), scored on the shared rubric in
`skills/prepare/reference/parallel-wave-execution.md` rather than invented per file. Routes:
`/implement` when the cause is known and the files are named, `/prepare` when it is ≥5
files or crosses layers, `/diagnose` when the cause is unknown, `/analyst` or `/grill` when the
premise is undecided, `/spike` when it needs a measurement first — and sessions are packed to the
context budget `/prepare` uses, one route per session, `Owns` sets pairwise disjoint inside a wave.

Full contract — gate, caps, card template, route rubric, packing arithmetic and the two index files:
**`reference/followups.md`**.

**Where a single orphan row goes.** Parent `RUN-ORDER.md` found in Phase 0 → **propose** the row for
its Follow-ups section, formatted per the companion's template; never write it yourself, it has
exactly one writer. No RUN-ORDER → a gated card if it has a trigger, otherwise a known-undone clause
in the ledger row. **Never write into a parent program's RUN-ORDER, and never create one as a side
effect of closing an epic** — the follow-up board above is the one index this skill authors.

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

**One row per epic in a batch** — a shared row for five epics is unreadable to `/retro` and to the
next `/revisit`; the batch gets at most one extra *summary* line naming the set.

**Show the row for approval.** Append it to the ledger/changelog (Phase 0) **only after the user
approves** — that, the `## E2E results` block in `00-overview.md` (Phase 2a), the allowlisted inline
fixes (Phase 4) and the follow-up board (Phase 5b) are the only files this skill writes. If the project defines no ledger, emit the row as copy-paste text for the user to
file wherever they keep settled-work records.

## Phase 7 — Emit the archive command (never run it)

The kit never runs git. Emit a **copy-paste** block using the Archive-on-done location and the
project's convention; the user runs it. Follow the **Commit Message** pattern in `/implement`:
explicit paths only (never `git add -A` / `.` / a bare directory), no `Co-Authored-By` trailer.

```
# move each settled epic into the archive (preserve the sub-path) — one line per epic in a batch
git mv <backlog>/<epic> <archive-location>/<YYYY>/<MM>/<DD>/<epic>
# stage the approved ledger row, and the follow-up board if one was authored
git add <ledger path> <backlog>/<topic>-followups/
git commit -m "chore(backlog): close <epic…> — archive + ledger row + follow-up board"
```

`git mv` needs the destination's parent directory to exist — prepend `mkdir -p` for the dated path,
and spell the full parent path when moving a **nested** sub-epic into an already-archived parent.

If backlog docs are **local** (gitignored, per Artifact git policy), swap `git mv` for a plain `mv`
and skip the commit — say so. If there is no archive convention, leave the epic in place and note
that closing is bookkeeping-only.

## Output

**In a batch, lead with a one-row-per-epic summary table** — epic · plans terminal · tier · E2E
(N/N blocking) · conformance · inline fixes (lines) · cards spun out · ledger row · archive line —
then the per-epic detail below it. An epic missing from that table is an epic that was not closed,
and saying so is the point.

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
| 4a Dangling refs      | none / fixed / reported (pre-existing) |
| 4b Surface ↔ profile  | N checked = A applied + P proposed + C carded + D already documented (must reconcile; detail in *Rules & docs sync*) |
| 4 Inline fixes        | N lines across <files> / none — allowlist only |
| 4.5 Completeness      | no gaps / N gaps (reopened: …, recorded known-undone: …) |
| — Debt stock          | open boards N (M untouched >14d) · open cards C (U not started) · parked P — gate **green / red** |
| 5a Findings gated     | N cards · N gated · N known-undone (**named, not counted**) · N dropped (all listed below) |
| 5b Follow-up board    | `<backlog>/<topic>-followups/` — N cards, W waves / **none** (stock gate red / generation ≥2 / no topic kept ≥2 cards) — say where the survivors went |
| 6 Ledger row          | drafted — awaiting approval / appended |

### E2E results — <date>
| # | Check | Drove | Observed | vs expected | Verdict |
|---|-------|-------|----------|-------------|---------|
(the same rows written back into `00-overview.md`; baseline stated or declared missing)

### Conformance summary
<per-plan plan-verifier verdicts>

### Rules & docs sync
| Surface the epic added | Artifact that must know | What changed | Why | Status |
(one row per added surface, the ones needing nothing included; counts reconcile with the 4b row, and
the same table is written into the epic's `00-overview.md` so it survives archiving)

### Proposed doc/rule edits — not applied
| Target | Exact edit (ready to paste, and where it goes) | Why it did not land | Unlock |
(the paste-ready detail behind every `proposed` row above — say "go" on any and it lands in this
session; over-budget is a reason to propose, never to drop)

### Findings — disposition (every row appears exactly once)
| F-id | Finding | Disposition | Where it landed / why not |

### Follow-up board — `<backlog>/<topic>-followups/`
| # | Card | Route | Wave | Est. context | Why here |
(plus the wave map, the per-session context projections, and any cross-card file collisions)

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
- **Never authors a parent program's RUN-ORDER.** Follow-up rows are *proposed* into an existing
  one; absence of one is not a gap and not something to fix while closing. The follow-up board of
  Phase 5b is the one index this skill creates, and only for cards its own gate kept.
- **Never files an unverified row into the small-debt register, and never sweeps it on a row count.**
  Rows rot; a sweep that fixes without re-reading writes new drift over old, and a count is not
  evidence a sweep is worth a session.
- **Never cards a finding it cannot write the consequence sentence for.** True is not the bar; the
  closed class list in `reference/followups.md` §2 is. Everything else real becomes a *named*
  known-undone clause — named, so the next close-out does not rediscover it as new work.
- **Never authors a new board while the stock gate is red**, or while closing an epic that is itself
  generation ≥2. A close-out that keeps spawning boards of its own size is re-financing debt, not
  retiring it; survivors merge into an open board, get parked, or land in the ledger row.
- **Never writes a card file before the user has confirmed the one-line list.** The board is still
  authored on disk once they say go — the confirmation is of contents, not of the artifact.
- **Never authors a rule or a profile section at close *unasked*.** The epic's delta is evidence for
  *one* epic; a rule needs the repo. Sync the one-liners, write the rest out as proposed edits in the
  report, and apply them here the moment the user says to. What stays a card is only what needs
  occurrences this session never read (`/distill` / `/retro` / `/bootstrap`).
- **Never reports a census that does not reconcile**, or one that omits the surfaces which needed
  nothing. A missing row and a silent drop look identical from the outside; the table exists so they
  cannot.
- **Never lets an edit exceed the inline budget silently.** Over-budget is a reason to propose, never
  a reason to drop: the report names every edit that did not land and why.
- **Never fixes source behaviour inline.** The Phase 4 allowlist is documentation, comments and plan
  text; a one-line bug fix at close is unreviewed, unowned by any plan, and buried in an archive
  commit. It becomes a card with a route.
- **Never closes a batch partially in silence.** Every epic named in the invocation appears in the
  summary table with a verdict, including "not closed — stragglers" and "deferred to a second pass".
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
- **`/triage`** — the natural inbox for the follow-up board Phase 5b authors (a card routed
  `/prepare` is an analysis request, not a bug report).
- **`assets/small-debt-register.md`** — the register's own contract, shipped as the template a
  project copies on first use: what may enter, the three ways a row dies, and why no row count ever
  triggers a sweep.
- **`reference/followups.md`** — the card tier in full: the worth-it gate, the card template, the
  route rubric, session packing, and the two index files Phase 5b writes.
- **`/handoff`** — snapshot an *unfinished* session (this skill settles a *finished* epic).
- **`plan-verifier`** / **`docs-writer`** agents — plan↔code conformance and docs-drift fixes.
