# Prompt patterns — design for the weakest executor

Skills, agent briefs, and prompt packs outlive the model that wrote them: tomorrow they run on Opus, Sonnet, or smaller. These patterns make instructions that *degrade gracefully* — the strongest model isn't hindered, the weakest is held up. Each pattern names the mechanism it compensates for (cross-refs: `docs/agent-failure-modes.md`).

Audience: `/writing-skills` (authoring kit skills), `/prompt-master` (compiling packs for other models), `delegation.md` (agent briefs), and anyone writing prompts that must be executed reliably rather than admired.

## 1. Externalize memory — never rely on attention

A capable model holds constraints in its head; a weaker one loses the middle (failure mode #8) and lets instructions decay (#5). So put working state **outside the head**:

- Checklists and tables the executor must *fill*, not just read — an empty cell is a visible omission; a forgotten instruction is invisible.
- Forced restatement: "quote the step verbatim before implementing it" (as `/implement` does) makes each item its own fresh context.
- One decision per step. A step containing two decisions will, on a weak model, get one.

## 2. Bookend the critical (the attention U-shape)

Attention over a long prompt peaks at the start and the end. The kit's skill shape is this pattern: **Phase 0 first** (load the profile, STOP conditions), **Hard rules last** (the non-negotiables restated where the second attention peak lands). When editing a skill, preserve the bookends — a critical constraint added mid-file is planted in the attention valley.

## 3. One worked example beats three paragraphs

An example is executable specification: a GOOD/BAD pair pins the interpretation that prose leaves open, and weaker models copy structure far more reliably than they follow descriptions. Where behavior matters, show it (`/sweep`'s FROM→TO pair, `/prepare`'s vague-vs-specific table, the spec template's concrete AC examples). Choose examples with **diverse edge cases** — the executor generalizes from the span of examples, not from the adjectives around them.

## 4. Positive instruction + targeted prohibition

Say what TO do as the main line — "write X to location Y in format Z" executes better than "don't put X in the wrong place". Reserve DO-NOTs for **predicted failure modes**, stated concretely (the do-not list in `delegation.md` briefs, the DO NOT sections closing kit skills). A prohibition without a predicted failure behind it is noise that dilutes the prohibitions that matter.

## 5. Structure output to force the thinking

A mandatory output section is a checkpoint the executor cannot skip silently: the Deviation Report's mandatory no-deviation row, the gate tables, "Searched but absent". If you need a check to *happen*, give its result a required slot — and demand evidence in the slot (`path:line`, counts, verbatim output), because slots invite padding (failure mode #13). Allow honest "n/a — <reason>" so the template never forces fabrication.

## 6. Fresh context gets a total brief

Subagents and next-session executors share nothing with you (failure mode #6 is the flip side: sharing *everything* poisons). No "as discussed", no pronouns pointing outside the text; file paths over descriptions; every needed fact in the brief or in a file the brief names. The five-part brief in `delegation.md` is this pattern's checklist; the Artifact-Continuity Contract is it applied to plans.

## 7. Name the executor's bias to its face

Telling the executor its predicted failure — "You have a bias to close the task; that is why a separate auditor runs" (`/implement`), "Your job is to KILL this finding" (`finding-verifier`) — measurably counteracts the bias. State it as a fact about the role, not an insult; pair it with the structural counter (the audit, the default-REFUTED).

## 8. STOP gates interrupt momentum

Weak models comply with momentum: once moving, they keep moving past the point where they should have asked. Place explicit STOPs where continuing wrongly is expensive: STOP-if- TEMPLATE, confirm-before-creating-files, STOP-and-ask before skipping a plan step. A STOP is a *structural* pause — "be careful here" is not (exhortation decays; structure survives).

## 9. Write steps as checkable states, not actions

"Ensure `<key>` is set in `<config>`" can be verified and is idempotent under re-execution (a re-run after compaction or a retry re-does it harmlessly); "add `<key>`" executed twice is a bug. Prefer state-shaped steps with a `Verify:` line — the step then carries its own done-test, and any-strength executor can tell whether it's finished (failure mode #1).

## 10. Tier the effort explicitly

Without instruction, an executor over-processes trivial input and under-processes hard input. Say which: "skip this phase entirely when …", complexity tiers that gate decomposition (`/prepare` Phase 3), `effort:` frontmatter. Every "skip if" you write is context reclaimed for the case that needs it.

## 11. Test prompts like code

A skill or prompt pack is software. Before trusting it: run it on one known scenario and compare the output *shape* to expectation (did the gates fire? did the tables fill with evidence?); when it misfires, fix the prompt's structure — add the slot, the STOP, the example — rather than appending another adjective to the instructions. Iterate descriptions from real trigger misses (`/writing-skills`' editing checklist), and let `/retro` catch what slips through in production.

## 12. Sequence output: evidence slots before verdict slots

A template that asks for the verdict first gets an analysis written to justify it — generation conditions on its own output, so the first committed sentence anchors everything after (failure mode #15). Order mandatory sections so evidence is produced before the conclusion is stated: observations → diagnosis, findings → severity, gate rows → GO/NO-GO. This governs *derivation* order inside the working artifact; the reader-facing summary still leads with the outcome (`core.md`) — the executor writes the conclusion last and places it first. When editing a template, moving the verdict slot above the evidence slots is a regression even though "nothing was removed".

---

**The meta-rule:** when an executor fails your prompt, the cheap diagnosis is "weak model"; the useful one is "which mechanism above did my prompt rely on that wasn't there?" Almost every reliable-prompt trick is one of two moves — **move state out of attention into structure** (1, 2, 5, 6, 9, 12) or **make the failure mode a first-class citizen of the prompt** (4, 7, 8, 10). Strong models make weak prompts look good; you find out which you wrote when the model changes.
