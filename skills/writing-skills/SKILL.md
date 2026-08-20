---
name: writing-skills
disable-model-invocation: true
description: >-
  Authoring reference for writing and editing the kit's own skills well — the frontmatter shape,
  description triggers, user- vs model-invoked split, the rule-vs-skill altitude call, and the
  house conventions every skill follows (Phase-0 profile load, facts-from-PROJECT.md, cross-refs,
  hard rules). A maintenance aid for developing THIS kit, not a project-runtime skill.
  TRIGGER when: someone is adding or editing a skill in this kit, asks "how should this skill be
  structured", whether something should be a rule or a skill, or how to write a good description.
  DO NOT TRIGGER during normal project work — this is for building the kit itself.
allowed-tools: Read, Grep, Glob
---

# Writing Skills (kit-internal)

A skill is a unit of reusable discipline the agent can invoke. A *good* skill is **predictable**:
its trigger is unambiguous, it carries only invariant logic, and it reads the way its siblings do.
This reference exists so new kit skills match the ones already here. It is a kit-development aid —
it does no project work itself.

When in doubt, **read a peer**: model a new pipeline skill on `analyst`/`prepare`, a quality skill
on `refactor`/`test`, a reference skill on `codebase-design`. Consistency with the existing set
beats novelty.

## Frontmatter shape

```yaml
---
name: <kebab-case, matches the directory>
disable-model-invocation: true
description: >-
  <one or two sentences: what it does + why>.
  TRIGGER when: <concrete situations and trigger phrases>.
  DO NOT TRIGGER when: <the adjacent skills it's confused with, and where to go instead>.
allowed-tools: <minimal set the skill actually uses>
effort: <low | medium | high>   # omit for pure-reference skills
---
```

Those five plus `context: fork` are the only fields the kit uses. Copy the shape, then decide each
one on purpose — inheriting a neighbour's frontmatter unexamined is how a skill ends up in the
wrong invocation class:

| Field | Required | Decide it by |
|---|---|---|
| `name` | yes | must match the directory, or the skill is unroutable |
| `description` | yes | it *is* the router — see below |
| `allowed-tools` | yes | least privilege: a read-only reviewer gets no `Edit`/`Write`; a reference skill gets `Read, Grep, Glob`. Granting more invites the skill to do more than its job |
| `disable-model-invocation` | **default `true`** (42 of 49 skills) | drop it only when the agent should be able to reach the skill *unprompted*. Omitting it is a decision, not a formality — see User-invoked vs model-invoked |
| `effort` | usually | `high` for deep design/analysis (analyst, prepare, tdd), `medium` for focused loops (spike, triage), omitted for vocabulary references (codebase-design) |
| `context: fork` | rare | run the body in a forked context to keep a long analysis out of the main thread |

