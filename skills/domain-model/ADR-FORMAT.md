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

## Consequences
What becomes easier and what becomes harder as a result. Name the trade-off you accepted and the
options you rejected (and why). This is the part that stops the decision being relitigated.
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

## When to write one

Write an ADR when: choosing a datastore or persistence pattern; introducing or removing a major
dependency; setting a boundary/seam that other code will depend on; picking between two designs
with lasting consequences; or any decision where "why didn't they just do X?" is a question a
future reader will ask. Skip it for routine, local, easily-reversed choices — those belong in the
code and its comments, not in the decision log.
