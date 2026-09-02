# Follow-ups → cards → epics (close-out's card tier)

Read at **Phase 5** of `/close-epic`. Owns everything between "the close-out found things" and "the operator has a board they can run": the worth-it gate (§2, whose default is **not** a card), the stock gate that decides whether a board may be authored at all (§2.5), topic grouping, the card file, the route rubric, session packing, and the two index files. `/prepare`'s decomposition contract is NOT restated here — `skills/prepare/reference/parallel-wave-execution.md` and `/prepare` Phase 6 stay the source for wave schedules, file-ownership matrices, the context budget and prompt format; this file says what a *close-out* is allowed to author and how a finding becomes a runnable session.

Every path, filename and status vocabulary below comes from `.claude/PROJECT.md` (backlog location, archive location, issue/plan naming, artifact git policy) — the shapes here are the contract, not the literals.

Why this tier exists: measured across one project's close-out sessions, **10 of 14** were immediately followed by the operator asking for the same artifact by hand — "create a run-order/epic for the follow-ups, with prompts and cards, so we can finish it", "if the follow-ups are small, do them now". The board was being rebuilt conversationally after every close, which is work the session that found the debt was already positioned to do.

## 1. Inventory — four sources, one list

Sweep, in this order: **(a)** *Flagged — NOT fixed* rows in each plan's Implementation Log (`/implement` files them there by contract — and by contract is where profile/rule edits land, since those are serialization-point files a wave session flags rather than edits); **(b)** Phase 2's failed **non-blocking** E2E rows; **(c)** `plan-verifier`'s `deviated-UNLOGGED` / `step-missing-from-code` findings the user chose to accept rather than fix; **(d)** the `completeness-critic`'s GAPS-FOUND rows; **(e)** Phase 4b's undocumented surface that was too big for the inline allowlist.

**In a batch the inventory is one list across all epics, grouped by topic and not by source epic.** Two epics that both left the same class of debt produce one card, not two — that is the whole point of closing them together, and it is the only thing a batch buys that N separate closes do not. Every row carries its origin (`<epic>/<plan> · F2.7`) so the trail survives the regrouping.

## 2. The worth-it gate — the default is *not* a card

**The default disposition is `known-undone`. A card is what a row earns, not what it gets for being true.** That inversion is the gate. The wording it replaces ("something breaks **or misleads** if it is never done") made a card the cheapest outcome to argue for — a stale comment misleads by definition — while the alternative asked for an unmeasurable "the cost of fixing exceeds the cost of living with it". Measured in one project on the run that forced this rewrite: a close-out's first draft carded **ten** findings across three boards; **seven** were documentation hygiene *about the tooling that does documentation hygiene*. All real. None with a consequence anyone would pay a session for. **Cards survive on consequence, not on truth.**

Each inventory row gets exactly one of four dispositions, and every row appears in the report under the one it got:

| Disposition | When | Where it lands |
|---|---|---|
| **Card in a follow-up epic** | CONFIRMED, has a named landing site (files), **and carries a consequence sentence from the closed list below** | `<backlog>/<topic>-followups/NN-<slug>.md` |
| **Gated card** | real, but blocked on a date / data / infra / audience — a precondition nobody in this session can discharge | the project's parked-plans location, with an **exact trigger** and the condition that fires it |
| **Known-undone clause in the ledger row** | **everything else that is real — this is the default, not the residue** | Phase 6's ledger row, named in one clause |
| **Dropped** | REFUTED or STALE — the claim does not hold against the current tree | the report, with the evidence that killed it. Never deleted silently |

### The consequence sentence — the only exit from `known-undone`

One line, this form, or the row is `known-undone` by construction:

`<class> · <who or what bears it> · <what goes wrong, and by when>`

**The classes are a closed list. Nothing outside it becomes a card, however true it is:**