- **`description` is the router.** Lead with what it does, then **TRIGGER** (phrases and
  situations) and **DO NOT TRIGGER** (the neighbours it's mistaken for, with the redirect). Vague
  descriptions cause misfires — the kit's failure mode is *under*-triggering, so be concrete.
- **`context: fork` obliges a file output.** A forked run is a **background task by default**
  (harness v2.1.218; `background: false` opts out per skill), so its reply *does* return to the
  main session — as a task-notification. That is a weaker guarantee than it sounds: a
  notification queued while the session keeps working to its end is never drained
  (`rules/_generic/delegation.md` → collect-on-notification, measured 2 of 6 delivered), and a
  fork is exactly the case where the main session has something else to do. So a fork whose only
  output is its reply can still report into a void — the reason changed, the obligation didn't.
  Give the skill `Write`, name the artifact path in the body, and end by telling the user where
  the file landed (`/audit-quality` is the model): the file is what survives a lost notification,
  and it is re-readable later, which a notification is not. A fork also runs on a reduced
  built-in toolset — a step that must call a specific tool doesn't belong behind one.
- Fields the kit deliberately does **not** use: `when_to_use` (triggers live inside `description`),
  `agent:`, `argument-hint`. Don't introduce them in one skill only.

## User-invoked vs model-invoked

Skills split on **who can invoke them** (see [GLOSSARY.md](GLOSSARY.md)):

- **User-invoked** — reached when the user types `/name`. Their job is to **orchestrate** a
  workflow (discover, analyst, prepare, arch-health, to-issues). A user-invoked skill may invoke
  model-invoked ones, but should not silently chain into another user-invoked skill — it
  *recommends* the next one and lets the user choose.
- **Model-invoked** — the agent can reach for them automatically when the task fits, *or* the user
  can type them. These hold **reusable discipline** other skills compose (grill, codebase-design,
  domain-model). Keep them self-contained so any caller can drop in.

If a skill is a primitive other skills should reuse, make it model-invokable and keep its contract
small. If it's a top-level workflow, make it user-invoked and have it *delegate* to the primitives.

## Platform caps on authoring

These are the platform's numbers, not house style, and they bound two decisions: how long a
`description` may be, and what to do when the set outgrows its listing budget. They do **not**
license a kit-wide character quota — that was proposed and rejected, because the kit's routing
failure is *under*-triggering (see `description` is the router, above). Concrete beats short;
these caps say *where* concrete stops paying.

- **Per skill: 1 536 characters** of `description` + `when_to_use` combined
  (`skillListingMaxDescChars`). Past it the description is truncated with an ellipsis — and the
  tail is where `DO NOT TRIGGER` lives, so the anti-misroute clause is the first thing lost.
- **Across the set: ~1% of the model's context window** (`skillListingBudgetFraction`, at ~4
  chars/token) — roughly **8 000 characters on a 200k model**, ~40 000 on `opus[1m]`. Over budget,
  descriptions are dropped **starting with the least-invoked skills**, so the rare ones go first —
  and, measured below, only the *project's* skills are ever dropped.
- **Measure with `/context` → Skills** (tokens and % of window), not `/doctor`: `/doctor`
  estimates from disk and points you at `/context` for the live number.

**Tripwire.** Only skills *without* `disable-model-invocation: true` claim listing space — 7 of
the kit's 49, ~7 281 characters in the kit tree, i.e. **~91% of an 8 000-character budget**.
Closest to the per-skill cap: `epic-status` at 1 450 (86 characters of headroom), then
`close-epic` at 1 327. Recount whenever you make a skill model-invocable — the next one starts
truncating the rare skills, and `close-epic` is exactly where the kit has measured misroutes.

**And the budget is shared with the built-ins — but the truncation is not.** Measured with
`/context all` in a consumer project (2026-08-04, `claude -p "/context all"` works outside the
TUI): the Skills table lists **built-in and project skills together** — ~1.8k tokens of built-ins
alongside ~2.1k of the kit's, ~3.9k total. That is comfortable on a 1m-window model (~39% of its
10k budget) and **roughly double the budget on a 200k model**, where 1% is only ~2 000 tokens.

Re-run on a genuine 200k model (same project, same day), the overflow is visible and one-sided:
the listing lands at **1.9k — the budget, exactly** — and **4 of 9 project skills collapse to
name-only** (`diagnose`, `epic-status`, `preflight`, `triage`) while **0 of 14 built-ins do**.
The untruncated project skills shrink by the same ~25% as every built-in, which is the model's own
token estimate, not truncation. So **the built-ins are effectively protected: the whole cut falls
on the project's own skills**, and "descriptions are dropped starting with the least-invoked"
describes the order *within the project's share*, not the pool. Note also that project **commands**
occupy listing slots (`commit`, `pr` appear in that table) — a new command is not free.

The practical consequence is worse than "the kit fills 91% of its budget": on a 200k consumer the
built-ins claim ~1.8k of a ~2k budget before the first kit skill is counted, so the kit is bidding
for what is left, and the rare kit skills are *already* unroutable-by-description today. Take the
live figure per project; the character arithmetic above is only a floor.

**When the listing overflows, in this order** — each step costs more than the last:

