---
name: incident
disable-model-invocation: true
description: >-
  Production incident discipline — stabilize first, understand later: triage severity and blast
  radius, mitigate with known-good states (rollback / flag off / failover), preserve evidence
  before it's destroyed, verify recovery by user-visible signal, then hand root-cause to
  /diagnose and feed the post-incident review.
  TRIGGER when: something is broken in production/live for real users RIGHT NOW — an outage,
  error spike, data corruption in progress, degraded service, a bad deploy — and the priority is
  making it stop.
  DO NOT TRIGGER when: the bug is reproducible in dev/CI with no live users affected (use
  /diagnose), or the incident is over and only analysis remains (use /diagnose for root cause,
  /retro for patterns).
allowed-tools: Read, Grep, Glob, Bash, WebFetch, AskUserQuestion, Write
effort: high
---

# Incident Response

Incident: $ARGUMENTS

## Principle — the priority inversion

Dev-time debugging (`/diagnose`) is *understand → then fix*; an incident **inverts** this:
**stop the harm → preserve the evidence → then understand.** Root-causing while users bleed
is the wrong altitude, and "quick fixes" invented under pressure are how one incident
becomes two. During the fire, movements go **toward known-good states** (the previous
deploy, the flag off, the replica) — never toward novel code written under adrenaline.

Everything that touches production is **suggested, never run**: this skill drives the
investigation and drafts the exact commands; the user executes them. Speed comes from
having the right command ready, not from the agent firing it.

## Phase 0 — Load profile (fast pass)

- [ ] Read `.claude/PROJECT.md` — **Commands** (logs / deploy / rollback if present),
      **Integrations** (monitoring, error tracking — read the live signal there, not
      guesses), **Architecture** (blast-radius map).
- [ ] If PROJECT.md is missing/TEMPLATE: **do not stop** — an incident outranks bootstrap
      ceremony. Ask the user for the two facts you need now (where are logs? how was the
      last deploy done?) and note the degraded mode in the report.

## Phase 1 — Triage (minutes, not depth)

- [ ] **Impact now**: who/what is affected, since when, how bad — from monitoring/error
      tracker/logs, stated with numbers ("checkout 5xx at 40% since 14:02"), not adjectives.
- [ ] **Severity call**: users blocked / money or data wrong / degraded / cosmetic. This
      sets how much process to skip — full outage justifies acting on *inferred* evidence;
      a cosmetic glitch doesn't justify a risky restart (`core.md` still
      applies, scaled by severity).
- [ ] **What changed?** Last deploy, config change, flag flip, dependency/provider event,
      traffic shape (`git log` + deploy history + provider status pages). Most incidents
      are changes; the most recent change is the prime suspect — *as a hypothesis to check
      against the timeline, not a verdict* (failure mode #11): does symptom onset match
      the change time?
      If nothing changed and the burning component is one nobody priced, read the operating list
      backwards (`docs/decision-craft.md` §9) — the unanswered entry is usually where it lives.
- [ ] **Is it spreading?** Corrupting data, filling a disk, cascading retries → containment
      (stop the writer, disable the job) may outrank diagnosis of anything.

## Phase 2 — Preserve evidence (before any restart)

Mitigation destroys evidence: restarts clear memory state, rollbacks overwrite the bad
build's behavior, log rotation eats the window. **Before** state-destroying mitigation,
capture (draft the exact commands for the user):

- [ ] The error window of logs, copied out of rotation's reach.
- [ ] A handful of failing request/job examples (IDs, payload shapes, timestamps).
- [ ] Current metrics snapshot / dashboard state (screenshot or export).
- [ ] If data corruption: a snapshot/dump of the affected tables **now** — the corrupted
      state itself is evidence, and the backup gates any later repair.

Cheap and skippable only when the mitigation doesn't destroy state (a flag flip preserves
everything — flip first, capture after).

## Phase 3 — Mitigate toward known-good

In order of preference (least novel first). **All of these are drafted commands the user runs —
never fire a deploy, rollback or restart yourself.** Output the exact command, say what it should
do, and wait; a production action taken to save a round-trip is the one action nobody sanctioned.

