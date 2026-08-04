# CONTEXT.md format

**Gate:** read at `/domain-model` §Write it down inline, when a term is new or changed and
`CONTEXT.md` must be written. A run that only records a decision skips this file (that one is
`ADR-FORMAT.md`).

`CONTEXT.md` is the project's **ubiquitous-language glossary** — the single place that decodes the
project's jargon so the agent (and every developer) uses one precise term per concept. It lives at
the repo root (or the path named in `PROJECT.md` → Domain). Keep it **concise** — it's read often.

## Structure

```markdown
# <Project> — Context

A one-paragraph orientation: what this project/context is, in plain language.

## Language

**<Canonical Term>**:
<One or two sentences defining it precisely, in terms of other canonical terms.>
_Avoid_: <synonyms or near-misses this term replaces — so they don't creep back in>

**<Next Term>**:
<definition>
_Avoid_: <...>

## Relationships

- A **<Term A>** holds many **<Term B>**
- A **<Term B>** carries one **<Term C>** at a time
- <other invariants between concepts, stated in the canonical terms>

## Flagged ambiguities

- "<word>" was used to mean both X and Y — resolved: <how it was split/collapsed>.
- "<word>" — open: <still unresolved; what decision is pending>.
```

## Rules of thumb

- **One term per concept.** If two words mean the same thing, pick one and list the other under
  `_Avoid_`. Ambiguity is the enemy you're removing.
- **Define in terms of other canonical terms**, so the glossary is internally consistent and a
  reader can follow the web of meaning.
- **Concision is the payoff.** A good glossary lets "there's a problem with the materialization
  cascade" replace a paragraph of explanation. Optimize for that.
- **Record what was confusing**, not the obvious. Don't define "user" if it's never ambiguous;
  *do* define it if "user" and "account" have been used interchangeably.
- **Flag, don't bury, open ambiguities.** When a term isn't settled yet, list it under "Flagged
  ambiguities" so the next session knows it's live — resolve it via `/grill` or `/domain-model`.
- **Multiple contexts:** when the project splits into bounded contexts, each gets its own
  `CONTEXT.md`, and a root `CONTEXT-MAP.md` lists where each lives and the system-wide terms.

## Example

```markdown
## Language

**Issue tracker**:
The tool that hosts a repo's issues — GitHub Issues, Linear, or a local `.scratch/` markdown
convention. Skills like to-issues, to-prd, and triage read from and write to it.
_Avoid_: backlog manager, backlog backend, issue host

**Issue**:
A single tracked unit of work inside an Issue tracker — a bug, task, PRD, or vertical slice.
_Avoid_: ticket (only when quoting external systems that call them tickets)
```
