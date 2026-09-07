---
name: deploy
disable-model-invocation: true
description: >-
  Pick the cheapest sufficient deploy command for what actually changed — classify the working
  tree against the project's Deploy mapping, name the command and what it costs, and hand it
  over as text the user runs. Includes the "no deploy needed" branch and a post-deploy
  verification checklist. Never executes anything.
  TRIGGER when: the user asks how to deploy / push / ship this change, which deploy command to
  run, whether a change needs a deploy at all, or wants the deploy step after work has landed.
  DO NOT TRIGGER when: the question is the *strategy* for shipping something risky or
  irreversible (expand-contract, flags, canary) — that is /rollout; the question is whether the
  release is ready at all — that is /preflight; production is currently broken — that is
  /incident.
allowed-tools: Read, Grep, Glob, Bash, AskUserQuestion
effort: medium
---

# Deploy: $ARGUMENTS

Pick the **cheapest sufficient** deploy command for what actually changed, and hand it over as
text. `$ARGUMENTS` optionally narrows the scope (a path, a commit range); empty = the current
working tree plus the last commit.

**This skill never runs a deploy command.** Every command it produces is presented as text for
the user to copy. That is not a formality: a deploy is an outward-facing, hard-to-reverse action,
and "it was obviously the next step" is exactly how an unsanctioned one happens.

## Phase 0 — Load the mapping

- [ ] `PROJECT.md` → **Deploy mapping** (change kind → action) and **Commands** → `deploy`.
- [ ] `PROJECT.md` → **Architecture**, to know which modules are *local-only* (they never ship).
- [ ] `PROJECT.md` → **Commands** → `remote-probe`, for the verification step. It is read-only by
      contract — a probe inspects, it never deploys or restarts.

**No Deploy mapping in the profile?** Do not guess a command. Build a draft:

1. Find the real deploy entry points — `Makefile` targets, `package.json` scripts, CI workflow
   jobs, a deploy script, container/compose files. Say which you found and where.
2. Ask the user (one `AskUserQuestion`) to confirm the change-kind → command rows and the rough
   cost of each.
3. Offer to write the confirmed table into `PROJECT.md` → Deploy mapping, so the next session
   does not re-derive it. **Confirm before editing the profile.**

If the project genuinely has no deploy step, say so and stop — that is a complete answer.

## Phase 1 — Classify the change BEFORE choosing a command

Order matters: naming a command first and justifying it afterwards is how a 5-minute full rebuild
gets suggested for a config-only edit.

```bash
git status --short          # uncommitted: staged + unstaged
git diff --name-only HEAD~1 # what the last commit moved
```

Bucket every touched path against the profile's mapping. Typical kinds, in the vocabulary the
mapping will use:

| Change touches… | Usually means |
|-----------------|---------------|
| Application code | the cheap code-only path — sync/restart, no image rebuild |
| Config or environment only | the config-only path, if the project has one |
| Dependency manifests / lockfiles / container definition | the expensive path — a full rebuild, no shortcut |
| Generated artifacts, data, results | an artifact-sync path, or nothing at all |
| Local-only modules (per Architecture — tooling, analysis, notebooks, docs) | **no deploy** |

A changeset that spans buckets takes the **most expensive** command among them — one command, not
a sequence, unless the mapping explicitly sequences them.

## Phase 2 — Name the command, and what it costs

Present exactly one recommended command plus the alternatives it beat, with the cost of each.
Cost is the whole point of this skill: the difference between the cheap path and the full rebuild
is usually 30 seconds versus 5 minutes, and the expensive one gets picked by default when nobody
states the number.

```
Change:      <bucket> — <the files, briefly>
Command:     <command from the profile>          (~<cost>)
Not needed:  <the more expensive command> (~<cost>) — <why this change doesn't require it>
```

If the profile's mapping does not cover what changed, say that plainly and ask rather than
extrapolating to the nearest command.

## Phase 3 — The "no deploy needed" branch

This branch is a real outcome, not a failure to find a command. When everything that changed is
local-only per the profile's Architecture, say **"No deployment needed"**, name the paths that led
to that conclusion, and stop. Do not offer a command "just in case" — an unnecessary deploy is a
real risk taken for no reason.

## Phase 4 — Post-deploy verification checklist

Hand this over with the command, as steps the user runs after it:

- [ ] **Startup check** — the project's log/status command, to confirm the service came up rather
      than crash-looped. This is the one step nobody should skip.
- [ ] **Read-only probe** — `PROJECT.md` → Commands → `remote-probe`, to confirm the deployed
      surface answers.
- [ ] **New configuration** — if environment variables or config keys were *added*, they must
      exist on the target before the deploy is meaningful. Say which ones, by name.
- [ ] **State/schema change** — if the change touches persisted structure, name the migration or
      the state check that proves it applied — and, where something outside this repository reads
      that structure, the check that those readers still work.
- [ ] **Rollback line** — the exact command that returns to the previous version, stated *before*
      the deploy, not after something goes wrong.

## Output

Keep it short — a classification, one command, the checklist:

```markdown
## Deploy — <what changed, one line>

**Classification:** <bucket> (<the deciding paths>)
**Run this:** `<command>`  (~<cost>)
**Not:** `<more expensive command>` (~<cost>) — <one line why>

### After it lands
- [ ] <startup check command>
- [ ] <read-only probe command>
- [ ] <config/migration notes, if any>
- [ ] Rollback: `<command>`
```

## Hard rules

- **Never execute.** Present every command as text the user copies. Suggest, don't ship.
- **Classify before choosing.** The command follows from the bucket; the bucket never follows
  from the command.
- **Commands come from the profile.** Never invent a deploy target, and never guess at one that
  "looks standard" for the stack.
- **Cheapest sufficient.** Suggesting the heavy command for a light change is a finding against
  this skill, not a safe default.
- **"No deploy needed" is a valid, complete answer.**

## See also

- **`/rollout`** — *how* to ship something risky or irreversible (staged, flagged, reversible).
  This skill answers *which command*; that one answers *what strategy*.
- **`/preflight`** — the release-readiness gate that runs before you get here.
- **`/incident`** — production is already broken; mitigation comes first, and the same
  never-execute rule applies.
