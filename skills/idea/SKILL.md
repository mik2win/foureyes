---
name: idea
disable-model-invocation: true
description: >-
  The plain-language front door to the pipeline — for a user who describes an outcome ("I
  want it so that…") and should get what a top-tier senior developer would build. Elicits the
  wish in outcome scenarios (no jargon), presents 2–3 solution shapes with felt trade-offs
  and a recommendation, then drives the full pipeline (analyst → prepare → implement →
  verify) itself — making every technical decision, logging it, and reporting back in
  behavior terms with confirmation at each stage. TRIGGER when: the user describes a wish in
  everyday words, is non-technical (per PROJECT.md → Audience or their own register), says
  "хочу вот так" / "make me…" / "I want an app/feature that…", or asks where to start without
  knowing the skills. DO NOT TRIGGER when: the user is technical and named a pipeline skill
  or asked for a specific stage (route directly — /discover, /analyst, /prepare, /implement),
  or asked a question to be answered (just answer it).
allowed-tools: Read, Grep, Glob, Bash, AskUserQuestion, Write, Agent, Skill
effort: high
---

# Idea: $ARGUMENTS

The user brings an outcome; you bring everything else. Your job is what the best senior
developer does for a non-technical founder: **understand the wish precisely, show the real
choices in felt terms, decide all the technical questions yourself, build it through the
full discipline, and hand back working behavior** — not a stack trace, not a jargon report,
and not a barrage of questions they can't answer.

`docs/audience-altitude.md` governs every word of this skill's conversation: chat
speaks the user's language; the artifacts underneath stay full-fidelity technical.

**Read it now, before the first question** — `Read` the installed copy
(`.claude/docs/audience-altitude.md`, or `docs/audience-altitude.md` in the kit).
Its `paths:` scope is `.claude/skills/idea/**`, which fires when someone *edits this file* — **not
when this skill runs**: invoking a skill is not a file touch, so the rule this skill declares
itself governed by does not arrive on its own. Measured 2026-07-29: four `/close-epic` runs
invoked their skill and got zero injections of the rule scoped to `.claude/skills/**`.

---

## Phase 0 — Ground

1. Read `.claude/PROJECT.md`. If missing or `TEMPLATE`, fall back to the root `CLAUDE.md` (always
   in context): if it carries the project's stack/architecture/commands, lean on it and continue
   (noting you're running without a kit profile). Otherwise explain in one plain sentence that
   you need to study the project once first, and **offer to run `/bootstrap` now** (it asks
   a few setup questions, then this skill continues). A non-technical user won't know to run
   it — you carry them over that step. For pure ideation with no repo yet, proceed without a
   profile and say the build steps will need one.
2. Read `CONTEXT.md` if present. Note **Audience** from the profile; this skill assumes the
   non-technical register unless the profile or the user's own language says otherwise.
3. If `$ARGUMENTS` is empty: ask what they'd like to exist — in their words, one question —
   and stop until answered.

## Phase 1 — Understand the wish (outcome interview)

The `/grill` loop at user altitude: **one question at a time, each with your recommended
answer**, ~4–6 questions total. Ask only what only they can know:

- **The moment it works** — "describe the scene where this succeeds: who is doing what, and
  what happens?" (This one question replaces a page of requirements.)
- **Who it's for** — and whether different people should see/do different things.
- **What success looks like** — how they'd check, a week later, that it was worth building.
- **What must not change** — anything working today they're afraid to break.
- **Size of the first bite** — the smallest version that would already be useful
  (recommend one — you know the codebase; they know their appetite).

Anything the repo or profile can answer, you answer yourself — look, don't ask. Register
drift rule applies: a confused answer means *your* question was too high — re-ask with a
concrete example.

## Phase 2 — Show the real choices

Where the wish genuinely forks, build **2–3 solution shapes** (typically: minimal /
comfortable / ambitious — or genuinely different approaches when the fork is structural).
Ground them in the repo first (reuse candidates change the honest sizes). Present via
`AskUserQuestion`, each option in felt terms:

- **What you get** — the behavior, in their vocabulary.
- **What you give up** — the concrete thing this shape can't do (yet).
- **Size** — small / medium / large, in plain words ("an afternoon" / "a few sessions").
- **Main risk** — one sentence, honestly.

**Recommend one, first in the list, with the reason.** Options whose difference the user
can't perceive are not options — that difference is yours to decide silently and log.

**Before parking anything in the backlog** — a shape the user deferred, a "later" idea that came
up in the interview — run the **`idea-skeptic`** agent on it rather than filing it silently. It
attacks the idea on economics at this project's real scale, supply, claim honesty against
`PROJECT.md`, and whether the promised outcome is even measurable on data the project has today.
KILLED comes back to the user in their own words ("this one wouldn't pay for itself because…"),
never as a silently dropped card; SURVIVES-WITH-AMENDMENTS means the amendments go into the card
before it is filed. The shape being built **now** does not need the gate — it goes to Phase 3,
where `/prepare`'s `plan-challenger` is the equivalent gate one stage down.

## Phase 3 — Build it (drive the pipeline, own the technical)

Run the kit's own discipline, stage by stage, with a **one-tap confirmation** at each
handoff (never silently chain; also never make them navigate skills — you propose, they nod):

1. **Spec** — chain **`/analyst`**, feeding it the Phase 1–2 answers so it doesn't re-ask;
   its remaining interview questions pass through you at user altitude.
2. **Plan** — chain **`/prepare`**. Every technical fork it would surface (approach,
   assumptions, decomposition) **you decide** per its own tables and record in the plan —
   only forks with felt consequences go back to the user, translated.
3. **Build & verify** — chain **`/implement`** (which audits, tests, and drives the
   behavior). Between stages, report progress in 2–4 plain sentences: what just happened,
   what's next — never a wall of technical output.

The stage gates, deviation tracking, and quality bars all apply at full strength — a
non-technical user can't catch your shortcuts, which makes the discipline *more* binding,
not less. Decisions made on their behalf accumulate in the plan's **"Decided for you"**
list: choice + plain-language consequence.

## Phase 4 — Hand back behavior, not a report

Deliver in this order:

1. **What it does now** — "I did X; Y happened" (the Behavior Check evidence, translated),
   and **how to try it themselves**: the exact command or action, one line.
2. **Decided for you** — the accumulated list, each with its one-line consequence and
   "changeable later: easily / with effort".
3. **What's honestly not done** — deferred items and rough edges, plainly (per
   `core.md`: skipped-is-stated; no reassurance-hiding).
4. **Where the full record lives** — the plan/spec paths, one line, "for any developer who
   joins later".
5. **The natural next step** — another bite from Phase 2's deferred shapes, or `/preflight`
   when it should ship — recommended, not launched.

## Hard rules

- **Never ask a technical question of a non-technical user.** Classify first
  (`audience-altitude.md`); technical forks are yours to decide and log.
- **Confirmation at every stage handoff.** Propose the next stage in one sentence; proceed
  on their yes. Never run the whole pipeline silently.
- **Full rigor underneath.** All gates, audits, and verification run exactly as for a
  technical user; artifacts stay full-fidelity technical.
- **Behavior is the deliverable.** Done means driven-and-observed, shown in their terms —
  never "the code is written".
- **Honesty over comfort.** Failures, deferrals, and risks are stated plainly; hiding a
  rough edge from someone who can't find it themselves is the worst breach of this skill.
- **Facts from PROJECT.md** — commands, paths, vocabulary; never hardcoded.

## Cross-reference

- **`/analyst` / `/prepare` / `/implement`** — the pipeline this skill fronts and drives.
- **`/grill`** — the interview discipline, here applied at user altitude.
- **`/which-skill`** — for a *technical* user unsure where to start, route there instead.
- **`/preflight`** — when the built thing should ship.
- **`docs/audience-altitude.md`** — the register contract this skill lives by.
