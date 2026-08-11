# Prompt pack — <title>

> Two shapes: the **chained pack** below (archetypes 1–6 — one prompt per phase, one
> session each), and the **program pack** at the bottom (archetype 7 — one orchestrator
> prompt that fans out). Use one or the other, not both.

> Generated: <YYYY-MM-DD> · Archetype: <feature | refactor | bug | research | architecture | greenfield | program>
> Mode: <kit | standalone> · Target: <Claude Code + kit / plain Claude Code / claude.ai / API>
> Source idea: <one-sentence restatement of $ARGUMENTS>

## How to run this pack

1. **Fresh session per prompt.** Paste one prompt, let it finish, review its artifact —
   then start a new session for the next prompt. Do not run two prompts in one session.
2. **You are the gate.** Each prompt ends with a stop condition and open questions; answer
   them / check the artifact before firing the next prompt. The "Gate" column below says
   what to check.
3. **Artifacts are the memory.** Prompts reference each other only through the files in
   the Artifact column. If you rename/move one, update the later prompts.
4. If a phase goes sideways, re-run that prompt in a fresh session (optionally pasting
   what went wrong) — don't patch it mid-session across phases.
5. **Copy the fenced block only, and let a slash command be the first thing in the
   message.** The heading above a prompt, and any note between it and the fence, are for
   your eyes — pasted along with the prompt they push `/prepare` or `/implement` off the
   start of the message, and the harness expands a slash command only from there. The
   failure is silent: the skill never loads, nothing errors, and the session runs a
   lookalike procedure. If you are unsure whether it expanded, ask — the session is
   required to tell you when a named command did not (`rules/_generic/core.md` § Done).

## Pipeline overview

| # | Phase | Artifact it produces | Gate before the next prompt |
|---|-------|----------------------|------------------------------|
| 1 | <phase> | `<path>` | <what the user checks/answers> |
| 2 | … | … | … |

<!-- Folded phases: note here which standard phases were merged and into which prompt. -->

## Open questions carried by this pack

- O-1 — <question a prompt defers to the user, and which prompt needs the answer>

---

## Prompt 1 — <phase name>

```markdown
<the full self-contained prompt: Role & mission · Context (read-first artifacts) · Task ·
Method · Guardrails · Output contract · Stop condition>
```

**Gate before Prompt 2:** <what to verify in the artifact / which O-n to answer>

---

## Prompt 2 — <phase name>

```markdown
…
```

**Gate before Prompt 3:** …

---

# Variant — program pack (archetype 7)

Replaces everything above when the input is a whole surface. One prompt, run by an
orchestrator that fans out per phase; the operator's gate is at the end, when they select
cards. Worked example: `references/program-pass-example.md`.

## Before you run it

```text
Goal:      <the question the whole pass answers, in the user's terms>
Executor:  a fresh session at the repo root, model <name>, effort high
Scope:     <what it audits · source is not modified · nothing is committed>
Scale:     ~<N>–<M> subagents, ~<T> tokens
Prep:      <the one command that refreshes the target's data, if any>
```

## Phases

| Phase | What | Artifact |
|-------|------|----------|
| P0 | Bootstrap: stand the target up, smoke it, pick the instances | running stand + work-list |
| P1 | Breadth sweep of every surface and state | `evidence/P1-*.md` |
| … | … | … |
| P6 | Synthesis: ranked report + cards + RUN-ORDER | `<program>/` |

## The orchestrator prompt

```markdown
<Role & mission · Ground facts (cited, dated, with the settled-decisions list) ·
Evidence-file convention · Method as ~6 phases · Guardrails (read-only · evidence
append-only · no binaries · never git) · Stop condition>
```

## Output contract

```text
<program>/00-report.md        ranked findings, each linked to its evidence file
<program>/evidence/<phase>-<slug>.md   one per agent, append-only once written
<program>/cards/NN-<slug>.md  one scoped unit of work each; the /prepare input
<program>/RUN-ORDER.md        the execution spine, when the cards have one
```

**After the pass:** select the cards worth doing → `/prepare <program>/cards/NN-<slug>.md`
for each. Nothing gets implemented from the report itself.

<!-- If a Workflow script was emitted for this pass, name it here and say that running it
     is the user's call — this pack never invokes it. -->