1. **Data or money loss** — records, state or a store are silently lost or overrun; or a documented capacity is wrong by an order of magnitude *and* something is sized from it.
2. **A wrong number on a production path** — a threshold, limit or sizing constant that is stale or wrong in code that runs unattended.
3. **User-visible breakage** — a gesture, command or endpoint that fails, hangs, or answers with a wrong value.
4. **Shipped code with an unobserved verification** — a declared E2E / AC row that was never actually driven, on code already merged.
5. **A blocked successor** — a named next card or epic cannot start until this lands.

**Never a card, whatever it looks like.** These become `known-undone` clauses, and they are named there in one clause each *so nobody rediscovers them as new work*:

- doc or comment drift with no behavioural consequence — including a comment this epic's diff falsified that fell past the inline budget;
- a count, tally or census figure quoted in a docstring, a rule or a header;
- vocabulary, mark-set or coverage gaps in **tooling that reports on already-stale boards**;
- tests for a dev-only tool, or coverage debt with no failing behaviour behind it;
- a convention or rule polish argued from **one** epic's occurrences (the repo-wide bar is several occurrences, and it belongs to the convention-distilling skill);
- anything whose entire cost is "a future human reading this might be mildly misled". **"Misleads" earns a card only when the misled reader is a machine or a production gate** — never when it is a person already reading the code around it.

**Where the never-card rows actually go.** A ledger clause is a *verdict index* entry — real, named, and never opened by anyone looking for work, which is how "recorded" becomes "invisible". So the never-card list is split by one test: **does the fix fit a ride-along?** If it is ≲10 lines and can be written down in full, it becomes a row in the project's **small-debt register** — one file, one row per zero-consequence fix, **keyed by file path** so any session about to edit that file greps it and takes what is there for free. If the fix does not fit — a test suite, a refactor, a rule needing occurrences nobody has read — it stays a **known-undone clause in the ledger row**, the honest artifact for real work nobody is scheduling.

Its location is a project fact (`PROJECT.md` § *Plans / backlog* → **Small-debt register**); when the profile names none, or the file does not exist yet, create it from **`assets/small-debt-register.md`** — that template *is* the contract, and three parts of it are load-bearing: **rows are verified before filing** (an unverified row outlives the tree it was true of), **the fix is written down in full** (if the next session re-derives it, batching saved nothing and the row was a card in disguise), and **no row count triggers anything** — a sweep session fires on the operator's word only, boxed to docs/comments/anchors with every row re-verified first. Measured on one project: an audit residue treated as a queue became a **nine-plan epic**, because the rows were cheap only while the files were already open.

**Why a sentence and not a judgement.** The gate's structural weakness is that the session applying it authored the findings — a finder cannot price their own finds, and that is exactly how it failed in practice, in the operator's own words: *"the worth-it gate failed because the author of the findings applied it to their own findings."* The sentence is the cheap mechanical substitute for an external skeptic: a row you cannot write it for has failed, and there is no argument to have. `finding-verifier` does **not** cover this — it rules on truth, never on worth.

**CONFIRMED is a verdict you fetch, not one you feel.** Any row you intend to promote to a card *and* whose defect you have not observed yourself this session goes through the **`finding-verifier`** agent first (CONFIRMED / REFUTED / STALE, batches of 3–4). This is the cheapest step in the tier and the one that stops a close-out from filing debt that was already fixed two epics ago. A row you *did* observe (a failed E2E row you drove, a diff you read) is CONFIRMED by that observation — say which.

**Caps.** At most **3** new follow-up epics per run — beyond that the grouping is wrong, not the world. Fewer than **2** cards on a topic → not an epic: it goes to the parent program's Follow-ups section as a proposed row (never written by you), or to the parked-plans location. More than **8** cards on one topic → the topic is an epic in its own right and belongs to `/prepare`, not here; say so and stop at the card list. **These bound containers, not work** — 3 boards × 8 cards is twenty-four sessions and is not what the caps permit. And the `≥2 cards per topic` floor is a floor, never a quota: pairing a second small finding to reach it is how a board gets built out of things that failed the gate. The bound on *work* is §2.5.

## 2.5. Stock before supply — measure the open debt before adding to it

