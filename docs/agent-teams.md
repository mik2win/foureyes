# Agent teams × the kit's wave model — a readiness sketch

> Status: **experimental, do not build on it.** Agent teams ship behind an env flag in current Claude Code (mid-2026) and their surface is still moving. This doc exists so that when they stabilize, adopting them is a mapping exercise, not a redesign. Until then the kit's answer to multi-session work stays `/prepare` waves + `/epic-status`.

## What agent teams provide (as of the 2026-07 doc sweep — re-verify before use)

- A **shared task list** all teammates read and claim work from.
- **Inter-agent messaging** — teammates talk to each other, not only to the lead.
- A **lead** that approves teammates' plans before they execute.
- **`TaskCompleted` quality gates** — a hook-like check that can reject a teammate's "done" and send the task back.

## The mapping is 1:1 with what the kit already does

| Agent-teams concept | Kit equivalent today |
|---------------------|----------------------|
| Shared task list | The epic directory from `/prepare` Phase 6 — `00-overview.md` + `NN-<subtask>.md` files with `status` frontmatter |
| Task claiming / collision avoidance | Wave scheduling with pairwise-disjoint `Owns` file sets; `/epic-status` session-collision check |
| Lead plan-approval | `/prepare`'s decomposition + the per-session briefs in `implementation-prompts.md` — decisions made once, upstream |
| Inter-agent messaging | Deliberately absent: siblings in a wave are *designed* not to need each other (disjoint ownership); cross-subtask facts travel through plan files, per the Artifact-Continuity Contract |
| `TaskCompleted` gate | `/implement`'s quality-auditor pass + `Verify:` lines + `plan-verifier` at `/close-epic` |

## What adoption would actually change

The kit's wave model is **files-as-coordination**: it survives session crashes, works in any harness, and leaves an audit trail. Agent teams move coordination into the harness: live claiming instead of pre-assigned waves, messages instead of plan-file folds, a runtime gate instead of a close-time verifier. The wins would be (a) dynamic re-balancing when one subtask finishes early, and (b) immediate rejection of bad work instead of catching it at wave close.

The risks mirror the worktree limitation (`working-with-agents.md`): teammates that don't reliably inherit `.claude/` rules would run outside the kit's discipline, and harness-internal chatter is invisible to `/retro`'s learning loop unless it lands in artifacts.

## Adoption checklist (when teams leave the env flag)

1. Re-verify the feature list above against current docs — names and surface will have moved.
2. Run the rules-inheritance test on a teammate (same test as for worktrees: have it report which `.claude/rules/*` loaded).
3. Map `TaskCompleted` to the quality-auditor rubric so the runtime gate and the close-time verdict agree.
4. Keep plan files as the durable record even if teams coordinate live — the Artifact- Continuity Contract outlives any harness feature.
5. **Before reusing a kit agent as a teammate, check what its contract rests on.** A teammate definition honours `tools` and `model`, but **`skills` and `mcpServers` are ignored**, and the body is *appended* to the system prompt rather than replacing it. Three kit agents carry their working contract in exactly that field — `agents/code-reviewer.md:13` (`code-review, refactor`), `agents/quality-auditor.md:14` (`audit-quality`), `agents/security-reviewer.md:16` (`security-review`) — so as teammates they would run silently without the skills that define them. Re-verify against current docs first (item 1): this is documented behaviour of an experimental feature, and the `mcpServers` half is pre-emptive — no kit agent declares one today. Also note in-process teammates cannot spawn a background subagent of their own.
