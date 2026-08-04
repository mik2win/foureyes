---
name: preflight
description: >-
  Release-readiness gate — one orchestrated pass before code ships: full test suite +
  lint/typecheck, dependency & security quick pass, docs drift, config/migration/flag check,
  changelog draft from commits, and a GO / GO-WITH-RISKS / NO-GO verdict with a suggested
  deploy command (never executed). TRIGGER when: the user is about to ship/release/deploy/tag
  ("are we ready to ship", "preflight", "release check", "can this go out"). TRIGGER ALSO on
  the same ask phrased as plain work, with this skill unnamed — "anything blocking release",
  "run the pre-release checks", "is main safe to deploy" — an ask for a ship/no-ship judgment
  IS this skill.
  DO NOT TRIGGER when: the user wants a review of one diff (use /code-review), a security-only sweep (use
  /audit-security), or to settle an epic's plans and archives (use /close-epic — run it before
  this when an epic is involved).
allowed-tools: Read, Grep, Glob, Bash, Write, AskUserQuestion, Agent, Skill
effort: high
---

# Preflight: $ARGUMENTS

The last gate before code leaves the machine. `/close-epic` settles the *plans*; this settles
the *release*: everything between "the code is done" and "the code is out" that is checkable,
checked once, in one report. Propose-only — the deploy command is **suggested, never run**
(the kit's code-publish policy stands: the user ships).

`$ARGUMENTS` optionally names the release scope (a tag/ref like `v1.4.0..HEAD`, a branch, or
free text); empty = resolve in Phase 1.

---

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` — **Commands** (test, lint, typecheck), **Deploy mapping**,
   **Integrations**, **Plans location**. If missing or `TEMPLATE`, fall back to the root `CLAUDE.md`
   (always in context) when it carries those commands — note you're running without a kit profile;
   **STOP**: run `/bootstrap` only if *neither* has them.
2. Read `.claude/rules/_generic/code.md` and any release/CI conventions in the profile.
3. If `CONTEXT.md` exists, read it — the changelog speaks the project's language.

## Phase 1 — Resolve the release scope

Determine what is shipping, in order of preference:

1. `$ARGUMENTS` as a ref/range → `git log --oneline <range>` + `git diff <range> --stat`.
2. Last release tag → `git describe --tags --abbrev=0` then `<tag>..HEAD`.
3. No tags → merge-base with the default branch, or ask via `AskUserQuestion`.

List the commits and changed files that constitute the release. **If the working tree is
dirty, flag it first** — shipping with uncommitted changes is a NO-GO finding unless the user
says those files are out of scope.

## Phase 2 — Run the gates

Each gate produces a row: **PASS / WARN / FAIL + evidence**. Run cheap ones first; don't stop
on failure — the report shows the whole picture. Skip a gate only when it's inapplicable, and
say so.

1. **Tests** — the full `test` command (PROJECT.md → Commands). FAIL on any failure; record
   the failing names verbatim.
2. **Lint / typecheck** — the profile's commands. FAIL on errors, WARN on warnings.
3. **Dependencies** — chain **`/deps`** (via `Skill`) in its quick mode, or if unavailable run
   the stack's audit command from the profile. FAIL on known-exploitable vulns in shipped
   deps; WARN otherwise.
4. **Security** — spawn the **`security-reviewer`** agent scoped to the release diff.
   FAIL on CRITICAL findings, WARN on HIGH.
5. **Docs drift** — same mechanic as `/close-epic`: does the release change a user-facing
   surface (commands, routes, config, API) that README/usage docs still describe the old way?
   Grep the docs for the changed surface names. WARN with the stale `path:line`s.
6. **Config & migrations** — grep the release diff for: new env keys / settings (are they
   documented and present in deploy config?), pending schema migrations (is the migration
   step in the deploy plan?), feature flags introduced (correct default?). FAIL on a
   migration or required key with no deploy step; WARN otherwise.
7. **Behavior spot-check** — if a run command exists and the release touches a runtime
   surface, drive the main affected flow once (the `/implement` Behavior Check discipline,
   applied to the release build). WARN if it can't be driven; record what was observed.

## Phase 3 — Changelog draft

From the Phase 1 commit list, draft a changelog section grouped **by user-visible effect**
(Added / Changed / Fixed / Security — or the project's existing changelog format if one
exists; follow it). One line per meaningful change, in the project's vocabulary — not a raw
commit dump. If the project keeps a `CHANGELOG.md`, show the draft **for the user to paste or
approve** — apply it only on confirmation.

## Phase 4 — Verdict & report

`Write` the report to `<plans>/<YYYY-MM-DD>-preflight-<scope>.md` and print it:

```markdown
# Preflight — <scope>

| Gate | Status | Evidence |
|------|--------|----------|
| Tests | PASS/WARN/FAIL | <counts / failing names> |
| Lint/typecheck | | |
| Dependencies | | |
| Security | | |
| Docs drift | | `path:line`s |
| Config & migrations | | |
| Behavior spot-check | | drove <flow> → observed <result> |

## Verdict: GO | GO-WITH-RISKS | NO-GO
- NO-GO: any FAIL — list the blockers, each with its fix route
  (/diagnose, /test, /deps, security fix …).
- GO-WITH-RISKS: WARNs only — each risk named with owner ("ship and fix forward" needs
  the user to say so).
- GO: all PASS.

## Changelog draft
<the Phase 3 section>

## Deploy (suggested — run it yourself)
<command(s) from PROJECT.md → Deploy mapping + verification step, e.g. tail logs>
```

## Hard rules

- **Never deploy, tag, commit, or push.** Output the commands; the user runs them.
- **Report the whole board.** Run every applicable gate even after a FAIL — a NO-GO with one
  known blocker beats three consecutive surprise NO-GOs.
- **Failures verbatim.** Failing test names and vuln IDs are quoted, not summarized away.
- **A skipped gate is a stated gate.** "Skipped — <reason>" in the row; never silently absent.
- **Facts from PROJECT.md.** Commands, deploy mapping, docs locations — never hardcoded.

## Cross-reference

- **Before this:** `/close-epic` (epic bookkeeping), `/code-review` + `/test` (per-change
  quality). **Components it orchestrates:** `/deps`, `security-reviewer` agent.
- **On NO-GO:** `/diagnose` (failures), `/test` (coverage), `/audit-security` (deep security).
- **After ship:** `/retro` — feed what preflight caught back into the kit's rules.