**Before the gate keeps anything, count what is already open, and report the result whether or not you file a card:** every follow-up board in the backlog that is not archived, its card count, how many of those cards were never started, and the date each board was last touched (`git log -1 --format=%ad --date=short -- <board>`).

Measured in one project on the run that forced this section into existence: **8 open boards · 30 cards · 21 never started**, plus 24 more parked — while the close-out in progress was authoring the ninth board. Boards are not dead weight (11 were archived that month), but the split was sharp: UI / infra boards got run; research and strategy boards stalled for weeks. **A new board is not free capacity — it is a claim on the same operator who has not reached the last five.**

**The stock gate. Red → this run authors no new board:**

- **≥3 open follow-up boards**, or **any open board untouched for >14 days** → no new board. Rows that survive §2 go (a) appended to the nearest existing open board on the same topic, (b) to the parked-plans location with a trigger, or (c) into the ledger as known-undone. State which, per row.
- The stock line is reported **always**, with its denominators: `open boards N (M untouched >14d) · open cards C (U not started) · parked P`. A close-out that files cards without stating what is already unfiled is hiding the one number that decides the question.

**Generation depth.** An epic whose slug marks it as a follow-up or residuals board, or whose board provenance names a `/close-epic` pass, is **generation ≥2**: closing it authors **no new board at all** — survivors merge into an existing board, get parked with a trigger, or become known-undone. The chain this breaks was measured at four generations of roughly constant size, each spawned by the close-out of the one before. A close-out that finances its own debt is not a converging series, and every generation costs one session to author and another to run.

**One approval line before any file is written.** When §2 and the stock gate leave a non-empty card list, put it to the operator as one line per card — `NN <slug> · <consequence class> · <route> · <rec>` — and write nothing until they answer. This is not a return to proposing boards as chat text: the board is still authored on disk, still runnable, still not rebuilt by hand. It is one confirmation of *contents*, priced at one message, standing between the close-out and a directory nobody asked for.

## 3. Naming and layout

`<backlog>/<topic>-followups/` — the slug names the *capability or defect family*, never a date and never the parent epic when the batch merged several. Contents:

```
<backlog>/<topic>-followups/
  00-RUN-ORDER.md            board · why this exists · wave schedule · file-ownership matrix · integration pass
  NN-<slug>.md               one card per work item, with a status header the project's tooling reads
  implementation-prompts.md  one copy-paste prompt per session, waves marked
```

The board's table is `| # | Card | Wave | Route | Rec | Status | Result |` — the **Rec** column is not optional, and it carries the same `<model>/<effort>` as the card header and the session heading. Three places, one value: a board that names a route but not a model makes the operator re-derive the hardest judgement in the file every time they launch a session.

**Picking it is a rubric, not a vibe.** Score complexity on the *Recommended model / effort* table in `skills/prepare/reference/parallel-wave-execution.md` — **strongest · high/xhigh** for novel deep-module design, cross-cutting rewrites and contract-defining work later waves code against; **default · medium/high** for careful surgery in existing central files and moderately complex work with a detailed spec; **cheapest · low/medium** for mechanical, mirror and pattern-copy tasks. Then apply that file's **risk overlay**: irreversible, server-side/live-path, schema-writing or wide-blast-radius work takes the strongest tier *even when the diff looks mechanical*. Tiers are what the rubric fixes; the model names behind them come from what is available at launch, and the suffix stays advisory.

Two calls the shared rubric does not make for a close-out. A **drive or measurement card** ships no production code, yet its verdicts are what the next decision rests on — price it on how easy it is to fool yourself, not on diff size, which puts it at the default tier rather than the cheapest. And a card whose whole job is a **record correction** really is mechanical — cheapest tier — *unless* it re-points a grep or an assertion that other files pin, which is the one place a cheap model reliably ships a false all-clear.

The board must open with **who made it and from what**: `**Created**: <date>, by the /close-epic pass over <parent epic(s)> | **Cards**: N | **Source of every finding**: <plan-verifier reports / critic gaps / E2E rows>`, plus the F-id → card mapping. A board whose provenance is not written on it gets re-litigated within a week.

## 4. Card file template

