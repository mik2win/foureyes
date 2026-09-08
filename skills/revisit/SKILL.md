---
name: revisit
disable-model-invocation: true
description: >-
  Decision re-review discipline — audit past architecture/technology decisions (ADRs,
  select-tech picks, structural choices baked into code with no record) by extracting each
  decision's load-bearing assumptions and testing them against TODAY's reality, internal
  and external. Verdict per decision: HOLDS / STRAINED (tripwire set) / BROKEN (reopen
  with evidence). Guards both failure modes: drive-by relitigation and silent ossification.
  TRIGGER when: the user asks "is X still the right choice", "we decided this a year ago —
  does it still make sense", "review our past decisions", "why do we even use Y", or a
  skill hits a prior ADR that looks stale.
  DO NOT TRIGGER when: making a NEW technology choice (use /select-tech), scanning code
  for rot rather than decisions for staleness (use /arch-health), recording a fresh
  decision (use /domain-model), or deciding a service boundary with no prior decision on
  file (use /decompose).
allowed-tools: Read, Grep, Glob, Bash, Write, WebFetch, WebSearch, AskUserQuestion, Agent
effort: high
---

# Revisit Decisions: $ARGUMENTS

`$ARGUMENTS` names one decision to re-examine ("the choice of Redis for sessions", an ADR
number) or is empty = inventory all recorded and load-bearing decisions and triage them.

## Principle

Code rots visibly; **decisions rot silently**. Every decision was correct *given its
assumptions* — expected scale, team size, what the ecosystem offered, what the product
needed. The code stays; the assumptions expire; nobody is notified. A codebase can be
clean at every `path:line` and still be built on choices that stopped making sense two
years ago.

The counterweight has a failure mode of its own: **relitigation**. Reopening settled
decisions because a new session "would have chosen differently" destroys the stability
that lets teams build. So this skill is an **assumption audit, not a preference audit**:
a decision is reopened only when a *named load-bearing assumption* is shown false today,
with evidence. "I'd have picked otherwise" is not grounds; "the library was chosen for
feature X, which the stdlib has shipped natively since" is.

This skill **verdicts and routes** — the re-decision itself happens in the routed skill.

## Phase 0 — Load profile & inventory sources

1. Read `.claude/PROJECT.md` — **Stack**, **Architecture**, **Integrations**, **Plans
   location**. Missing or `TEMPLATE` → fall back to the root `CLAUDE.md` (always in context)
   when it carries those facts, proceeding on it and noting you're running without a kit
   profile; only if *neither* has them, **STOP**, run `/bootstrap` first.
2. Decision sources, in order of authority:
   - `docs/adr/` (or the ADR location in `PROJECT.md`) — recorded decisions.
   - The Plans location — `/select-tech` reports, `/rollout` strategies, archived plans
     with decision sections.
   - `CONTEXT.md` — terms that encode decisions.
   - **Undocumented decisions** — load-bearing choices visible only in code: the
     framework, the queue, the ORM, a pervasive pattern. No record ≠ no decision; it means
     the assumptions were never written down.
3. Recalled knowledge about any tool or library is **dated by construction**
   (`core.md`) — and the revisiting agent is itself the stalest instrument in
   the room: its sense of "what people use now" froze at training time. That disqualifies
   it as a *source* and makes its own instinct one more assumption to test — every
   external fact in Phase 2 gets verified live, including the ones that feel certain.

## Phase 1 — Extract the load-bearing assumptions

For each decision in scope, state: **what was decided · when · what it assumed.**

- From an ADR: read its Context/Consequences; the assumptions are usually explicit.
- From an undocumented decision: **decision archaeology** — `git log` the introducing
  commit(s), the PR description if reachable, the state of the tree at the time. Write
  down the reconstructed assumptions and mark them **RECONSTRUCTED** (lower confidence —
  the bar for calling them broken is correspondingly higher, since you may have guessed
  the rationale wrong). Propose a retro-ADR via `/domain-model` so the next revisit
  doesn't re-dig.
