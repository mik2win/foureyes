# <Feature name> — Specification

- **Date:** <YYYY-MM-DD>
- **Ticket / ref:** <ID or —>
- **Status:** Draft
- **Author:** analyst skill (interview with user)

## 1. Context / Problem

**Problem.** <What pain or gap this solves, and for whom it is painful today.>

**Current state.** <How it is handled now: workaround, manual process, or not at all.>

**Value.** <What changes for the user / business if we build this.>

**Stakeholders.**

| Role | Interest / use |
| --- | --- |
| <role> | <how they use or are affected> |

## 2. Requirements

### User stories

- **US-1.** As a <role>, I want <capability>, so that <benefit>.
- **US-2.** ...

### Scope

**In scope**
- <item>

**Out of scope (for now)**
- <item>

### Behavior & rules

- <Action> — <effect, validations, side effects, async work>

## 3. Domain model

> Entities/concepts in the project's vocabulary (see PROJECT.md → Domain). Omit if purely technical.

| Entity / concept | Description | Key attributes | Relationships |
| --- | --- | --- | --- |
| <name> | <what it represents> | <attrs, required ones> | <links to other entities> |

**States & transitions** <if the entity has a lifecycle — list states and what triggers each transition; omit if none.>

## 4. Roles / authorization

> Who may do what. Use the roles from PROJECT.md → Stakeholders.

| Action | <role A> | <role B> | <role C> |
| --- | --- | --- | --- |
| view | ✓ | ✓ | |
| create | ✓ | | |

Policy / enforcement: <new vs. extend existing; per project auth rules>.

## 5. Affected areas

> Concrete places in the codebase this touches, grounded in PROJECT.md → Architecture
> and the codebase-grounding phase. Flag reuse opportunities (DRY).

| Area / layer | What changes | Reuse existing? |
| --- | --- | --- |
| <module / path / slice> | <new / modified> | <existing X / new> |

Data & integration notes: <migrations, backfills, external services, performance hotspots.>

## 6. Assumptions & open questions

**Assumptions** — what this spec takes as given; the user should validate these before
implementation (scope, data, integration behavior, reuse bets). Never silently assumed.

| # | Assumption | If wrong → impact | Confirm? |
| --- | --- | --- | --- |
| A1 | <what we are taking as given> | <what breaks / re-scopes> | user / verified |

**Open questions** — unresolved decisions that still block or shape the work.

| # | Question | Blocks | Owner |
| --- | --- | --- | --- |
| Q1 | <unresolved decision> | US-x | <user / TBD> |

## 7. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| <risk> | low / med / high | <how to mitigate> |

## 8. Acceptance criteria

> Verifiable, traceable to user stories.

- **AC-1 (US-1):** <observable, testable condition>
- **AC-2 (US-2):** ...

**Definition of done** — <overall condition for "shipped".>

## 9. Next steps

1. Resolve open questions Q1…Qn with stakeholders.
2. Run `/prepare <this-file>` for codebase-readiness analysis.
3. Implement. Suggested test scope per the project's testing rules.
