---
name: handoff
disable-model-invocation: true
description: >-
  Snapshot the live session state into a resume doc at the project's plans/backlog
  location so a fresh session (or another developer) can pick the work up without
  re-deriving context: what's done, what's next, key decisions, modified files, and
  how to verify. Complements the deviation report /implement writes.
  TRIGGER when the user wants to hand off / pause / checkpoint work, save progress for
  later, or prep a resume note before a context reset ("handoff", "save state",
  "checkpoint this", "I'll continue tomorrow", "write a resume doc"). DO NOT TRIGGER
  to execute a plan (use /implement) or to write a feature spec (use /analyst) — this
  only snapshots state and writes no code.
allowed-tools: Read, Grep, Glob, Bash, Write
effort: medium
---

# Handoff — snapshot state for resume: $ARGUMENTS

Capture everything a fresh session needs to continue THIS work without re-deriving it.
You do NOT implement, refactor, or run heavy builds — you observe the current state and
write one resume document. This is the explicit, durable counterpart to the
`precompact.sh` hook (which auto-reinjects a lighter reminder on compaction).

This skill carries ONLY invariant workflow logic. Every project-specific fact (commands,
plans location, naming convention) is read at runtime from `.claude/PROJECT.md`.

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md`. If it is missing, or `profile_status` is `TEMPLATE` (or it
   still contains `<...>` placeholders), **STOP** and tell the user:
   "Profile not configured — run `/bootstrap` to generate `.claude/PROJECT.md`, then
   re-run `/handoff`." Do not proceed.
2. Resolve and hold:
   - **Plans/backlog location** and naming convention (PROJECT.md → Plans / backlog).
     This is where the resume doc is written.
   - **Commands** — `test`, `test:targeted`, `lint` (PROJECT.md → Commands). These are
     the "how to verify" the next session will run; do not run them here.
3. Read the repo `CLAUDE.md` "Context compaction" section if present, to match what it
   says must be preserved.

## Phase 1 — Gather state (no questions, fast, read-only)

Collect from the session and the working tree. Do NOT run the test/lint suite here — a
handoff is a snapshot, not a verification (that is `/test` or the opt-in `verify-stop.sh`).

- **Source plan/backlog file** — `$ARGUMENTS` if it names one; else the plan/backlog file
  this session has been working from; else the most-recently-modified file in the
  plans/backlog location. Note its path (may be none).
- **Git state** — run, from the repo root:
  - `git branch --show-current`
  - `git rev-parse --short HEAD` — the commit this snapshot describes; it goes into the
    frontmatter as `git_commit` and is what the next session diffs against to see what moved
    since (Phase "How to resume" below). Without it, "what's done" has no anchor in time.
  - `git status --short` (modified/untracked files)
  - `git diff --stat HEAD` (size of the change)
  - `git log --oneline -5` (recent commits, for orientation)
- **What's done / what's next** — never a read-back of a session task list (it may not exist, and
  a ticked item is a claim, not a diff), so this is *derived from evidence*, in this order:
  1. **The source plan's step list** — the authoritative enumeration of the work. Each step is
     done, in progress, or untouched.
  2. **What the session wrote down** — the plan's `## Implementation Log` and Deviation rows if
     `/implement` already appended them, plus any step ledger / deviation scratchpad this
     session kept (`/implement`, `/sweep`, `/tdd` each keep one in a file — `/implement`'s is
     `<scratchpad>/implement-ledger-<slug>.md`, and it holds deviation rows the plan does not
     yet have).
  3. **The working tree** — the git state gathered above: `git status --short` and
     `git diff --stat HEAD` say which files actually moved; `git log --oneline -5` says what
     already landed.

  **Cross-check the plan against the tree — do not trust either alone.** A step whose files
  show no diff is not done however confidently the chat reads, and a file modified with no
  matching step is either an undeclared deviation or out-of-scope work: say which. Any step
  whose state you cannot establish from the three sources goes into the doc marked
  **unverified**, never silently promoted to done — a resume doc that overstates progress
  costs the next session more than one that admits a gap.