1. Shorten `description`, leading scenario first.
2. `skillOverrides: "name-only"` on skills that need not be model-reachable by description —
   they stay in the listing as a name, so nothing becomes unroutable. It accepts **built-in skill
   names too**, and that is the only per-skill way to reclaim their share; on the kit's own skills
   it merely re-spends a budget the built-ins have already claimed.
3. `disableBundledSkills` (or `CLAUDE_CODE_DISABLE_BUNDLED_SKILLS=1`) — the blunt version of
   step 2: bundled skills and workflows are removed entirely, built-in slash commands stay typable
   but are hidden from the model. Measured on the 200k run above, it took the project's share from
   ~660 tokens back to ~1 560 and **restored all four collapsed descriptions in full**. It is the
   only lever that reaches the protected half, so it is also the only one that can fix a listing
   the kit cannot fit into — at the cost of the built-ins the project actually uses.
4. `skillListingMaxDescChars`, if one specific skill is the one hitting the wall.
5. `skillListingBudgetFraction` (e.g. `0.02`) **last**: a raised budget is paid on every turn.

`SLASH_COMMAND_TOOL_CHAR_BUDGET` is not a first reach — it pins the cap in characters and cancels
the scaling with window size, which makes it a regression on `opus[1m]`. Overflow also writes a
warning to the debug log (`claude --debug -p "<prompt>"`); nothing surfaces in normal use, so the
condition is invisible unless you look.

**Load-bearing content goes at the top of the file.** Auto-compaction re-attaches only the
**first ~5 000 tokens** of each invoked skill, within a shared ~25 000-token ceiling filled from
the most recently invoked backwards (docs, 2026-08-03 — orders of magnitude, not a contract).
So gates, output format and where the skill writes belong before the phase bodies; the tail is
what gets cut. Five kit skills are already past that line — `prepare`, `close-epic`, `implement`,
`bootstrap`, `which-skill`. This is good structure regardless of compaction, and it is only half a
defence: a skill invoked *first* in a long session can be dropped entirely, which is why a long
run keeps its state in the plan artifact rather than in the skill body
(`rules/_generic/planning-artifacts.md`).

## Rule vs skill — the altitude call

The kit splits always-on context from on-demand reference (see `guide/en/reference.md` and `_kit/rules-library/PACKS.md`):

- **Rule** (`rules/**.md`) — **always-on**, lean, imperative, path-scoped. Loads in full whenever a
  matching file is read. Use for invariants that must apply *every* time (function size, boundary
  direction, the deep-module pointer). Keep it short — always-on context is precious.
- **Skill** (`skills/**/SKILL.md`) — **on-demand**. Loads only when invoked. Use for workflows and
  for **heavy reference** (worked examples, glossaries, API tours, checklists) that would bloat
  always-on context. `codebase-design`, the stack `*-reference` skills, and these companion files
  are reference-as-skill.

Rule of thumb: *"must this apply on every matching file edit?"* → rule. *"is this a workflow, or
reference you pull when relevant?"* → skill. When a rule grows heavy, split it: a one-line always-on
pointer in the rule + the bulk in an on-demand skill (that's how the deep-module line in
`code-quality.md` points to `/codebase-design`).

## House conventions every kit skill follows

- **Phase 0 — Load profile.** Read `.claude/PROJECT.md` first. If it's missing or still `TEMPLATE`,
  **fall back to the root `CLAUDE.md`** (always in context) when it carries the project's
  stack/architecture/commands, and note you're running without a kit profile; **only STOP and tell
  the user to run `/bootstrap`** when *neither* has the facts you need. (Primitives that can run
  pre-bootstrap, like `grill`, treat the profile as optional — say so explicitly.)
- **Facts from PROJECT.md, never hardcoded.** Commands, paths, layer names, frameworks, services,
  and the domain vocabulary all come from `PROJECT.md` / installed rules / `CONTEXT.md`. A skill
  that hardcodes `pytest` or `app/services` is broken for the next project.