```markdown
---
status: PLANNED
---

# NN — <Card Title>

**Wave**: W1 | **Owns**: <paths this session may edit> | **Reads**: <paths> | **Deps**: <NN or None> | **Shared edits**: none | **Est. Context**: ~<N>k
**Route**: /implement | **Rec**: <model>/<effort> | **Origin**: <parent-epic>/<plan> § Flagged — NOT fixed (F2.7) | **Verified**: CONFIRMED (finding-verifier, <date>) | **Size**: S (~2 files, ~40 LOC)
**Consequence**: <class from §2> · <who or what bears it> · <what goes wrong, and by when>

## Problem
<what is wrong, stated so it is checkable — not "improve X">

## Evidence
<path:line, the observed value, the command that produced it. The close-out already paid for this; a card that drops it makes the next session re-derive it>

## Change
<what to do, at the altitude the route implies — for /implement, concrete enough to build; for /prepare, the question the analysis must answer>

## Verify
<the observable that says it is done — a command and its expected output>
```

The status header is not decoration: a card the project's plan tooling cannot parse is invisible to `/epic-status`, `/triage` and the next close-out. Use whatever shape that tooling reads (`PROJECT.md` → Plans / backlog).

## 5. Route rubric — where the next session starts

The card names its route, and the prompt is written **for that route**. Getting this wrong is expensive in both directions: a `/prepare` on a two-line fix burns a session on ceremony, an `/implement` on an undertold premise gets rewritten.

