# Work-Log Contract — every executing skill writes back to the artifact it was handed

`/implement` § *Persist implementation log* is the original. This file extends it to every skill that
**changes the tree, or measures it, on behalf of a planning artifact**: `/diagnose`, `/test`,
`/test-spec`, `/refactor`, `/tdd`, `/perf`, `/clean-mvp`, `/sweep`. The chat reply is a copy of the
log, never the only record. Measured on one project: in one parallel wave, six `/diagnose`
sessions each fixed a card and left **zero** on-disk logs. The close-out had only commit subjects
to verify against, and every post-deploy check those sessions could not run existed only in
transcripts.

## When it applies

| What the session was handed | Target file | Mandatory? |
|---|---|---|
| A plan under the **Plans/backlog location** (PROJECT.md) | that plan | **yes** |
| A card, spec or backlog item file | that file | **yes** |
| A per-session brief from a prompt pack whose first line names a card or plan | the card or plan the brief names | **yes** |
| A bare description, a source path, `staged`, a git range | none — keep the skill's own suggest-only note | no |

A target that lives outside the repo still gets the log; flag that it will not reach a commit.

## How

1. **Keep a ledger on disk from the start.** Create `<scratchpad>/<skill>-ledger-<slug>.md` and
   print its path. List the artifact's steps or acceptance criteria verbatim. A card with no steps
   uses its direction/harm bullets plus the brief's test line as rows. Mark each row `todo`,
   `done`, `deviated` or `skipped` as you go.
2. **Record deviations at the moment of decision.** Each row goes in the ledger's `## Deviations`
   table with four columns: `Artifact said` (verbatim), `What was done`, `Reason`, `Decided by`.
   `Decided by` is `[AGENT]` or `[USER] "<verbatim quote>"`, exactly as in `/implement`. A row
   reconstructed at the end is not a record.
3. **Append the log before the final reply.** Re-read the ledger first. Append — **never overwrite,
   never edit earlier sections** — `## <Skill> Log — <YYYY-MM-DD> — <VERDICT>` to the target file,
   using the sections below. Omit a section only by writing its `None` line.
4. **Set the status.** A file with status frontmatter gets `DONE`, `PARTIAL` or `BLOCKED`, plus
   `completed_at` when terminal and a reason in `notes`. A file without frontmatter carries the
   verdict in the log heading only; never bolt frontmatter on. A board or run-order row belongs to
   the coordinator: **propose** the change, don't write it.
5. **Commit suggestion.** It lists the target file by explicit path next to the code
   (`/implement` § Commit Message).
6. **In a parallel wave,** append only your own section. A correction to earlier text is a
   `Superseded:` bullet inside your section, never an in-place edit.

## Log sections (in this order)

```markdown
## <Skill> Log — <YYYY-MM-DD> — DONE | PARTIAL | BLOCKED | NOT REPRODUCED

Session: <wave/session id or "solo">, route `/<skill>`. Rows: N/N accounted (d done · v deviated · s skipped).

### Result
<skill-specific block — see the table below>

### Changes made
| File | What changed | Row |

### Deviations
| Artifact said | What was done | Reason | Decided by |   ← or "None"

### Verification
- Tests: `<exact command>` → <counts> (or "not run — <reason>")
- Behaviour: drove `<command/flow>` → observed `<value>` (or "skipped — <reason>")
- Acceptance number from the artifact: <expected> → <observed>

### Re-check later (post-deploy / soak / needs another session)
| Row | Command | Baseline (captured now, dated) | Pass condition | When readable |   ← or "None"

### Findings not fixed here
| Finding | Confidence (observed / inferred) | Suggested owner |   ← or "None"

### Out-of-scope edits
| File | Why it was safe (sequenced / unowned) | What & why |   ← or "None"
```

**Re-check later is the section that gets lost.** Anything the session could not observe itself
gets a row with its command and today's baseline: a production log grep, a 24-hour count, a query
after N events, a UI gesture. If the epic declares an end-to-end verify table, **propose** the same
rows in the final reply; the coordinator writes them into that table.

## Skill-specific `Result` block

| Skill | `### Result` holds |
|---|---|
| `/diagnose` | the Diagnosis Report fields: symptom, reproduction (command + output), isolation `path:line`, root cause, fix, related risk (a search for the same defect class) |
| `/test`, `/test-spec` | each pin written (test → the behaviour or spec line it pins); defects found while pinning (pinned as current behaviour, never the wished one); coverage before → after if measured; floors or budgets changed |
| `/refactor`, `/clean-mvp` | the findings or removal table, each row with its verdict (FIRST / AFTER / LATER / NEVER, or REMOVE / KEEP / DEFER) and applied / left; the price line |
| `/tdd` | the slices table (behaviour → test → status) and any surviving devil's-advocate cheat |
| `/perf` | metric and budget; baseline → final (median ± spread, exact command); the top-3 profile; kept and reverted changes with expected vs actual; the regression guard |
| `/sweep` | the inventory count; transformed / deferred-with-reason / flagged; the zero-leftover re-scan command and its output |

Don't restate the rules these blocks judge against. Name the rule file.
