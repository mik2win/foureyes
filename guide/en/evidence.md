[← README](../../README.md) · **English** · [Русский](../ru/evidence.md)

# What was measured — including the results that argue against the kit

Most kits ship claims. This one was put on a blind A/B bench first: two arms of the same real repository differing by exactly one thing, a sealed mixing map, a 5-axis rubric (correctness · edge/unhappy-path · verification · report honesty · process fit), and a written noise-limits section. Four rounds. Everything it returned is below, negatives included.

| Question the bench was asked | What came back |
|---|---|
| Do the generic rules beat no rules at all? | **Yes, weakly.** Round 1, 16 runs: the arm *with* rules wins 2 of 4 task types, ties 2, loses 0 — mean Δ ≈ +0.5 on the rubric, cleanest on implementation and planning. It also burned **1.3–2× the tokens.** |
| Does the always-on rule tier make output *better*? | **No — three rounds running, no measurable quality gain.** It is reliably *cheaper* (0.82× and 0.93× tokens on two slots). The honest sentence is *"the same result for less money"*, not *"it works better"*. This result is why the always-on tier was cut from 13 rules to 4. |
| Do skills fire by themselves when a prompt matches one? | **No. Zero invocations across all 16 runs.** ~10k of always-on skill descriptions never matched anything. That is the finding behind [manual-by-default and its three escape hatches](#skills-are-manual-by-default--and-the-three-escape-hatches). |
| Does *this particular rule* pay for its context? | **The bench cannot answer that** — isolating one rule and keeping a run valid turned out to be mutually exclusive conditions. Saying so was more useful than a number; the candidate queue was closed with transcript counters instead. |

**Limits, stated plainly.** One production Python repo plus neutral arms, n=2 per cell, and the judge is a model. The stack packs (ruby / rails / react-ts / postgres) were never in an arm — they are contributed templates, not measured ones. Read the table as directional, not as a benchmark.

The reason to publish the negatives is that they are the expensive part. Anyone can write a rule file; knowing that a tier of them buys cost and not quality took four rounds and ~40 judged sessions, and it changed the kit's shape.

## Skills are manual by default — and the three escape hatches

**41 of the kit's 49 skills carry `disable-model-invocation: true`.** They run when *you* type `/prepare`, and never because the model decided a prompt looked like planning. That is the deliberate default, and it is worth being explicit about both sides of it.

**What it buys.** No surprise activation. A skill is a long, opinionated procedure — `/close-epic` alone spawns verifier agents, runs a battery, and edits two files. Auto-firing one on a half-formed request costs a rewind, not a turn, and the *silent* variant is worse: work done under a procedure you never chose and can't see in the transcript. Manual invocation also keeps the skill index out of the model's decision loop on every prompt.

**What it costs, measured.** A concrete task request with a perfect skill match **silently runs bare**. Three sessions asked "check if epic is done? `backlog/<name>`, run the verification steps from the overview" and reconstructed `/close-epic`'s checklist by hand: 70–92 Bash calls each, **zero** verifier agents spawned, the plan-status tool never run, and one session executed a `git mv` the skill's DO-NOT list forbids. The output was still good — the loss is the verification that never happened and roughly a quarter of each session spent rediscovering facts the skill already knows.

The escape hatches exist because that failure is invisible from inside: nothing tells you a skill *would* have fired. There are three, in increasing order of how much they change:

| # | Hatch | What it does | Cost |
|---|-------|--------------|------|
| 1 | **Eight skills stay invocable** | the terminal/verification five — `/close-epic`, `/epic-status`, `/diagnose`, `/triage`, `/preflight` — plus `/which-skill` (the router), `/bootstrap` (the installer) and `/grill`. Each of the five carries a task-shaped `TRIGGER ALSO` line written in the phrasing that actually failed above. Three of them write *files* (a ledger row, a `status:`, a report) but none touches code or git | the narrowest class where the miss hurt; no config |
| 1a | **`/grill` is invocable for a second reason** | it is the kit's shared alignment primitive, and a dozen skills instruct the model to *run* it — `/arch-health` "then `/grill` the opportunity", `/prototype` "`/grill` them on what they're seeing", `/decompose` "`/grill` it: the exact interface at the seam". A skill carrying `disable-model-invocation` cannot be reached through the `Skill` tool at all, so every one of those lines was a dead end and the calling skill silently improvised an interview instead of running the contract | 779 chars of always-on listing budget, and a long interview can now fire on "what am I missing" — its `DO NOT TRIGGER` line is the only guard |
| 2 | **`/which-skill`'s silent match** | the router also fires on a concrete task that matches an installed skill's domain *without* naming it. One obvious match → one line naming the skill, then it runs (on your yes, or when the task is plainly that skill's own job); two candidates → one `AskUserQuestion`; no match → it says nothing about routing and the work happens bare | a router that answers loudly on every task would just add a turn; the brevity rule is what makes this affordable |
| 3 | **`hooks/skill-hint.sh`** — opt-in, **OFF by default** | a `UserPromptSubmit` hook that scores the prompt against every installed skill's frontmatter and injects the top 1–2 names as advisory context. It never blocks, never rewrites the prompt, and stays silent when nothing scores or when the prompt already names a skill. ~29 ms/prompt, measured at 46 skills | not wired by the kit — merge the `UserPromptSubmit` block from `settings.skill-hint.example.json` into `.claude/settings.json` (or accept `/bootstrap`'s offer). `SKILL_HINT_DISABLE=1` turns it off without unwiring. **Matching is English-token based**, so a non-English prompt scores 0 and the hook stays silent — a missed hint, never a wrong one |

A hint is not an invocation: hatches 2 and 3 put the skill's *name* in front of the session and stop there. The decision to run it stays yours, which is the property manual-by-default was protecting in the first place.

**A fourth failure, and none of the three hatches reaches it: the command was typed and did not expand.** All three above answer *"the user never named the skill."* This one is the opposite — the user named it, and the harness still ran bare. Claude Code expands a slash command only when the message **starts** with it, so anything riding above the command turns the invocation into ordinary text: a `>`-quoted hand-off copied along with the block, a heading pasted with it, a note above a fenced prompt. Nothing errors. The skill does not load, no `<command-name>` block reaches the model, and the session executes a lookalike procedure while both sides believe the contract is running.

Measured once, and expensively (`chart-ux-audit-2`, 2026-08-11): an implementation prompt was copied together with the note above it, `/implement` landed at character 30, and the run lost the skill's mandatory architecture-audit phase and its report contract. The audit — spawned only after the operator asked where it was — returned **nine findings, two of them blocking regressions** in code that had already passed every acceptance check the session wrote for itself. Against 487 slash commands that expanded correctly in the same archive, so it is rare; but it is silent, and the cost is a whole quality gate.

Two defences, and the kit wants both, because each covers what the other misses:

- **Authoring** — in a copy-paste prompt pack, the slash command is the **first line inside the fenced block**, and headings, hand-offs and notes stay **outside** it. What the operator copies then starts with the command by construction. (One epic's pack carried a note above **22 of its 32** blocks — the trap was structural, not a slip.)
- **Behavioural** — an always-on rule telling the agent that a `/skill` present in the message with no `<command-name>` block **did not load**: say which command failed to expand and let the operator re-send it, never substitute an improvised equivalent. This is the only half that fires when the authoring rule was not followed, which is exactly when it is needed.
