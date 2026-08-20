---
description: On-demand subagent delegation craft — brief-shaped prompts, the evidence-file convention, parallel/serial discipline, honest aggregation, deterministic fan-out. The judgment spine that must hold at spawn time is NOT load-bearing here — collected-not-awaited lives in always-on core.md, and spawn-time damping comes from the harness's own Agent tool description (a single-fact lookup goes straight to a search; a delegated search is not re-run in the main thread). The long-form treatments are docs/self-knowledge.md and docs/decision-craft.md — documentation, not always-on rules. This file is the orchestration how-to and loads only when AUTHORING agents/skills — a session that merely spawns subagents does not get it, which is why nothing here may be load-bearing at spawn time.
paths:
  - ".claude/agents/**"
  - ".claude/skills/**"
---

# Delegation (generic)

Rules for any skill or session that spawns subagents. A subagent is a capable stranger with
**none of your context** — treat the prompt as a written brief, and the report as testimony.

## When a spawn is worth it

A spawn is not free: it costs a written brief, a wait, and a report you are then obliged to
spot-check. Spawn when at least one of these holds:

- **Output ≫ conclusion.** The work generates far more text than the answer needs — browser
  and remote-host drives, log and trace reads, wide reconnaissance, competitive research.
- **Fresh context is the point.** Review, audit, refutation, plan-challenge — where your own
  context is the disqualification (`core.md`).
- **Genuinely parallel.** Disjoint scopes that would otherwise serialize.
- **Past your competence boundary.** Route the doubt instead of guessing through it.

Do **not** spawn when:

- The answer is one `grep` away — a brief plus a wait plus a spot-check costs more than the
  grep.
- The work **edits source or plan files** in the shared tree: a subagent has no `Owns`
  discipline and no deviation contract (`rules/_generic/parallel-wave-execution.md` — that
  contract is carried by a full session, not by a subagent). (`isolation: 'worktree'` is the
  exception, and it exists for parallel mutation, not for sparing the main thread work.)
- You would not be able to verify the report. An unverifiable report is a guess with extra
  steps.
- It is a decision. Agents inform decisions; the main thread makes them.

## The delegation boundary

**The main thread keeps** anything that writes a file, decides, or is answerable to the user:
every `Edit`/`Write` on source and plan files; deviation classification and the call to STOP;
the final report, ledger row, and commit message; and the reading of the plan plus the one or
two files a step actually modifies.

**It delegates** anything that produces far more output than conclusion: long-running drives,
wide reconnaissance ("where is X used across the repo"), log and trace reads, audits of what
this session just wrote, per-plan conformance checks at close-out.

The split is what keeps a session's context spent on judgment rather than on transcript.
Delegating a decision and hoarding a bulk read are the two ways to get it wrong, and both cost
more than they save.

## The prompt is a brief

Every agent prompt carries five parts; a missing part is filled by the agent's guess:

1. **Goal** — the question to answer or artifact to produce, and *why* (one line of purpose
   changes what a good agent prioritizes).