- **Speak the project's language.** Read `CONTEXT.md` when present and use its terms.
- **Companion files** (`FOO.md` next to `SKILL.md`) hold heavy reference the skill links to, so the
  main file stays scannable. Link them with relative paths, and **open every companion with its own
  gate** — before any content, name the phase or mode that loads it *and* the condition under which
  a run skips it entirely (`skills/test/reference/async-patterns.md` is the model). Without the
  skip half, progressive loading degrades into "read everything just in case". `assets/*`
  fill-in templates are exempt.
- **Multi-site or judgment edits get a gate before the write, not only before the run.** A skill
  that applies a change across many sites, or picks between options on the user's behalf, shows the
  batch (or the winner) and waits — `/sweep` confirms the recipe then shows a pilot diff, `/distill`
  settles the winner with the user then installs. A single-target skill whose target arrived in
  `$ARGUMENTS` needs no second gate; adding one there is friction.
- **End with cross-references.** A "See also" / "Cross-reference" section pointing to the adjacent
  skills (the ones the DO-NOT-TRIGGER block names) keeps the set navigable.
- **A "Hard rules" section** (workflow skills) restates the non-negotiables so they survive a
  skim; pure-reference skills like `codebase-design` — and this file — use the closing
  checklist / See-also instead.
- **`$ARGUMENTS`** is the user's input to a user-invoked skill; handle the empty case (ask, then
  stop).

## Design against the failure catalog

Before finalizing a skill, ask **which agent failure modes this workflow invites** —
`docs/agent-failure-modes.md` is the catalog (premature closure, silent scope narrowing,
thrash, format-compliance trance, …). Build the countermeasure into the skill's *structure*
(a gate, a mandatory table row, a STOP) — never into a "be careful" sentence: structure
survives weak models and long sessions; exhortation decays. The construction techniques —
bookending, forced restatement, worked examples, checkable steps, named biases — are in
`docs/prompt-patterns.md`; kit skills are written for the **weakest model that will run
them**, not the strongest.

## Editing checklist

- [ ] `name` matches the directory; `description` has clear TRIGGER + DO-NOT-TRIGGER.
- [ ] `allowed-tools` is the minimal real set; `effort` fits (or omitted for reference).
- [ ] Phase-0 profile load + `TEMPLATE` guard (or an explicit "optional" note).
- [ ] No hardcoded commands/paths/frameworks — all via `PROJECT.md`/rules/`CONTEXT.md`.
- [ ] Cross-references resolve to skills that exist; neighbours' DO-NOT-TRIGGER blocks point back.
- [ ] If you added a skill: update the "What's in it" table **and** the Layout tree in
      `guide/en/reference.md` + `guide/ru/reference.md` **and** `/which-skill`'s catalog (parity).
- [ ] If you renamed or deleted one: `grep -rn '<old-name>'` across `skills/ agents/ rules/ docs/
      guide/ README.md settings.template.json _kit/` and fix every hit — a stale route is worse
      than a missing one, and counts in prose ("N of the kit's M skills") drift too.
- [ ] Heavy reference lives in companions, not the main file, and each companion opens with its
      gate: consumer phase/mode named + the skip condition (`assets/*` exempt).
- [ ] The workflow's likely failure modes (per `docs/agent-failure-modes.md`) have a
      *structural* countermeasure, and steps are checkable states (`docs/prompt-patterns.md`).
- [ ] Editing an `agents/*.md`, not a skill? Its `tools:` list is governed elsewhere —
      `rules/_generic/delegation.md` §Tools an agent will not get. This file covers skills only.
- [ ] `description` + `when_to_use` under **1 536** characters, and if you dropped
      `disable-model-invocation`, recount the model-invocable total against the listing budget
      (§Platform caps on authoring). Load-bearing content — gates, output format, write target —
      is above the phase bodies.

## See also

- [GLOSSARY.md](GLOSSARY.md) — the authoring vocabulary (skill, trigger, invocation, altitude).
- **`/which-skill`** — the router whose catalog you update when adding a skill.
- `guide/en/reference.md` · `_kit/rules-library/PACKS.md` — kit layout and the rule-vs-skill
  triage at the pack level.
