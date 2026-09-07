---
name: arch-health
disable-model-invocation: true
description: >-
  Proactive whole-codebase architecture scan — find shallow modules, leaky interfaces, misplaced
  seams, layer violations, and ball-of-mud hotspots; present them as a RANKED report; then grill
  through the one you pick and route it to /refactor or /prepare. Run it every few days to keep
  entropy in check, before the codebase becomes hard to change. Distinct from /refactor (cleans
  the current diff on demand) — this scans the whole tree and surfaces what to clean.
  TRIGGER when: the user wants an architecture health-check, "what's rotting here", "find the
  worst modules", "where's the tech debt", a periodic ball-of-mud scan, or deepening opportunities.
  DO NOT TRIGGER when: the user wants to clean up specific changed files (use /refactor), review a
  diff for bugs (use /code-review), or plan one known change (use /prepare).
allowed-tools: Read, Grep, Glob, Bash, Write, AskUserQuestion, Agent
effort: high
---

# Architecture Health: $ARGUMENTS

Invest in the design of the system *every day*. Agents accelerate coding — and therefore software
entropy — so codebases get complex at an unprecedented rate. This skill is the counterweight: scan
for where the code is becoming a ball of mud, surface the highest-leverage **deepening
opportunities**, and route the chosen one to real cleanup. Run it regularly, not once.