1. **Rollback** the suspect deploy (the previous build is the most-tested artifact you have).
2. **Flag off** the suspect feature.
3. **Shed or reroute**: failover, disable the non-critical subsystem, rate-limit the
   aggressor, serve degraded.
4. **Restart** — only with a reason it would help (leak, wedged pool), not as a reflex.
5. **Hot-fix forward** — *last resort*, only when no known-good state exists (e.g. the bug
   predates every rollback target). Smallest possible diff, reviewed by a second pair of
   eyes (or a fresh-context subagent) even under time pressure — pressure is when review
   pays most.

For the chosen mitigation, state **before executing** (predict-before-peek,
`core.md`): the expected signal change ("5xx should drop to baseline within ~2
min of rollback") and the abort condition. **Two-strikes applies to mitigations**: if two
attempts haven't moved the signal, the model of the incident is wrong — stop trying
variants, go back to Phase 1's "what changed" with the assumption audit from
`core.md` anti-thrash.

## Phase 4 — Verify recovery

- [ ] The **user-visible** signal is back to baseline (not just "the process is up") —
      the same monitoring numbers from Phase 1, re-read.
- [ ] No secondary damage: queues drained, retries settled, data writes consistent.
- [ ] State plainly what is *mitigated* vs what is *fixed* — a rollback means the bug still
      exists and redeploying reintroduces it; say so in the report so nobody re-ships it
      (failure mode #14 — this caveat must survive every summary verbatim).

## Phase 5 — After the fire

- [ ] **Root cause** → hand the preserved evidence to `/diagnose` (its Phase 1 reproduction
      now has real payloads to work from) and lock the fix with a regression test.
- [ ] **Post-incident review** — write the timeline **from the preserved evidence, not from
      memory** (self-anchoring bends recollection toward the story where responders were
      right): detection → decisions → mitigation → recovery, each with a timestamp and
      source. **Blameless as a hard rule** — causes are systems and defenses, never people;
      a review that names a culprit teaches everyone to hide the next incident.
- [ ] Each contributing cause gets a defense at a named altitude (`core.md`): detection
      (alert earlier), prevention (the `/rollout` stage or check that would have caught it),
      or mitigation (faster rollback path). Recurring patterns feed `/retro`.
      An alert earns that altitude on two conditions — it reliably indicates that user experience
      is degraded, and a responder has a systematic way to act on it. Fail either and delete it.
      Anything the system already heals (autoscale, failover, breaker) is a business-hours
      investigation, never a page.
- [ ] Offer to Write the review to the **Plans location**
      (`<plans>/<YYYY-MM-DD>-<slug>-incident.md`).

## Output Format

```
## Incident Report
**Impact**: [who/what, numbers, start time — and current status]
**Severity**: [call + basis]
**Suspected trigger**: [the change + timeline evidence, or "unknown — candidates ruled out: …"]
**Evidence preserved**: [what, where]
**Mitigation**: [action taken + signal before/after] — MITIGATED / FIXED (say which)
**Residual risk**: [what's still true: bug alive in HEAD, degraded mode on, backfill owed]
**Next**: [root-cause via /diagnose · repair · review]
```

## Hard rules

- **Suggest, never execute** anything that touches production — rollbacks, restarts, flag
  flips, data repairs are drafted commands the user runs.
- **No novel code during the fire** — mitigate with known-good states; hot-fix forward only
  when no known-good exists, minimal and second-eyed.
- **Preserve before you destroy**: state-destroying mitigation waits for the evidence
  capture (or an explicit user "skip it, bleeding is worse").
- **Data repair is gated on a backup** of the affected data taken first — a repair script
  with a bug is the second incident.
- **Mitigated ≠ fixed** — the report always says which one happened, and the caveat travels
  verbatim into every handoff.

## See also

- `/diagnose` — root cause, after the fire is out (dev-time priority order).
- `/rollout` — the staged-deployment discipline that makes the next incident smaller.
- `/retro` — recurring incident patterns fold back into rules.
- `docs/decision-craft.md` — doors, predict-before-peek, pre-mortems.
