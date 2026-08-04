---
name: distill
disable-model-invocation: true
description: >-
  Pattern mining — surface the codebase's recurring implicit conventions (error handling,
  construction, data access, naming, test shape…), verdict each as BLESS / UNIFY / BAN /
  DEEPEN with cited occurrences, then install the verdicts where agents actually read
  them: project rules, CONTEXT.md, reference examples. Makes the implicit explicit so
  generated code copies the best pattern in the repo instead of the most frequent one.
  TRIGGER when: the user wants to extract/codify the codebase's conventions, "make the
  code consistent", "what patterns do we have", "turn how we do X into a rule", or after
  inheriting a codebase whose house style exists only in the code.
  DO NOT TRIGGER when: hunting rot/shallow modules (use /arch-health), applying cleanups
  to a diff (use /refactor), executing an already-decided mass migration (use /sweep), or
  writing the initial profile for a fresh project (use /bootstrap).
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Agent
effort: high
---

# Distill Patterns: $ARGUMENTS

`$ARGUMENTS` optionally scopes the mining to a subtree or a dimension ("error handling in
the API layer"); empty = the whole codebase, all dimensions below.

## Principle

Every codebase teaches by example — and its next contributor is an agent that learns the
house style from whatever code it happens to read. If three error-handling styles coexist,
generated code picks one at random; if the dominant example is bad, **every generated line
copies the rot forward**. Consistency isn't aesthetics: it's the difference between a
codebase that compounds and one that decays with each addition.

This skill closes the loop: **mine** the recurring patterns actually present, **verdict**
each one deliberately instead of letting frequency decide, and **install** the verdicts
where they change behavior — always-on rules, `CONTEXT.md`, reference examples. The kit's
rule packs carry the *stack's* conventions; this skill extracts the *project's own*, which
no pack can know.

It decides and codifies. Code changes (unification, deepening) route out.

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` — **Architecture**, **Conventions**, **Plans location**.
   Missing or `TEMPLATE` → fall back to the root `CLAUDE.md` (always in context) when it
   carries those facts, proceeding on it and noting you're running without a kit profile;
   only if *neither* has them, **STOP**, run `/bootstrap` first.
2. Read the installed `.claude/rules/*` (generic + stack packs) — what's already codified
   is not re-mined; a mined pattern that *contradicts* an installed rule is a finding of
   its own (the rule is aspiration, the code is fact — the user decides which bends).
3. Read `CONTEXT.md` if present — patterns get named in the project's language.

## Phase 1 — Mine (fan out)

Mine along dimensions, one finder agent per dimension over the scope (parallel,
background; pass `.claude/schemas/finding.schema.json` for mergeable output):

error handling & propagation · construction/wiring (DI, factories, composition root) ·
how modules address each other (import shapes, layering idiom) · data access · validation
placement · naming & file organization · test structure (arrange/act/assert idiom,
fixtures, fakes-vs-mocks) · async/concurrency idiom · logging & observability · config
access · dynamic dispatch & metaprogramming (verdict against
`rules/_generic/code.md`: a declared, enumerable DSL seam is BLESS material;
scattered runtime name-construction is BAN with the static replacement — registry table
or committed codegen — named).

Each finder reports *pattern candidates*: a recurring shape with **every occurrence cited
`path:line`**. The floor is **3 occurrences** — below that it's an incident, not a
convention (report 2-site near-patterns separately as "emerging", no verdict). For each
candidate also report the **counter-occurrences**: sites doing the same job a different
way. Frequency counts come from `grep -c`-style evidence, not impression.

## Phase 2 — Verdict each pattern

Frequency describes; it does not prescribe. For each mined pattern, decide:

- **BLESS** — dominant and good: codify it. The best in-repo occurrence becomes the
  worked GOOD example.
- **UNIFY** — 2+ competing conventions for the same job (the *fork tax*: every reader
  and every generation pays it). Pick the winner **with the user** (`AskUserQuestion`),
  on evidence: which the stack rules favor, which the newer code uses, which is deeper
  per `/codebase-design`, migration cost each way. Codify the winner; route the
  migration of the loser's sites to `/sweep`.
- **BAN** — dominant but harmful: codify the *replacement*, never a bare prohibition — a
  ban without a named alternative just breeds a third variant. Route existing sites to
  `/sweep` (mechanical) or `/arch-health` (structural).
- **DEEPEN** — a copy-paste family: the same logic re-implemented with variations wants
  to be one deep module (`/codebase-design`). Route to `/refactor` (small, local) or
  `/prepare` (cross-cutting).

**Intent gate before any BAN or UNIFY-against verdict** (`core.md`: surprising
code is load-bearing until proven decorative; your prior for "idiomatic" is the training
mean, not this repo): check `git log` on representative sites and `docs/adr/` for a
reason the pattern is deliberate. A **sanctioned exception** — an ADR or a rule that
blesses it — is intent, not rot: leave it, or route the disagreement to `/revisit`.
Weird-but-consistent beats familiar-but-foreign.

## Phase 3 — Install (with confirmation)

Nothing lands without the user confirming the batch. Placement follows
`/writing-skills`' altitude call — **always-on context is precious**:

- **Rule** (`.claude/rules/<name>.md`, `paths:`-scoped frontmatter): the invariant only —
  a few imperative lines plus ONE GOOD / ONE BAD example **taken from this repo**
  (`path` cited). Must-apply-on-every-matching-edit things only.
- **Reference skill** (`.claude/skills/<name>-conventions/SKILL.md`, on-demand): the heavy
  version — many worked examples, edge cases — when the rule would otherwise bloat.
- **`CONTEXT.md`** via `/domain-model`: when the pattern names a domain concept.
- **Scaffold / codemod**: a BLESSed *structural* pattern may install as a committed
  generator template (greppable codegen, per `rules/_generic/code.md` — never
  runtime magic); a UNIFY/BAN verdict hands `/sweep` a ready codemod spec (the FROM → TO
  pair + suggested tool), not prose.
- **Report**: `Write` the full inventory to the Plans location
  (`<plans>/<YYYY-MM-DD>-distill.md`) so verdicts survive the session (git policy per
  `PROJECT.md` → Artifact git policy).

Verify each installed rule's `paths:` glob actually matches the intended files (`Glob`
it). Project-specific rules land in the project's `rules/`, never back into kit packs.

## Output

```
## Pattern Inventory — <scope>

| Pattern | Dimension | Sites (for/against) | Verdict | Installed as | Route |

### Blessed & installed
- <pattern> — rule `rules/<name>.md` (exemplar: `path:line`)

### Unified (winner chosen)
- <job>: <winner> over <loser> (N vs M sites) — migration → /sweep

### Banned (replacement named)
- <pattern> → <replacement> — sites → /sweep | /arch-health

### Deepening candidates
- <family> (N variants) → /refactor | /prepare

### Emerging (< 3 sites, no verdict) · Contradictions with installed rules
```

## Hard rules

- **3+ cited occurrences** or it isn't a pattern. Every count grounded in search output.
- **Frequency never auto-wins.** Dominant-and-bad gets banned; the verdict is a decision,
  not a tally.
- **Intent gate before banning.** Check git history and ADRs; sanctioned exceptions
  stand (disagreement → `/revisit`).
- **Every BAN names its replacement.**
- **Install only with confirmation**, at the right altitude — lean always-on rules,
  heavy reference on-demand.
- **Codify here, migrate elsewhere.** Site changes go to `/sweep` / `/refactor` /
  `/prepare` — never applied in this skill.

## Cross-reference

- **`/sweep`** — executes a UNIFY/BAN migration mechanically, with inventory + re-scan.
- **`/arch-health`** — hunts *structural* rot; this skill hunts *conventional* drift.
  Complementary periodic scans.
- **`/codebase-design`** — the depth vocabulary behind DEEPEN verdicts.
- **`/refactor`** — applies small deepenings; reads the rules this skill installs.
- **`/revisit`** — where a mined pattern collides with a recorded decision.
- **`/retro`** — folds *process* lessons into rules; this skill folds *code* patterns.
- **`/writing-skills`** — the rule-vs-skill altitude call Phase 3 follows.