| The card's shape | Route | The prompt says |
|---|---|---|
| Defect, cause known, files named, ≲3 files, no cross-layer ripple | **`/implement <card path>`** | the constraint set and what NOT to touch |
| Defect, cause **unknown** — a symptom with no traced chain | **`/diagnose <symptom>`** | the observed evidence and the two hypotheses it splits |
| Change touching ≥5 files, crossing layers, adding a dependency, or with an unmapped blast radius | **`/prepare <card path>`** → then `/implement` | that the deliverable is the plan, not the code |
| The premise is undecided — the card states a goal but not what would satisfy it | **`/analyst`** (spec) or **`/grill`** (a decision between named options) | the options and the constraint that will decide between them |
| The answer is unknown and needs a measurement before any design | **`/spike <question>`** | the pre-registered bar: what result means go, what means kill |
| A convention or lesson worth installing repo-wide (Phase 4b's ≥3-occurrence findings) | **`/distill`** (a convention) or **`/retro`** (a lesson that recurred) | the occurrences observed here, and which rule tier should own it |
| A profile section that needs re-deriving rather than a line edit | **`/bootstrap`** — named as a *proposed* edit in the close-out report first, run in this session if the user says go | which `PROJECT.md` section went stale and what the epic changed under it |
| Blocked on a precondition nobody here can discharge | **no session** — parked plans | (the trigger, in the card) |

A card whose route is `/prepare` or `/spike` must **not** carry an `Owns` set that pretends the files are known — write `**Owns**: TBD (route: /prepare)` and keep it out of the wave-disjointness arithmetic by giving it its own wave or its own session.

## 6. Session packing

Group cards into **sessions**, then sessions into **waves**, against the same context budget `/prepare` uses for subtasks (`skills/prepare/reference/parallel-wave-execution.md`):

- **Project, don't guess**: each card carries `Est. Context`. A session's projection is the sum of its cards plus the fixed session overhead (skill body, rules, the reads every session pays — ~30k in a measured project). Land inside the budget with headroom; a session that opens near the ceiling degrades in recall before it ends, and one far under it pays session overhead for nothing.
- **Never pack across routes**: one session runs one route. `/implement` cards may share a session; an `/implement` and a `/prepare` may not.
- **Never pack across waves**, and never pack cards whose `Owns` sets intersect into *parallel* sessions — that is the wave-safety invariant, not a preference.
- **Coupled surfaces are sequenced, not parallelised**: two cards that edit different files but render into the same visual row (or write the same table) are file-disjoint and still not safe concurrently. Say so on both cards and put the joint check on the integration pass.

Self-check before reporting the board: run whatever wave-safety lint the project ships (`PROJECT.md` → Commands) and verify by hand what it does not cover — no dependency cycles, no dangling `Deps`, `Owns` sets pairwise disjoint inside each parallel wave, board ↔ prompts at parity. A board that does not pass its own lint is not a deliverable.

## 7. The session-prompts file

**This file is `/prepare`'s artifact and `/prepare` owns its shape. Do not invent a lighter one here.** The template — the `## Execution Order` map, the `## Wave W<n>` sections, the `### Session NN — <title> · rec: <model>/<effort>` heading, and the fenced brief with its `Solo:` / `OWN (edit only these):` / `READ-ONLY (context):` / `DO NOT TOUCH:` / `Out-of-OWN fix?` / `Siblings this wave:` / `Tests:` / `Commit:` lines — lives in `skills/prepare/reference/parallel-wave-execution.md` § *Per-session brief*. Copy it; a close-out board's sessions are launched by the same operator, into the same wave model, as a `/prepare` board's.

Three things that template makes non-negotiable, and that a hand-rolled prompt loses:

- **The `## Execution Order` line is how parallelism is stated.** `W1: [01 ∥ 02] → W2: [03] → W3: [04 ∥ 05]` — sessions inside one `[…]` are file-disjoint and may be launched concurrently; a wave with one entry is sequential, and a session that must run alone says `Solo: YES` **with its reason**. A board that implies concurrency only by two cards sharing a wave number has not stated it.
- **The heading and every note live OUTSIDE the fence; the slash command is the FIRST line inside it.** A slash command expands only when the message *starts* with it, so a heading or a hand-off note riding above the command turns the invocation into plain text — the skill never loads and **nothing reports an error**. This is also why two cards packed into one session get **two fenced blocks pasted as two messages**, never one block with two commands: only the first would expand.
- **`DO NOT TOUCH` is annotated per file** — `[<NN> · concurrent|future|merged]` — so the session knows which collisions are hard (a concurrent sibling) and which are merely sequenced.

The `rec:` value is the same one the card's `**Rec**:` field and the board's `Rec` column carry — never a fourth opinion. Close-out-specific prompt rules, all load-bearing:

- **Self-contained.** The next session has none of this context. Name the files, the invariant, and the verify command inside the prompt.
- **State the hard NOTs.** What this session must not touch, and why — the cross-card collisions from §6 live here.
- **Point at the evidence, don't re-derive it.** "READ FIRST, do not re-derive — the chain is traced in `<path>`" saves a session from repeating the close-out's work.
- **Every session ends the same way**: edit only `Owns`, log deviations in the card as they happen, append an Implementation Log with a terminal status, record out-of-`Owns` findings under *Flagged — NOT fixed* instead of fixing them, and emit the commit command as text (never run it).
- Head the file with the wave map and the shared-constraint paragraph once, so the per-session blocks stay short.

Close with an **integration pass** section: what to run once after the last wave merges (the project's integration test command, the cross-card checks no single session could make, and *tick the board rows with one-line Results* — a finished board with empty Result cells reads as "nothing ran").

## 8. Still not yours, even here

Authoring the follow-up board does not widen the close-out's writing rights anywhere else:

- The **parent program's** `RUN-ORDER.md` (its Follow-ups section, its Status cells) has exactly one writer and it is not this skill — propose the rows as text.
- Status flips in the **closing** epic stay proposals; the user confirms completion.
- The ledger row is appended only after approval.
- Every git verb — the rename, the staging, the commit — is emitted as copy-paste text and never run, including for the new board you just authored.
- Cards describe fixes; **the close-out does not implement them.** A card you could have fixed in five minutes is still a card unless it is inside the inline-fix allowlist in `SKILL.md` Phase 4 — and if it is neither, it is a `known-undone` clause, not a card (§2).
- **Authoring a board is not the close-out's success metric.** A run that files zero cards and names six known-undone clauses has done this tier correctly; a run that files six cards because six findings were true has not. The deliverable is a *disposition for every row*; the board is only what survives §2 and §2.5.
