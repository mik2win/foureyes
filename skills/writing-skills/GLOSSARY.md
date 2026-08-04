# Writing-skills glossary

**Gate:** read when the authoring question is *which kind of thing this is* — invocation class,
rule-vs-skill altitude, what "trigger" means here. Editing an existing skill's body needs
`SKILL.md` only.

The vocabulary for talking about the kit's skills precisely. Use these terms exactly when authoring
or discussing a skill — consistent language is what makes the skill set predictable to extend.

**Skill**:
A unit of reusable discipline the agent can invoke, living at `skills/<name>/SKILL.md`. Carries
*invariant logic* only — project facts come from `PROJECT.md` at runtime.
_Avoid_: command, macro, prompt (too narrow — a skill is a workflow or a reference, not a string).

**Invocation**:
How a skill is reached. **User-invoked** = the user types `/name`. **Model-invoked** = the agent may
reach for it automatically when the task fits (the user can still type it).
_Avoid_: calling, triggering (reserve "trigger" for the description field, below).

**Trigger**:
The part of a skill's `description` that tells the router *when* to use it — the situations and
phrases under TRIGGER / DO-NOT-TRIGGER. A skill's predictability lives or dies here.
_Avoid_: using "trigger" loosely to mean "invoke".

**Orchestrator**:
A (usually user-invoked) skill that drives a workflow and *delegates* to primitives — e.g.
`analyst` orchestrating `grill`. An orchestrator recommends the next user-invoked skill; it doesn't
silently chain into one.

**Primitive**:
A small, self-contained, model-invokable skill holding one reusable discipline that orchestrators
compose — `grill`, `codebase-design`, `domain-model`. Kept contract-small so any caller can drop it
in.

**Altitude**:
Whether something belongs in an always-on **rule** or an on-demand **skill**. High-altitude
invariants that must apply on every matching file = rule; workflows and heavy reference = skill.
_Avoid_: "level" (ambiguous).

**Companion file**:
A `.md` next to `SKILL.md` (e.g. `tests.md`, `ADR-FORMAT.md`) holding heavy reference the skill
links to, so the main file stays scannable. Loaded only when the skill points the reader to it.
_Avoid_: sub-skill (a companion is not separately invokable).

**Profile**:
The project's stack/commands/architecture/domain facts every skill reads in Phase 0.
Canonically `.claude/PROJECT.md` (kit-managed, written by `/bootstrap`) — kept out of the
always-on `CLAUDE.md` so the every-turn context stays lean and the detail is read on demand.
**Fallback:** the root `CLAUDE.md` is always in context; a project that keeps its facts there
instead of in `PROJECT.md` is valid — treat `CLAUDE.md` as the profile source, and only STOP
for `/bootstrap` when *neither* carries the facts. `CONTEXT.md` is the *domain* counterpart
(vocabulary), maintained by `/domain-model`.
_Avoid_: config (the profile is facts, not settings — settings live in `settings.json`).