- **Test/lint status** — the *last observed* result from this session (e.g. "tests green
  before the last edit", "lint not run since"). If unknown, say "not run this session"
  and record the exact commands so the next session can run them.
- **Key decisions & open questions** — decisions made this session and assumptions or
  questions still unresolved (mirror the spec/plan's open-questions style).
- **Artifact continuity** (per `rules/_generic/planning-artifacts.md`) — flag any **decision
  made this session that was NOT yet written into the plan**, and any **sibling plan / epic
  overview left unswept** after a decision rippled. These are the first things the next session
  must reconcile; a decision left only in this chat is lost on reset.

## Phase 2 — Write the resume doc

Write a NEW file to the plans/backlog location using the project's naming convention,
e.g. `<plans>/<YYYY-MM-DD>-handoff-<slug>.md` (slug from the source plan or the work
focus; prefix a ticket id if the project uses one). **Never overwrite** an existing plan
or a prior handoff — always a new dated file.

Frontmatter + sections:

```markdown
---
type: handoff
created: <YYYY-MM-DD>
branch: <current branch>
git_commit: <short SHA of HEAD when this was written>
source_plan: <path or "none">
status: <IN_PROGRESS | BLOCKED | READY_TO_REVIEW>
---

# Handoff — <work focus> (<YYYY-MM-DD>)

## What's done
- <completed step / change, with file refs — plan step ↔ the diff that proves it>
- <step whose state the tree could not confirm> — **unverified**, check `<what to look at>`

## What's next
- <the very next action, then the rest, in order>

## Key decisions
- <decision> — <why>

## Open questions / assumptions
- <unresolved question or assumption to validate>

## Artifact continuity
- Decisions not yet written into the plan: <none | which decisions, into which plan>
- Sibling plans / overview left unswept: <none | which files need reconciling>

## Modified files
- `path` — <what changed / still in progress>

## How to verify
- Branch: `<branch>`; uncommitted: <one-line summary>.
- Run: `<test / test:targeted command from PROJECT.md>`, `<lint command>`.
- Last observed: <e.g. "tests green before final edit; lint not yet run">.

## How to resume
- Re-read this file + the source plan (`<path>`) + `.claude/PROJECT.md`.
- **Re-verify before trusting.** `git log --oneline <git_commit>..HEAD` and `git status --short`
  first: anything there happened after this snapshot. Then take each "What's done" line and
  check it against the live tree — `[from handoff] → [checked now] → present | missing | modified`
  — before building on it. Re-read, then re-check; a line that no longer holds is corrected here,
  not carried forward.
- Continue from "What's next"; for execution use `/implement <source plan>`.
```

Keep it factual and short — it is read at the start of the next session, not archived
prose. Do not duplicate the full plan; link to it via `source_plan`.

## Phase 3 — Hand off

- Print the resume doc path.
- Summarize in 2–3 lines: where things stand and the single next action.
- Remind the user the next session can pick up with `/implement <source plan>` (or just
  by reading the resume doc), and that `precompact.sh` will reinject a lighter reminder
  automatically if this session compacts before then.

## Commit (only if handoff docs are shared)

If the artifact git policy in `PROJECT.md` keeps handoff docs **committed**, offer a
copy-paste commit block for **this one file** — follow the **Commit Message** pattern in
`/implement`: explicit paths only (never `-A` / `.` / a directory), output text the user
pastes (**never run it**). If handoff docs are **local** (gitignored), skip this.

## DO NOT

- Do not write code, refactor, or run the full test/lint suite — only snapshot state.
- Do not overwrite an existing plan or handoff file — always write a new dated file.
- Do not run `git commit` or a deploy.
- Do not invent status: if test/lint was not run this session, say so explicitly.

## See also

- **`/implement`** — resume execution from the source plan; writes the deviation report
  this snapshot complements.
- **`/analyst`** — write a feature spec (not a state snapshot).
- **`/test`** — actually run/verify the suite (handoff only records the *last observed* status).
