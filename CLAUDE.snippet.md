<!-- feature-flow-kit:begin — управляется /bootstrap, не редактировать вручную -->
## Project profile & workflow

This project uses the **feature-flow kit** (`.claude/`). The single source of
truth about stack, commands, architecture and domain is **[.claude/PROJECT.md](.claude/PROJECT.md)** —
all skills read it instead of hardcoding project facts. Keep it current. It's kept out of this
always-on `CLAUDE.md` on purpose, so the every-turn context stays lean and the detail is read on
demand. (If this project instead keeps those facts here in `CLAUDE.md`, that's fine — skills fall
back to it and only ask for `/bootstrap` when neither file carries the facts.) The project's
**shared language** lives in **`CONTEXT.md`** (the ubiquitous-language glossary) + ADRs in
`docs/adr/`, both maintained by `/domain-model`; skills read it and speak its terms.

**Agent-generated artifacts** (briefs, specs, plans, PRDs, issues, handoff notes, and the
`CONTEXT.md`/ADR model) follow the per-category **git policy chosen at `/bootstrap`** — recorded in
`PROJECT.md` → "Artifact git policy". Some are kept **local** (gitignored, never pushed), some are
**committed** (shared). The agent never `git add`/`commit`s them itself; `.gitignore` enforces what
stays local.

**Code-publish control.** The agent **never publishes code without you**: `git add`/`commit`/`merge`/
`push` are denied in `settings.json` and blocked by `guard-bash.sh` (suggest-only — it outputs the
command for you to run). See `PROJECT.md` → "Security / VCS policy" for the project's exact policy and
any other forbidden commands. Web search/fetch for research stay available.

**Feature flow:** `/discover` (research prior-art & reuse — when scope is fuzzy) →
`/analyst` (gather requirements → spec) → `/prepare` (design alternatives + impact +
decomposition plan) → `/implement` (execute plan + audit + tests). Explore first:
`/spike` (validate ONE risky hypothesis, throwaway) · `/prototype` (explore a design space —
logic or UI variations). Align & design: `/grill` (relentless interview), `/domain-model`
(glossary + ADRs), `/codebase-design` (deep-module vocabulary). Quality:
`/code-review`, `/refactor`, `/diagnose`, `/test`, `/tdd` (test-first), `/arch-health`
(periodic architecture scan). Architecture evolution: `/decompose` (monolith vs services),
`/revisit` (re-audit past decisions), `/distill` (mine conventions → rules).
Backlog (local): `/to-prd` → `/to-issues` → `/triage`.
Security: `/deps` + the `security-reviewer` agent. Session: `/handoff`. Lost? `/which-skill`
routes you. Re-run `/bootstrap` to re-adapt the kit after big structural changes.

**Recommended flows** (or just ask `/which-skill "<situation>"` — it gives the whole route and
each skill hands off to the next; you confirm each step):

- **Build a feature:** `/discover → /analyst → /prepare → /implement → /code-review + /test`
  (`/domain-model` alongside). Small/known → start at `/prepare` or `/implement`.
- **Research:** `/discover` (→ global `/deep-research` for open questions) → `/analyst`.
- **Requirements → backlog:** `/grill-with-docs → /analyst → /to-prd → /to-issues → /triage`.
- **Test:** `/tdd` (test-first) · `/test` (cover/clean existing).
- **Fix a bug:** `/diagnose → /tdd | /test` (lock it with a regression test).
- **Refactor:** changed code `/code-review → /refactor`; whole-codebase rot
  `/arch-health → /refactor | /prepare`.
- **Revisit what's built:** split or stay `/decompose` · stale decisions `/revisit` ·
  conventions → rules `/distill` (→ `/sweep` to unify).
- **De-risk a design:** `/spike` (one risk) · `/prototype` (compare options).

## Context compaction

Long sessions get compacted (manually via `/compact` or automatically), and a fresh
session starts empty — so the active plan, modified files, and test status can be lost.
When compaction is imminent or you sense context slipping, make sure the following
survive **in the active plan/backlog file or here in `CLAUDE.md`** (not only in the
transcript):

- **Active plan** — the plan/backlog file path and the current step.
- **Modified files** — what changed and what is still in progress.
- **Test/lint status** — latest result of the project's `test` / `lint` commands.
- **Branch & changes** — current branch + a one-line uncommitted-change summary.
- **Open decisions** — assumptions and decisions still unresolved.

The `precompact.sh` hook re-injects this checklist (with live git state) on every
compaction. For an explicit, durable snapshot before a reset or a developer handoff,
run **`/handoff`** — it writes a resume doc (done · next · decisions · files · how to
verify) to the plans/backlog location.

Claude Code also preserves state natively, and the kit leans on it rather than duplicating
it: the **project-root `CLAUDE.md` is re-read and re-injected after `/compact`**, and
**auto memory** (on by default) persists learnings to `~/.claude/projects/<project>/memory/`
across sessions. Those cover durable facts and conventions; the checklist above and
`/handoff` cover the **transient turn state** (active plan, in-progress files, latest
test/lint status) that native memory does not capture.
<!-- feature-flow-kit:end -->