`$ARGUMENTS` optionally scopes the scan to a subtree (a module path) or theme ("the services
layer", "anything touching billing"); empty = the whole codebase per `PROJECT.md` → Architecture.

This skill **proposes** — it does not apply edits. The fix happens in `/refactor` (small) or
`/prepare`→`/implement` (large), so changes go through the kit's normal verification.

---

## Phase 0 — Load profile

**Tooling preflight — one call, before step 1.** Some tools this skill relies on are **deferred**
by the harness: the session lists them by name only and loads their schemas on demand, so calling
one before it is fetched fails. Listing a tool in `allowed-tools` does **not** un-defer it. Issue
a single `ToolSearch` up front covering the whole run — `select:SendMessage,TaskOutput`
(continuing the same finder across loop-until-dry rounds instead of respawning, collecting a
backgrounded batch) — instead of one round-trip per discovery. A name already loaded costs
nothing to include; a schema discovered missing mid-run costs a turn.

1. Read `.claude/PROJECT.md` — **Architecture** (layers, module map, dependency direction, where
   domain logic lives / must not live), **Commands**, and **Plans location** (where the findings
   report is saved). If missing or `TEMPLATE`, fall back to the root `CLAUDE.md` (always in
   context) when it carries the architecture/commands — proceed on it, noting you're running
   without a kit profile. Only if *neither* has those facts, **STOP** and tell the user to run
   `/bootstrap` first.
2. Read `rules/_generic/code-quality.md` and any stack rules whose `paths` cover the scan scope —
   layer/boundary rules are the violations you're hunting.
3. If `CONTEXT.md` exists, read it so findings are named in the project's vocabulary.
4. Read **`skills/codebase-design/SKILL.md`** (+ `DEEPENING.md`; `WHEN-TO-CUT.md` before a finding
   proposes a new seam) for the deep-module vocabulary —
   every finding is phrased in it (shallow module, leaky interface, misplaced seam, information
   leakage…).

---

## Phase 1 — Scan (fan out)

Map the codebase against the smells in `/codebase-design` → DEEPENING.md. For anything beyond a
small tree, **delegate** — don't read everything yourself:

**First, cheap evidence (stack-neutral, no profile facts needed) to steer the fan-out:**
- `git log --format= --name-only --since='6 months ago' | sort | uniq -c | sort -rn | head` —
  churn hotspots: the files that change most are where entropy concentrates; they seed which
  subtrees to scan first.
- For a candidate module, `grep -rn` its public symbols across the tree to count call sites —
  that call-site count is the **leverage** number Phase 2 ranks on.
- Shallow clone or no history? Skip the churn step and rely on the agent fan-out below.

**Profile drift check (cheap, piggybacks on this periodic run).** `PROJECT.md` goes stale
silently as the codebase evolves — and every kit skill trusts it. Verify its load-bearing
facts against reality: the named layer/module directories still exist (`Glob`), the
test/lint commands still resolve (`--version` / `--help`, never a full run here), the listed
integrations still appear in the code. Report each divergence as a **Profile drift** row
(fact → reality, `path` evidence) and suggest the `PROJECT.md` correction — apply only on
user confirmation. Structural drift (renamed layers, new stack) → recommend `/update-kit`
re-adapt instead of piecemeal edits.

- **`arch-tracer`** agent — trace data flow & dependencies through each layer/module; report
  **layer violations** and dependency-direction breaks (imports pointing the wrong way,
  sibling-to-sibling coupling, domain logic reaching into I/O).
- **`deep-analyzer`** agent — for the densest/most-central modules, assess interface depth, leaky
  abstractions, conjoined methods, information leakage, god-objects.

Run several in parallel over disjoint subtrees; each is blind to the others, so collect and dedupe
their findings. Prefer **structured output**: pass the installed Finding Contract schema
(`.claude/schemas/finding.schema.json`) as the `schema` so N agents' findings merge mechanically
instead of by prose-parsing. Finders run in the **background** by default — launch the batch, keep
doing the cheap-evidence work above, and collect on completion notifications rather than idling.
**But no health verdict while a finder is outstanding:** the notification is queued and becomes a
turn only after the current one ends, so a run that keeps working and then writes its report never
receives it (`delegation.md`; measured 4 of 6 reports lost). Before the verdict, every finder's
output is in context or pulled with `TaskOutput` — an uncollected finder means its subtree is
**unscanned**, and the coverage line says so rather than reading as clean.
Ground every finding in `path:line` — an uncited smell is a guess.

**Loop until dry (unknown-size hunt).** Rot has no known count, so a fixed fan-out misses the
tail. At skill effort `high`, iterate: after each round, aim the next round's finders at the
subtrees and smells the previous round did NOT cover (churn list minus scanned, remaining layers),
and stop only when **2 consecutive rounds surface nothing new**. Dedup each round against
**everything already seen** (including candidates later refuted in Phase 2) — deduping only
against confirmed findings makes refuted ones reappear every round and the loop never converges.
At effort `low`, a single round over the highest-churn subtrees is acceptable — say so in the
report ("coverage: 1 round, top-churn only").

---

## Phase 2 — Rank the opportunities

**Verify before ranking — evidence-gate every ball-of-mud call.** A smell is a guess until
proven. Launch the `finding-verifier` agent on each Phase-1 candidate (batches of 3–4 in
parallel; its 3 lenses: real-today · blast-radius · prior-decisions). **Scale the verification
to the skill's effort**: at `low`, one verifier per finding (single vote); at `high`, findings
heading for a **HACK** verdict get the verifier's **panel mode** — 3 instances in parallel, one
lens each, majority decides, ties die (a HACK label sends someone to restructure code, so it
must survive an adversarial panel, not one skeptic's mood). Each candidate must clear
the gate: the churn/call-site evidence shows it's real today, `git log -p` on the module shows no
logged reason that makes the pattern intentional, and it isn't a **sanctioned exception** — an ADR
/ decision record, or a `paths`-matched boundary rule that explicitly blesses the seam. A blessed
pattern is intent, not mud. Drop REFUTED/STALE findings with a one-line reason — only CONFIRMED
findings enter the ranked table, so the user never triages a false positive or a re-litigated
decision.

Label each surviving finding with the shared quality verdict — **SHORTCUT** (bounded debt, schedule
it) or **HACK** (violates the architecture, fix before building on top) — as defined by the
`quality-auditor` agent. A **SOUND** module is not a finding; it never reaches this table.

Score each finding so the user spends effort where it pays off most. **Leverage** (how many callers
/ how much code gets simpler) against **cost** (how risky/large the change):

| Opportunity | Smell | Verdict | Leverage | Cost | Score |
|-------------|-------|---------|----------|------|-------|
| `path` — <module> | shallow / leaky / misplaced-seam / layer-violation / info-leak | SHORTCUT / HACK | high/med/low | high/med/low | ⭐ rank |

- **Leverage high** = many call sites simplify, a leaked decision gets owned, a hot interface
  shrinks, or a recurring bug class disappears.
- **Cost** = blast radius (callers touched), test coverage present, reversibility.
- Prioritize **high-leverage / low-cost** first; flag **high-cost** ones as "plan via `/prepare`",
  not quick refactors.

Present the ranked table, and **`Write` it as a durable markdown report** to the **Plans location**
from `PROJECT.md` (e.g. `<plans>/<YYYY-MM-DD>-arch-health.md`) so the findings aren't lost when the
session ends and you can re-run and compare later (its git policy follows `PROJECT.md` → Artifact
git policy). For a visual overview the user can scan, *optionally also* render an HTML version per
[REPORT.md](REPORT.md).

---

## Phase 3 — Pick one and grill it

The user chooses an opportunity (via `AskUserQuestion` if it's a real toss-up). Then **`/grill`**
through it: what *exactly* is shallow, what the deeper design looks like (apply
`/codebase-design` → DESIGN-IT-TWICE.md), what the new seam/interface is, the blast radius, and
whether tests exist to make the change safe. Don't restructure on a hunch — resolve the design
first.

If the deepening encodes a lasting decision (a new boundary, a chosen seam), record it via
`/domain-model` as an ADR so it isn't relitigated.

---

## Phase 4 — Route to the fix

| The chosen change is… | Route |
|-----------------------|-------|
| Small, mechanical, behaviour-preserving, in already-changed/local files | **`/refactor`** (applies + verifies via format/test) |
| Larger, cross-layer, or needs new abstractions/migrations | **`/prepare`** (design + impact + decomposition) → `/implement` |
| Missing test coverage that makes any change risky | **`/test`** first to pin behaviour, then refactor |

Hand off the grilled design as the input to that skill. Never apply the restructure here.

---

## Output

```
## Architecture Health — <scope>

### Ranked opportunities
| Opportunity (path) | Smell | Verdict | Leverage | Cost | Rank |

### Recommended next
- ⭐ <top opportunity> — <one-line why it's highest leverage> → route: /refactor | /prepare

### Layer-violation summary
- `path:line` — <violation> (per PROJECT.md dependency direction)

### Deferred / high-cost
- <opportunity> — <why it needs /prepare, not a quick refactor>

### Profile drift
- <PROJECT.md fact> → <reality, with path evidence> — <suggested correction | route: /update-kit>
  *(or "none — profile matches reality")*
```

---

## Hard rules

- **Propose, don't apply.** The fix goes through `/refactor` or `/prepare`→`/implement` — never
  edit code in this skill.
- **Cite `path:line`** for every finding; phrase it in the `/codebase-design` vocabulary.
- **Evidence-gate every verdict.** No SHORTCUT/HACK call without proof: call-site count, `git log`
  history, and a check that it isn't a sanctioned exception (ADR / `paths`-matched boundary rule).
  A blessed pattern is intent, not mud — leave it SOUND.
- **Rank by leverage, not by ease.** The point is the highest-impact deepening, not the easiest.
- **Facts from PROJECT.md.** Layers, dependency direction, and "where domain logic lives" come from
  the profile — don't impose a generic architecture.
- **Don't deepen for its own sake.** A correctly-simple leaf is not a finding (DEEPENING.md → "Not
  deepening").

## See also

- **`/codebase-design`** — the vocabulary and the smell/move catalog this scan runs on.
- **`/refactor`** — applies a small deepening + verifies. **`/prepare`** — plans a large one.
- **`/domain-model`** — record a structural decision as an ADR.
- **`/decompose`** — when a finding is service-sized ("this module wants to be its own
  deployable"), the split/stay decision lives there, not in a refactor.
- **`/revisit`** — when a smell traces back to a *recorded decision* (the sanctioned-exception
  check hit an ADR you think is stale), test the decision's assumptions there instead of
  relitigating it here.
- **`/distill`** — hunts *conventional* drift (competing patterns) where this skill hunts
  *structural* rot; run both periodically.
- **`quality-auditor`** agent — owns the SOUND / SHORTCUT / HACK verdict rubric these labels use.