2. **Scope** — where to look and, as important, where **not** to (out-of-scope trees, settled
   topics, other agents' territory).
3. **Output contract** — exact format and bounds (the Finding Contract for finders; a schema
   when the caller must parse — the kit ships it as `.claude/schemas/finding.schema.json`,
   the default for multi-agent fan-outs since schema-validated JSON merges mechanically and
   retries on mismatch; keep markdown for single-agent, human-facing runs). Unbounded output
   from N agents is how a fan-out floods the session that launched it.
4. **Do-NOT list** — the failure mode you'd predict for this task, stated as a prohibition
   ("do not propose fixes, only locate", "do not read generated dirs"). One prohibition is
   standing, on every brief: **never describe the fan-out to the delegate.** A brief says what
   to investigate and what to return; "ask the second agent", "check the panel finished",
   "collect the others' results" is launch machinery, not a requirement of the task — and an
   agent handed it opens a nested review of its own.
5. **Evidence requirement** — citations (`path:line`, command output) for every claim, and an
   explicit instruction to report *negative* results ("searched X, found nothing") — an agent
   that only reports hits looks identical to one that barely searched.

The agent shares no conversation state: every fact it needs is in the prompt or in a file the
prompt tells it to read. "As discussed above" is an empty reference in a fresh context.

## The evidence-file convention

Applies to **every** finder or probe agent in a fan-out. An agent's return value lives only in
the run that spawned it — useless to the next pass. So every agent does **both**:

- **(a)** write the **full** raw output — every finding with its evidence refs, state maps,
  timings, probe numbers, console errors — to
  `<epic-or-program-dir>/evidence/<phase>-<slug>.md`, one file per agent, with a date and
  scope header;
- **(b)** return to the orchestrator only a **compact structured summary**: finding titles,
  severities, and the evidence-file path.

Verifiers read the evidence **files**, not the summaries; cards and reports link findings to
them by relative path. Binaries stay out of the record: a screenshot lives in the scratchpad
and its evidence file **describes in one line** what it showed, so the text still stands once
the image is gone.

This is what makes a wide fan-out survivable — the orchestrator holds N compact summaries
instead of N full reports — and what makes it re-runnable: the next pass diffs against the
files instead of rediscovering, and can check any claim without this session's transcripts.

## Reports are claims, not facts

- **Spot-check load-bearing citations** before acting on a report — open the one or two
  `path:line`s the conclusion rests on. Trust scales with verification, not with confidence
  of tone.
- "All X are Y" from an agent means "all X *that its search found* are Y" — the bound is the
  search, not the codebase. Ask what was searched before believing "none exist"
  (evidence-of-absence vs absence-of-evidence, as in `/discover`).
- An **empty** return is a failed unit, not a negative finding. A subagent whose prompt overflows
  dies with "Prompt is too long" and from outside that is indistinguishable from "nothing to
  report". A negative result only counts when it is stated in words ("searched X, found none");
  silence means re-run or escalate, never "clean".
- A verdict worth acting on at scale (delete list, release gate, CRITICAL finding) passes an
  adversarial check first — `finding-verifier`, or a second agent briefed to refute.

## Orchestration

- **Parallelize independent, serialize dependent.** Disjoint scopes fan out together; a stage
  that needs another's output waits for it. Never re-do work you delegated because waiting
  feels slow — two writers on one question waste both.
- **Match the agent to the work.** Mechanical sweeps go to cheap/fast configurations; verdicts
  and refutations get the strongest reasoning available (each agent's own `model:` frontmatter
  encodes this — don't override it casually).
- **Route doubt, don't guess through it.** When a load-bearing claim sits past your
  competence boundary — deep perf, security implications, framework feasibility, wide
  codebase facts — delegate *that doubt* (precisely scoped) to the specialized agent, a
  `/spike`, or the docs, instead of shipping a confident guess the caller must re-verify
  (`rules/_generic/core.md`). And the converse: don't re-spawn agents to re-check
  what a gate already verified — each doubt is routed once.
- **Vary the lens, not just the count.** N instances of the same model briefed identically
  are not N independent opinions — they share training, so they share blind spots, and
  their agreement is an echo, not accumulating evidence (failure mode #18). When stacking
  verifiers, give each a distinct frame: lens (correctness / security / does-it-reproduce),
  stance (refute vs. defend), or entry point (spec-first vs. code-first). Count
  clone-agreement as one opinion; lens-agreement as several.
- **Aggregate honestly.** Dedupe overlapping findings, keep attribution, and preserve
  disagreement between agents as a finding in itself — two agents reading the same code to
  opposite conclusions is signal about the code (or the brief), never noise to average away.
- **The synthesizer does not re-investigate.** Aggregating a fan-out is reading the reports and,
  where they are unclear, asking their authors again — not re-running the reads and searches the
  finders already did. Measured in rejudge (SYN-039): a judge holding `read`/`git_diff` stops
  delegating and re-checks the panel itself — duplicating its work, spending the context the
  fan-out existed to save, and getting captured by instructions embedded in the material it
  reopens. Here the judge is almost always the main thread, which has every tool by definition,
  so this is **discipline, not configuration**: the targeted spot-check of the one load-bearing
  citation stays (*Reports are claims, not facts*); re-reading what the finders read does not.
  When no one can confirm a claim, the synthesizer **reports the uncertainty** rather than going
  to look for itself.
- **Effort scales breadth, not just depth.** An orchestrating skill's `effort:` (and each
  agent's own `effort:` frontmatter) is a real dial: at `low` — few finders, single-vote
  verification, one round; at `high` — a wider finder pool, panel/majority verification for
  CRITICAL findings, loop-until-dry rounds, and a completeness critic at the end. Name the
  level you ran at in the report ("coverage: 1 round, single-vote") so under-coverage is
  visible, never silent.
- **Background by default; continue, don't respawn.** Spawned agents run in the background —
  launch the batch, keep working, collect on completion notifications; never fabricate a
  pending agent's result. When a follow-up needs the *same* context (a fix→re-audit loop, a
  clarification on its own report), **continue the same agent** (SendMessage / follow-up to
  its ID) instead of respawning fresh — the continuation keeps its context and verdicts
  consistent; a respawn re-reads everything and may re-litigate what it already settled.
- **Collect-on-notification is a main-session primitive — from inside a subagent, spawn
  synchronously or not at all.** Measured over the whole transcript archive: **0 of 18**
  subagent transcripts that launched a background agent ever received its notification,
  against **145 of 147** sessions. The notification is routed to the *root session* and
  delivered when control returns there — in the one case traced end to end, 27 minutes after
  the launch and 0.12 s **after** the requesting subagent had already finished. The launch
  stub still promises "You will be notified automatically when it completes"; from a
  sidechain that promise cannot be kept. So when the thing doing the spawning is itself an
  agent, pass `run_in_background: false` and take the block, or do the work inline. The
  failure is silent and expensive: the observed case re-derived 8 of its 12 delegated
  questions by hand, and paid a 9.5-minute blocking review to rediscover an interface its
  abandoned agent had already quoted in full. **When authoring a skill, this is your
  problem** — a skill that says "background; collect on notification" is unfulfillable in
  every context where that skill is dispatched into an agent. Tripwire:
  `grep -l 'Async agent launched' ~/.claude/projects/*/*/subagents/agent-*.jsonl` must come
  back empty.
- **A report you need for a verdict is collected explicitly — background is only for what the
  verdict doesn't depend on.** The rule above is about *who* spawns; this one is about *when the
  turn ends*, and it bites main sessions too — which is why the binding sentence lives in
  always-on `core.md` and only its evidence and tripwires live here. This file
  does not load at spawn time; a contract that only appears here would not be read by the
  sessions it governs. A completion notification is queued as a
  `queued_command` and becomes a turn only after the current turn ends; a session that keeps
  working, writes its report and finishes never drains the queue. Measured 2026-07-29 across two
  `/close-epic` runs: 6 agents spawned, all 6 finished **before** their parent ended, all 6
  notifications queued, **2 delivered**. The four lost included both `plan-verifier` reports —
  the plan↔code conformance the closure verdict rests on — at 10 543 and 15 347 characters, plus
  a 21 175-character probe. The parent declared the epic closed having read none of them, and
  nothing in its transcript says so. So: if the finding is an *input to your conclusion*, either
  spawn it `run_in_background: false`, or collect it with `TaskOutput` on its task id before you
  write the conclusion. "End the turn and the notification brings you back" is sound advice only
  for a session with nothing else to do — and a session closing an epic always has something else
  to do. Tripwire (the grep above does **not** catch this): count `agent-*.jsonl` under a session
  against its `<task-notification>` records of `type: user` — they must match.

## Deterministic fan-out (`Workflow`)

Some fan-outs have the same shape every time — N finders, a verify stage, a synthesis — and
prose instructions to spawn agents re-derive that shape on every run. The harness ships a
`Workflow` tool for exactly that: a script with `pipeline()` / `parallel()` / `agent(schema)`,
journaled, resumable from its `runId`, and budget-bounded — with the caveat that a resume hands
back the *cached* results of completed agents, and a cached result can itself be empty: read the
run's `journal.jsonl` before assuming a phase recovered anything.

**It is the user's call, never a skill's.** `Workflow` runs only on the user's explicit opt-in
(their keyword, a session setting, or their asking for one in their own words). No SKILL.md
contains a literal `Workflow(` call. A skill may *offer* the upgrade in one line and stop
there — `/prompt-master` → *Workflow emission* is the pattern: emit the script next to the
pack, tell the user how to run it, never invoke it.

**When a Workflow, when parallel `/implement` sessions.** Both are parallel; what differs is
where the operator stands.

| | Parallel sessions | `Workflow` |
|---|---|---|
| Operator sees | full reasoning, live, in each session | a progress tree; reasoning lands in agent transcripts + `journal.jsonl`, read after |
| Operator decides mid-run | yes — `AskUserQuestion`, review and commit between waves | no — control flow is fixed at launch |
| Quality mechanism | the human gate: report → review → commit | schema validation + adversarial verify stages |
| Recovers from a wrong turn | operator interrupts | resume from `runId`, unchanged prefix cached |
| Natural output | edited files + a report | one merged, structured verdict |

**Yes** — read-only fan-outs whose product is a verdict or a set of findings and which contain
no operator decision: whole-surface discovery passes (report + evidence + cards), close-out
verification batteries (one agent per scenario, structured returns), per-plan conformance
checks plus a completeness critic, judge panels (generate N designs → judge → synthesize),
audit and review fan-outs with adversarial verify, loop-until-dry sweeps. The unifying
property: **read-only on source, findings out, no decision inside.**

**No** — implementing waves. Not because a Workflow cannot edit files (`isolation: 'worktree'`
exists), but because it removes the review-and-commit boundary each wave passes through and
buries the reasoning the operator wants to see. A Workflow editing source in a shared tree is
the wrong tool however parallel it looks.

**The middle case worth building:** a Workflow that *prepares* a parallel launch — computes
wave safety over the `Owns` sets (the disjointness invariant in
`rules/_generic/parallel-wave-execution.md`), checks RUN-ORDER ↔ plan-frontmatter drift, drafts
the per-session briefs — and hands back N ready-to-paste commands. Deterministic work, no
decision inside, and the sessions still run under the gate.

Nothing above stops applying inside a Workflow: agents still get briefs, still write evidence
files, still return compact summaries — `schema` is how that compact return gets enforced
instead of requested.

## Deferred tools

Part of the tool surface is **deferred**: the name is visible, the schema is not, and calling
it before fetching fails. `SendMessage`, `Monitor`, `TaskOutput` and `TaskStop` — the
continue-don't-respawn and background-collection primitives this file prescribes — are
routinely among them, as are `WebFetch` and `WebSearch`.

So a run that plans to delegate fetches them **once, up front**:
`ToolSearch("select:SendMessage,Monitor,TaskOutput")`. One call before the first spawn beats
three discovered mid-run, and the check is cheap: if a tool you need appears only as a name in
a `<system-reminder>`, its schema is not loaded yet. Listing a deferred tool in a skill's
`allowed-tools` does **not** un-defer it.

## Tools an agent will not get

An `agents/*.md` `tools:` list is not what runs, and **removal is silent** — "the removal reports
no error unless it leaves the `tools` list resolving to nothing". This is not the deferred case
above: deferred means present-but-unfetched, stripped means absent, and `ToolSearch` does not
bring it back. Stripped from **every** subagent even when listed: `Agent` (at the nesting depth
limit), `AskUserQuestion`, `EndConversation`, `EnterPlanMode`, `ExitPlanMode`, `ScheduleWakeup`,
`TaskOutput`, `WaitForMcpServers`, `Workflow` — and in a fork `Agent` stays listed but returns an
error instead of spawning. Background narrows the set again; check `docs/sub-agents` §Available
tools for what survives rather than freezing a copy here. So run the check **when you add a
tool**, not as a one-off audit: an agent instructed to call a tool it cannot reach does not fail
— it invents the result (`agents/docs-writer.md` § Output options and `skills/audit-quality/SKILL.md`
are the kit's two cases, both already fixed).

**A third way a tool disappears: the build or the model tier drops it.** The todo tools
(`TodoWrite`, `TaskCreate`/`Get`/`Update`/`List`) are gated by tier and build, and the gate moves
under you: absent outright in an Opus 5 session on 2.1.220 (observed 2026-08-20, here), present as
a *deferred* tool in an Opus 5 session on that same 2.1.220 elsewhere (observed 2026-08-21). Do
not trust a named escape hatch either — `CLAUDE_CODE_ENABLE_TODO_TOOLS` does not exist in the
2.1.220 binary at all (0 hits against 14 for `CLAUDE_CODE_ENABLE_TELEMETRY` as a control), so
pinning it in `env` writes down a decision nothing executes. That is the case with no local
signal: nothing in `tools:` or `allowed-tools` changed, and the instruction rots wherever it was
written. So assume nothing either way — when a skill *prescribes* a tool call, the durable form is
a mechanism the kit owns — a checklist file, an artifact section — with the harness tool as at
most an accelerator. Progress tracking across the kit is written to files for exactly this reason
(`/implement`'s step ledger, `/sweep`'s site inventory) — and for a second reason that does not
depend on the tool existing at all: the todo list is **write-only**. There is no `TodoRead`, so
nothing can read a task list back; even where `TodoWrite` is present it is live operator display,
never a record, and never a source `/handoff` can derive "what's done" from.
