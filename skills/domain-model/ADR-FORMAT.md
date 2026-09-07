# ADR format

**Gate:** read at `/domain-model` §Write it down inline, when a decision with real trade-offs is
about to be recorded. A run that only settles vocabulary skips this file (that one is
`CONTEXT-FORMAT.md`).

An **Architectural Decision Record** captures one hard-to-explain decision and *why* it was made,
so future readers (human or agent) don't relitigate it or quietly undo it. Write one when a
decision has real trade-offs someone will later question — not for obvious or easily-reversed
choices.

## File

`docs/adr/NNNN-<slug>.md` (zero-padded sequence, e.g. `0007-event-sourced-orders.md`), or the ADR
location named in `PROJECT.md`. One decision per file; ADRs are **append-only history** — never
rewrite a past one. To change a decision, write a *new* ADR that supersedes it.

## Structure

```markdown
# NNNN — <short decision title>

- **Status:** Proposed | Accepted | Superseded by [NNNN](NNNN-<slug>.md) | Deprecated
- **Date:** <YYYY-MM-DD>

## Context
What forces are at play — the problem, constraints, and the domain terms involved (use the
`CONTEXT.md` vocabulary). What made this a real decision rather than an obvious one.

## Decision
The choice, stated plainly and actively: "We will <do X>." One decision per ADR.

## Assumptions
The one or two ways this requirement is most likely to shift within a year, each falsifiable, and
what the shift would cost this choice — a code change, a data migration, or a different store.

## Consequences
What becomes easier, what becomes harder, and what the choice now **obliges**. Name the trade-off
accepted and the options rejected (and why) — that is what stops the decision being relitigated.
Owed work is not a drawback: a drawback you live with, an owed item is a task with an owner, and
it lands as a named plan step or an explicit deferral, never as a caveat in prose; "none" is a
valid answer. Add one line of business ground — cost, time to market, users, strategic position;
if none of the four can be written, reopen the decision rather than document it worse.

## Compliance
How this is checked — a test/lint/CI rule cited as `path::name`, a guard not yet written and filed
as a follow-up, or a review at a named cadence. Manual is acceptable, empty is not.
```

## Rules of thumb

- **One decision per record.** If you're writing "and also…", that's a second ADR.
- **Capture the *why*, not just the *what*.** The code already shows what was built; the ADR
  exists for the reasoning the code can't show.
- **Use the ubiquitous language.** ADRs and `CONTEXT.md` reinforce each other — a decision phrased
  in canonical terms is the decision a reader can actually follow.
- **Supersede, don't edit.** A reversed decision gets a new ADR whose Status links back; the old
  one stays as history with `Status: Superseded by NNNN`.
- **Status is a lifecycle**, not decoration: Proposed → Accepted, later maybe Superseded/Deprecated.
- **An unguarded decision is quietly undone.** Fill Compliance while the guard is still obvious.

## When to write one

Write an ADR when: choosing a datastore or persistence pattern; introducing or removing a major
dependency; setting a boundary/seam that other code will depend on; picking a technology or a
setting to hold up a nonfunctional characteristic (latency, durability, concurrency — "it names a
technology, so it's merely technical" is not an exemption); picking between two designs with
lasting consequences; or any decision where "why didn't they just do X?" is a question a future
reader will ask. Skip it for routine, local, easily-reversed choices — those belong in the code
and its comments, not in the decision log.
