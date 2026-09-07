# Interview Question Bank

**Gate:** read at `/analyst` Phase 2 (business interview) and Phase 4 (technical interview) when
the ~4–8 questions need more than the prompts in `SKILL.md`. A run whose answers are already in a
`/discover` brief skips this file.

Use as a checklist, not a script. Ask one question at a time, adapt to answers, skip what
is already clear. Phrase questions in the user's language. Frame every question in the
project's domain vocabulary and roles (from `PROJECT.md` → Domain) — never invent terms.

## Part A — Business analyst (both paths)

### Problem & value
- What concrete problem or pain does this solve? For whom is it painful today?
- How is it handled now — workaround, manual process, or not at all?
- What happens if we do NOT build this? Is the current state acceptable?
- What does success look like — what changes for the user or the business?

### Users & stakeholders
- Who are the primary users? (use the roles listed in `PROJECT.md`)
- Who else is affected but does not use it directly?
- Do different roles need different capabilities or views?

### Scope
- What is the minimal first version that is still useful?
- What is explicitly OUT of scope for now?
- Is there a phased rollout — what ships first, what comes later?

### Scale & horizon
- How many users, records or requests today — a number, not "a lot"?
- What do you expect at three months, six months, a year?
- Which of those numbers would change what we build if it were ten times larger?

### Acceptance & constraints
- How will we verify it works? What are the acceptance criteria?
- What is the definition of done?
- Is there a deadline or a dependency on other work (e.g. a ticket)?
- Is now the right time, or is something else higher priority?

## Part B1 — Domain / feature-design path

### Concept framing
- Which domain concept(s) does this introduce or change? How does it relate to the
  existing core concepts in `PROJECT.md`?
- What makes this different from what already exists?
- What rules or invariants must always hold for this concept?

### Workflow
- Walk me through the user's flow step by step (happy path).
- What triggers the flow — a user action, a schedule, an external event?
- Where can it go wrong? What are the error/edge paths?

## Part B2 — Code / technical-feature path

### Framing
- What problem does this feature solve, and who is the primary user?
- What is the current workaround, if any?

### If the ask is "make X automatic" or "self-correcting"
- Is each step a decision followed by an action, or is it retrieval that only looks like one?
- What in the environment answers back after each step, and can the loop act on that answer?

### Workflow & I/O
- What triggers use of this feature? Expected input format?
- What output should the user see? How often is it used?

### Integration
- Which existing modules/layers does this touch (per `PROJECT.md` → Architecture)?
- Any new dependencies? Breaking changes to existing behavior?

### Operations
- Logging, monitoring, configuration, deployment considerations?

## Part C — System analyst (both paths)

### Domain walk (unfamiliar domain)
- What has already happened — name the events in past tense along a timeline; collect too many,
  and mark the ones that run in parallel.
- What command causes each event, and who issues it? Only then: what entity does it act on?
- Skip the walk for a plain linear sequence with no interesting rules. Record missing domain
  knowledge the moment it surfaces, at whatever step.

### Domain model
- What new entities/concepts are needed? What does each represent?
- Key attributes per entity — which are required?
- Relationships to existing entities?
- Scoping/isolation needs (tenancy, ownership)?
- Does it need a status/lifecycle field?

### States & transitions
- Does the entity have a lifecycle? List the states.
- Who/what triggers each transition? Any guards?

### Behavior & rules
- What actions/operations are performed — in your words, not create/update/delete?
- Validations — what must always be true?
- Side effects — emails, background jobs, events, webhooks, audit logs?
- Anything needing a transaction or a dedicated service/unit per the architecture?

### Authorization
- Which roles can perform which actions? (build a role × action matrix)
- New enforcement needed, or extend an existing one?
- Different permitted fields or visible records per role?

### Interface / entry points
- What screens, routes, commands, or APIs are needed?
- Forms — fields and validation? Lists — pagination, filters, sorting?
- Where do these live per the project's structure model?

### Data & integration
- Migrations — new tables/columns? Backfill for existing records?
- External integrations or APIs (from `PROJECT.md` → Integrations)?
- For each external system: real-time or batch, is there a cut-off, and how long from "we sent
  it" to "the result is final"? Batch or next-day makes a synchronous call a defect — ask for the
  intermediate state and what the user sees while it is pending.
- Performance hotspots — N+1 risk, heavy queries, large payloads?

### Edge cases & non-functionals
- Empty states, very large datasets, concurrent edits?
- What breaks if this feature fails? Failure modes?
- Idempotency and retry behavior for async work?
- A slogan ("five nines", "instant", "zero downtime") gets restated as a quantity before you
  agree or object — then ask which part of the system actually needs it.
- In production, how many callers against how many providers, and what limit does the far side
  hold?

## Clarification patterns

- "Can you give me a specific example?"
- "What would that look like in practice?"
- "Is this similar to how <existing feature> works?"
- "What should happen if <edge case>?"

## Skip patterns

Skip a question when: already answered, not applicable to this path, or the user says
it is not relevant.

## Reflection pattern

After ~3–5 questions, summarize:
> "Let me make sure I understand: you want <summary>. Is that correct?"

This catches misunderstandings early.
