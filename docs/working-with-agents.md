# Working with agents — the developer's side of the contract

The kit disciplines the agent. This page disciplines the *collaboration* — what the human does that makes agent work compound instead of churn. Written by an agent, about what actually helps from the other side of the conversation.

## Briefing

- **Give goal + constraints + acceptance, not steps.** State what must be true when the work is done and what must not change; let the agent own the route. Dictate steps only for genuinely mechanical work — then dictate them exactly. The worst brief is half-and-half: loose enough that the agent must guess, specific enough that it can't flag your guess.
- **Front-load what the agent cannot discover.** Intent, priorities, deadlines, "we tried X in 2024 and it burned us", which trade-off you'd pick — none of that is in the repo. What *is* in the repo, don't retype: the agent reads code faster than you type summaries of it.
- **Your specificity sets the output's specificity.** A vague ask gets a plausible guess; one concrete example of the desired outcome ("like `path:line` but for orders") beats three paragraphs of description. This is symmetric — the agent's specs work on you the same way.
- **For diagnosis, describe symptoms, not your theory** — or label the theory as a theory. A stated diagnosis anchors the search (failure mode #7: hypothesis mirroring); the agent will find evidence for the cache problem you mentioned whether or not the cache is guilty.

## Steering

- **Correct the first drift immediately.** Deviation compounds: a wrong turn at step 2 costs one message now and the whole session at step 20. If a plan or early diff smells wrong, stop it — "keep going, I'll fix it later" is how later gets expensive.
- **When the frame is wrong, regenerate — don't patch.** Interactively repairing a structurally-wrong draft costs more than a fresh run with a corrected brief, and the failed frame keeps gravitating (failure mode #6: context poisoning). Patch details; rebrief frames.
- **After a thrash, reset.** Two or three failed fix attempts poison the context. Take the `/handoff` snapshot, open a fresh session, hand it the *problem* — not the fix history.
- **One topic per session.** Interleaved topics bleed into each other's context and dilute both. The pipeline's per-stage artifacts exist precisely so you can stop cleanly and resume anywhere.

## Verifying

- **Ask for evidence, not confirmation.** "Did the tests pass?" invites "yes" (failure modes #1, #14). "Paste the test output" produces the truth. The kit's report formats are shaped to pre-answer this — read the evidence sections, not just the verdict line.
- **Review the diff, not the summary.** The summary is the agent's *belief* about the diff; the diff is the fact. For big changes, review the plan hard (it's small and dense with decisions) and sample the diff against it — that's the leverage point the kit's plan-centric flow is built around.
- **Calibrate autonomy by track record, not vibes.** New model, new skill, new domain → verify everything for a while. Proven combination → sample. And trust the gates you built: if work passed stage gates and `/preflight`, re-checking it by feel wastes you; if it didn't pass them, accepting it by feel burns you.
- **Shape work into reviewable slices.** Your attention is the scarce resource in the loop. Vertical slices, waves, batch-sized commits — the kit produces them so that no single review exceeds what a human can actually hold. Don't merge what you couldn't review.

## Improving the system (not just the output)

- **Recurring feedback belongs in rules, not in chat.** Correcting the same thing twice means the correction is in the wrong place — put it in a rule (or let `/retro` mine it) so every future session inherits it. Chat corrections evaporate; rules compound.
- **Criticize the artifact, not the agent.** "This plan misses the migration step" is actionable; "you always forget migrations" isn't (and if it *is* always — that's a rule, see above).
- **Feed the loop.** The kit learns through artifacts: deviations land in plans, plans land in archives, `/retro` turns archives into rules. The single highest-leverage habit is running `/retro` after each epic — five minutes of confirmation that make the next epic measurably smoother.
- **Keep the profile honest.** Half of "the agent is being dumb" is a stale `PROJECT.md` asserting a world that no longer exists. `/arch-health`'s drift check helps; so does fixing the profile the moment you notice the lie.

## Worktree isolation — a known limitation (keep the waves)

`isolation: worktree` gives an agent its own git worktree — real protection against parallel *file* collisions. The catch: the project's `.claude/` rules and config are **not reliably inherited** inside an agent worktree, so a worktree'd subagent can run without the kit's always-on rules (working discipline, reporting, guard hooks). That's why the kit's answer to parallel writes is the **wave model** (`/prepare` — disjoint file ownership, one shared working tree, separate commits), not worktrees; the only shipped use is `test-writer`, which mostly needs *test-runner* isolation, where missing rules cost little.

Before widening worktree use, verify inheritance is fixed with a one-minute test: spawn any agent with `isolation: worktree` and have it report which `.claude/rules/*` files it can actually see and which loaded. If they all load, worktrees become a real option for parallel *writers* — at that point also look at `.worktreeinclude` (copying gitignored `.env`/config into fresh worktrees) so isolated agents can run the project at all.

## The economics, plainly

Agent work is cheap to generate, expensive to review, and *very* expensive to un-merge. Spend accordingly: invest in briefs and plans (cheap, high leverage), review at the artifact level (concentrated decisions), regenerate rather than nurse bad drafts (sunk cost is the agent's failure mode #1 — don't make it yours), and push every lesson into rules where it pays compound interest.

**One economy that runs backwards: don't cap the controller's thinking to save tokens.** In one measured run on an outside harness, capping an orchestrator's thinking budget made the run *more* expensive — turns went 92 → 138 and output volume roughly doubled, because the reasoning that was cut had been buying efficiency per turn. Treat this as a directional warning from someone else's setup and model, not a law: it is a single external measurement, and the kit does not currently cap anything (`effort:` across its agents is 7 × `high`, 2 × `medium`, and never `low`). It is here because the saving is intuitive and the result is not — so the idea tends to get retried.