- An assumption is load-bearing only if its falsity would have changed the decision.
  List 2–5 per decision, each **falsifiable** ("traffic stays under N", "no native
  alternative exists", "team stays at one squad") — vague assumptions can't be tested and
  don't count.

## Phase 2 — Test each assumption against today

**Predict before you peek** (`core.md`): before checking, write the expected
finding; a surprise is signal either way.

- **Internal evidence** (the repo can answer): current scale/usage numbers, call-site
  counts (`grep -rn`), whether the pain the decision solved still exists, whether the
  constraint it honored still binds, churn around the decision's code. Fan out agents for
  breadth; every claim cites `path:line` or a command's output.
- **External evidence** (the world can answer — this is where research happens):
  is the dependency alive (issue tracker, release cadence, maintainer count — the
  `/select-tech` lens: the tracker over the README)? Has the ecosystem moved — language/
  framework/platform now covering natively what the dependency was adopted for? Has a
  category-winner emerged since? Verify via WebFetch/WebSearch **live, never from
  memory**. A broad "what does the landscape look like now" question routes to the global
  `/deep-research`; a testable "would our hard case work on Y now" routes to `/spike`.
- **User evidence** (only the user can answer): team size/shape changes, product
  direction, actual production numbers not visible in the repo. Ask via
  `AskUserQuestion` — never assume the org held still.

## Phase 3 — Verdict per decision

| Verdict | Meaning | Action |
|---------|---------|--------|
| **HOLDS** | load-bearing assumptions verified true today | re-affirm: note "revisited YYYY-MM-DD — holds" on the ADR; no further work |
| **STRAINED** | an assumption is weakening but not false | set a **tripwire** — a measurable condition ("p95 > Xms", "library goes 12 months without a release", "second team forms") recorded on the ADR; do NOT reopen now |
| **BROKEN** | a named load-bearing assumption is false today, with evidence — an accumulated list of the tool's defects is not one unless a named defect blocks a named requirement | reopen — route in Phase 4 |

The **anti-relitigation gate**: a BROKEN verdict must cite the assumption verbatim and
the evidence that falsifies it. If you cannot fill both slots, the verdict is HOLDS or
STRAINED — however much a different choice might appeal. Conversely, HOLDS must rest on
*checked* assumptions, not on deference to the document: "the ADR says so" is not
verification.

## Phase 4 — Route what's broken; record everything

| Reopened decision is about… | Route |
|-----------------------------|-------|
| A library/framework/service choice | `/select-tech` — fresh selection; the incumbent goes on the ballot with its **escape cost** priced in |
| Structure / module shape | `/arch-health` (find the leverage) or `/prepare` (change is known) |
| A service boundary (split/merge) | `/decompose` |
| Shipping the replacement | `/rollout` — a reversed decision is usually a risky migration |

Recording (via `/domain-model`): **never edit a past ADR's substance — supersede it** with
a new ADR linking back ("supersedes ADR-NNNN; assumption X broken by Y"). History is how
future sessions avoid re-digging. HOLDS/STRAINED annotations (revisit date, tripwires) are
the only in-place additions. Apply file changes only with user confirmation.

## Output

`Write` the table below as a durable report to the **Plans location** from `PROJECT.md`
(e.g. `<plans>/<YYYY-MM-DD>-revisit.md`; git policy per `PROJECT.md` → Artifact git
policy) — tripwires are worthless if they die with the session — then present it:

```
## Decision Revisit — <scope>

| Decision (ADR/source) | Age | Load-bearing assumptions | Verdict | Evidence | Route |

### Reopened
- <decision> — assumption broken: "<verbatim>" — evidence: <fact> → /select-tech | /prepare | /decompose

### Tripwires set (STRAINED)
- <decision> — reopen when: <measurable condition>

### Undocumented decisions found
- <choice> — reconstructed assumptions … → retro-ADR proposed

### Held
- <decision> — revisited, holds (assumptions checked: …)
```

## Hard rules

- **Assumption audit, not preference audit.** Reopen only on a named broken assumption
  with evidence; taste is never grounds.
- **Frustration is knowledge, not a verdict on the tool.** A list of a tool's defects is what
  operating it produces; a replacement looks clean because nobody has operated it yet. Reopen on a
  named defect blocking a named requirement — a list of learned defects is a tripwire, not a break.
- **HOLDS requires checking.** Re-affirming without testing the assumptions is
  ossification wearing a checkmark.
- **External facts verified live** — recalled library/ecosystem knowledge is dated by
  construction.
- **Supersede, never rewrite.** Past ADRs are history; changes land as new ADRs.
- **Verdict and route only** — the re-decision happens in `/select-tech` / `/prepare` /
  `/decompose`, not here.

## Cross-reference

- **`/select-tech`** — executes a reopened technology choice (incumbent on the ballot).
- **`/decompose`** — executes a reopened service-boundary decision.
- **`/domain-model`** — owns the ADR log this skill reads, annotates, and supersedes into.
- **`/arch-health`** — scans code for rot; this skill scans decisions for staleness. Its
  "sanctioned exception" check is the meeting point: what it must not relitigate, this
  skill is allowed to test.
- **`/retro`** — mines what *recurred*; this skill tests what was *assumed*.
