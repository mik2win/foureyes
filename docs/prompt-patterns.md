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

An example is executable specification: a GOOD/BAD pair pins the interpretation that prose leaves open, and weaker models copy structure far more reliably than they follow descriptions. Where behavior matters, show it (`/sweep`'s FROM→TO pair, `/prepare`'s vague-vs-specific table, the spec template's concrete AC examples). Choose a few **diverse, canonical** examples of the behaviour you want rather than an enumeration of every edge case — a laundry list of exceptions makes the prompt longer and the behaviour less clear, and the executor generalizes from the span of examples, not from the adjectives around them.

Two properties of the set are themselves instructions. **Order:** normal cases first and errors last teaches "things start fine and then go wrong", and that is the order a systematic sweep produces by default — shuffle unless the sequence is the lesson. **Proportion:** one example per class says the classes are equally likely, so on ambiguous input the executor drifts to the middle; either match the real rate or state it in words beside the examples, because a balanced GOOD/BAD pair reads as 50/50.

## 4. Positive instruction + targeted prohibition

Say what TO do as the main line — "write X to location Y in format Z" executes better than "don't put X in the wrong place". Reserve DO-NOTs for **predicted failure modes**, stated concretely (the do-not list in `delegation.md` briefs, the DO NOT sections closing kit skills). A prohibition without a predicted failure behind it is noise that dilutes the prohibitions that matter.

Two measured refinements, both counter-intuitive enough to be worth stating (`obra/superpowers`, micro-tests on their own skills). On **shaping** failures — where the output has the wrong flavour rather than the wrong facts — a bare "don't X" produced *more* of the unwanted content than a positive recipe, and more than no guidance at all: naming the thing summons it. And one hedge bolted onto a recipe that was winning — "unless it matters", "use judgment here" — degraded it back to baseline, because a nuance clause re-opens the decision the recipe had closed. So: recipe first; prohibition only where you have *seen* the failure; no softening clause on a line that already works.

Treat both as hypotheses about your prompt, not as facts about models — and settle them the same way they were settled: a **control arm with no guidance at all** (if the control doesn't fail, there is nothing to fix and the guidance should be deleted), 5+ runs per variant, every hit read by hand rather than grepped, and **answer variance scored as its own metric** — five runs that read a line five ways mean it doesn't bind, however many of them pass. The full protocol is in `/writing-skills` §Micro-test a wording; it needs no test harness, only raw calls.

## 5. Structure output to force the thinking

A mandatory output section is a checkpoint the executor cannot skip silently: the Deviation Report's mandatory no-deviation row, the gate tables, "Searched but absent". If you need a check to *happen*, give its result a required slot — and demand evidence in the slot (`path:line`, counts, verbatim output), because slots invite padding (failure mode #13). Allow honest "n/a — <reason>" so the template never forces fabrication.

A verdict slot names its levels **in words**, not as labels: each level says what has to be true to earn it (`quality-auditor`'s three, `plan-verifier`'s five), because a bare CRITICAL / STRUCTURAL / STYLE list floats between runs — two instances of the same reviewer then return incomparable verdicts, and the aggregator reads a difference in bar as a finding about the code. Name the aspects being judged too (intent vs execution at the minimum), and split any "was it just right?" into "was it enough?" and "was it too much?", which are answerable separately.

## 6. Fresh context gets a total brief

Subagents and next-session executors share nothing with you (failure mode #6 is the flip side: sharing *everything* poisons). No "as discussed", no pronouns pointing outside the text; file paths over descriptions; every needed fact in the brief or in a file the brief names. The five-part brief in `delegation.md` is this pattern's checklist; the Artifact-Continuity Contract is it applied to plans.

Assume every snippet you include will be **used**, not merely available: an irrelevant one is not ignored, it is read as significant and produces a confident wrong decision rather than noise. Before adding a file, a log, or an earlier artifact to a brief, say in one line which decision in *this* phase it is meant to change; if you cannot, drop it. When the context genuinely is optional, give it its own frame — "prior art, for comparison, not necessarily relevant" — so it can be consulted without demanding to be used; unframed background is read as a requirement.

## 7. Name the executor's bias to its face

Telling the executor its predicted failure — "You have a bias to close the task; that is why a separate auditor runs" (`/implement`), "Your job is to KILL this finding" (`finding-verifier`) — measurably counteracts the bias. State it as a fact about the role, not an insult; pair it with the structural counter (the audit, the default-REFUTED).

## 8. STOP gates interrupt momentum

Weak models comply with momentum: once moving, they keep moving past the point where they should have asked. Place explicit STOPs where continuing wrongly is expensive: STOP-if- TEMPLATE, confirm-before-creating-files, STOP-and-ask before skipping a plan step. A STOP is a *structural* pause — "be careful here" is not (exhortation decays; structure survives).

A STOP is structure only where something outside the model can enforce it. A prompt-level prohibition on a destructive action leaks a fraction of the time by construction — the sentence competes with everything else in the context, and some share of runs does exactly the forbidden thing. Treat such a line as a *reminder* and name the structural gate that actually holds: a hook, a permission denial, a write scope narrowed to one directory, a human confirmation. Where no structural gate exists, write that down in the plan instead of trusting the sentence.

## 9. Write steps as checkable states, not actions

"Ensure `<key>` is set in `<config>`" can be verified and is idempotent under re-execution (a re-run after compaction or a retry re-does it harmlessly); "add `<key>`" executed twice is a bug. Prefer state-shaped steps with a `Verify:` line — the step then carries its own done-test, and any-strength executor can tell whether it's finished (failure mode #1).

## 10. Tier the effort explicitly

Without instruction, an executor over-processes trivial input and under-processes hard input. Say which: "skip this phase entirely when …", complexity tiers that gate decomposition (`/prepare` Phase 3), `effort:` frontmatter. Every "skip if" you write is context reclaimed for the case that needs it.

## 11. Test prompts like code

A skill or prompt pack is software. Before trusting it: run it on one known scenario and compare the output *shape* to expectation (did the gates fire? did the tables fill with evidence?); when it misfires, fix the prompt's structure — add the slot, the STOP, the example — rather than appending another adjective to the instructions. Iterate descriptions from real trigger misses (`/writing-skills`' editing checklist), and let `/retro` catch what slips through in production. For a single **behavioural line** rather than a whole skill, the cheap version is the micro-test protocol under §4 — control arm, 5+ runs, hits read by hand.

## 12. Sequence output: evidence slots before verdict slots

A template that asks for the verdict first gets an analysis written to justify it — generation conditions on its own output, so the first committed sentence anchors everything after (failure mode #15). Order mandatory sections so evidence is produced before the conclusion is stated: observations → diagnosis, findings → severity, gate rows → GO/NO-GO. This governs *derivation* order inside the working artifact; the reader-facing summary still leads with the outcome (`core.md`) — the executor writes the conclusion last and places it first. When editing a template, moving the verdict slot above the evidence slots is a regression even though "nothing was removed".

---

**The meta-rule:** when an executor fails your prompt, the cheap diagnosis is "weak model"; the useful one is "which mechanism above did my prompt rely on that wasn't there?" Almost every reliable-prompt trick is one of two moves — **move state out of attention into structure** (1, 2, 5, 6, 9, 12) or **make the failure mode a first-class citizen of the prompt** (4, 7, 8, 10). Strong models make weak prompts look good; you find out which you wrote when the model changes.
