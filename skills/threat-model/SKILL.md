---
name: threat-model
disable-model-invocation: true
description: >-
  Design-time threat modeling (STRIDE-lite) for a feature BEFORE it's built — map the new
  surface and trust boundaries, walk spoofing/tampering/disclosure/DoS/elevation per entry
  point, add abuse cases (IDOR, mass assignment, rate abuse), and land every accepted threat
  as a spec AC or plan step — not a wish.
  TRIGGER when: a spec/plan adds or changes external surface — a new endpoint/form/webhook,
  file upload, auth/authz change, a new integration or tenant boundary — and code hasn't been
  written yet; or the user says "threat model", "что тут может пойти не так по безопасности".
  DO NOT TRIGGER when: auditing EXISTING code (use /audit-security or the security-reviewer
  agent), or reviewing a diff (built-in /security-review).
allowed-tools: Read, Grep, Glob, Bash, WebFetch, AskUserQuestion, Write
effort: high
---

# Threat Model: $ARGUMENTS

## Principle

`/audit-security` finds the holes after they're built; this skill prices them **before**,
when a mitigation is one AC-line instead of a refactor. The method is an attacker's walk
over the *design*: every new entry point, every trust boundary crossed, every data class
touched — asked "how would I abuse this?" while it's still paper. Output is never advice —
every threat lands as a spec AC, a plan step, or a **named accepted risk** with the user's
sign-off.

## Phase 0 — Load context

Read `.claude/PROJECT.md` (Architecture, Integrations, Domain → roles), the installed
`code.md` + stack security rules, and the input artifact — an `/analyst` spec, a
`/prepare` plan, or a described feature (`$ARGUMENTS`). Missing/TEMPLATE profile → fall back to the
root `CLAUDE.md` (always in context) when it carries the architecture/integrations/roles (note
you're running without a kit profile); STOP for `/bootstrap` first only if *neither* has them. Skim
how the codebase *already* does auth/authz/validation
(grep the enforcement points) — mitigations must reuse the house mechanism, not invent a
parallel one.

## Phase 1 — Map the surface (the model)

For the feature, enumerate — a table each, cited against spec/plan items:

1. **Entry points** — endpoints, forms, webhooks, file uploads, CLI/jobs args, messages
   consumed. New AND changed.
2. **Trust boundaries crossed** — internet→app, app→DB, app→third-party, tenant→tenant,
   user-role→admin-surface. Each crossing is where validation/authz must live
   (`code.md`).
3. **Data classes touched** — credentials/tokens, PII, money/ledger, user content,
   internal config. Class sets the stakes.
4. **Actors** — the role matrix from the spec, **plus the two the spec forgot**: the
   *unauthenticated stranger* and the *authenticated-but-wrong-tenant/role user*. Most
   real-world holes belong to those two.

## Phase 2 — STRIDE-lite walk

Per entry point, five questions — pragmatic, not ceremonial (skip a row only with a
written "n/a — why"):

| Threat | The question at this entry point |
|---|---|
| **S**poofing | Who can call this pretending to be someone else? Is authn actually checked *here* (not just "somewhere upstream")? |
| **T**ampering | Which inputs reach state/queries/paths/templates? Mass assignment — can extra fields ride in? Is anything trusted that the client controls (IDs, prices, role fields, redirect URLs)? |
| **I**nfo disclosure | What does the response/error/log leak — other tenants' rows (IDOR), stack traces, existence oracles ("user not found" vs "wrong password"), secrets in logs? |
| **D**oS | What's unbounded — payload size, list length, fan-out, regex on user input, expensive query per anonymous request? Where's the rate/size limit? |
| **E**levation | Can a lower role reach a higher action via this path — direct object reference, missing per-object authz (not just per-endpoint), workflow-step skipping? |

Ground every YES/RISK in the artifact or codebase (`path:line` / spec item) — a threat
with no concrete avenue is noise; this table feeds engineers, not compliance.

## Phase 3 — Abuse cases (the attacker's user stories)

Three deliberate inversions beyond STRIDE:

- **The hostile power user**: scripts the feature at 1000× — what breaks, what gets
  scraped, what costs money (per-request LLM/API calls behind a free endpoint)?
- **The curious insider**: same-tenant low-role user exploring — what do IDs enumerate to,
  what do "hidden" UI actions actually enforce server-side?
- **The supply path**: what enters from the third-party side — webhook forgery (is the
  signature verified?), uploaded file content (parsed by what?), callback/redirect URLs.

## Phase 4 — Land the mitigations

Every threat gets exactly one disposition — the table is the deliverable:

| # | Threat (entry, STRIDE) | Impact | Disposition |
|---|---|---|---|
| T1 | … | … | **AC** — add AC-n to the spec (falsifiable: "role X requesting object of tenant Y observes 404") / **Plan step** — with `Verify:` line / **Accepted risk** — user-confirmed, with why |

- Mitigations reuse the house mechanisms found in Phase 0.
- **Accepted risks are the user's to accept** — one `AskUserQuestion` listing them with
  your recommendation, never silently self-accepted (`core.md`).
- Route the additions: back into the spec (`/analyst` numbering — append, never renumber)
  or the plan (`/prepare`); the artifact's stage gate should fail until the rows land.
- Offer to write the model to the Plans location (`<slug>-threat-model.md`) when the
  surface is big enough to outlive this session.

## Hard rules

- **Design-time only; read-only on code** — you change specs/plans, never source.
- **No threat without an avenue; no mitigation without a landing place** (AC / step /
  accepted-with-sign-off). A threat model whose findings changed nothing was theater.
- **The forgotten actors are mandatory**: unauthenticated + wrong-tenant walked at every
  entry point — that's where IDOR lives.
- **Per-object authz, not per-endpoint** — the elevation row always asks about the object.

## See also

- `/audit-security` — the post-build counterpart (code-level sweep); `security-reviewer`
  agent — diff-level check; `/analyst` / `/prepare` — where the mitigations land;
  `rules/_generic/code.md` — the always-on floor.
