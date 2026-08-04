---
name: audit-security
disable-model-invocation: true
description: >-
  Orchestrating security audit — an OWASP-style sweep that ties together the project's
  security rule, the built-in /security-review, the security-reviewer agent, and /deps
  into one risk-tiered report with a deploy verdict. Covers secrets, injection
  (command/SQL/path), authorization, unsafe deserialization, and dependency trust.
  TRIGGER when: the user wants a security audit before a deploy, after adding an external
  integration or user-input surface, or as a periodic security review of the codebase.
  DO NOT TRIGGER when: the user only wants a diff/PR-level security review of their own
  changes (use the security-reviewer agent / built-in /security-review directly), or only
  a dependency/CVE audit (use /deps).
allowed-tools: Read, Grep, Glob, Bash, Agent
effort: high
---

# Security Audit: $ARGUMENTS

`$ARGUMENTS` scopes the audit: a file, a directory, or empty/`full` = the whole source
tree per `PROJECT.md` → Architecture.

This skill is the **orchestrator**, not another scanner. It sequences the pieces the kit
already ships and folds their output into one risk-tiered verdict:

- `rules/_generic/code.md` — the baseline every finding traces back to.
- Built-in **`/security-review`** — the deep vulnerability pass (do not reimplement it).
- **`security-reviewer`** agent — the read-only deep analysis, run per scope.
- **`/deps`** — the CVE/dependency audit (delegate; never duplicate here).

This skill **proposes** — it never edits code, rotates keys, or upgrades packages. It
reports; the user decides and acts.

---

## Phase 0 — Load profile

**Tooling preflight — one call, before step 1.** Some tools this skill relies on are **deferred**
by the harness: the session lists them by name only and loads their schemas on demand, so calling
one before it is fetched fails. Listing a tool in `allowed-tools` does **not** un-defer it. Issue
a single `ToolSearch` up front covering the whole run — `select:SendMessage,TaskOutput`
(continuing the same `security-reviewer` across loop-until-dry rounds instead of respawning,
collecting a backgrounded pass) — instead of one round-trip per discovery. A name already loaded
costs nothing to include; a schema discovered missing mid-run costs a turn.

1. Read `.claude/PROJECT.md` → **Stack** (language, framework), **Architecture** (trust
   boundaries, entry points, where untrusted input enters), and **Commands**. The source
   globs, entry points, and secret-loading convention all come from here — never guess them.
2. Read `rules/_generic/code.md` (the baseline) and `rules/_generic/observability.md`
   (shared secret-redaction stance). After Phase 1, read any `paths`-matched **stack
   security rule** (e.g. a `*-security.md` pack) for framework specifics.
3. **No profile yet?** If `PROJECT.md` is missing or still `TEMPLATE` (pre-`/bootstrap`),
   do not stop: prefer the root `CLAUDE.md` (always in context) when it carries the stack, source
   layout, and trust boundaries; otherwise infer them from the tree (manifests, lockfiles, entry
   points, env handling). State your assumptions at the top of the report, and proceed against the
   generic security rule plus `/security-review`. Note that stack-specific security checks are
   unavailable until `/bootstrap` runs.

The grep sweeps below are **language-neutral triage** — fast pointers to code worth a human
(or the agent's) closer look. Adapt the patterns to the stack's syntax from `PROJECT.md`;
substitute the real source glob for `<src>`. A grep hit is a lead, not a finding.

---

## Phase 1 — Secrets

Search for credentials, keys, and tokens hardcoded in source, config, or fixtures:

```bash
# Assignment of a literal to a secret-shaped name (tune keywords to the stack)
grep -rniE "(api[_-]?key|secret|password|passwd|token|access[_-]?key|private[_-]?key)\s*[:=]\s*['\"][^'\"]{6,}" <src> \
  | grep -viE "example|sample|placeholder|dummy|test|process\.env|os\.environ|getenv|config\("
```

Verify:
- All secrets load from env or a secret store — never a literal in code (`rules/_generic/code.md` → Secrets).
- `.env` / key material is git-ignored and absent from git history.
- Test/demo credentials are clearly marked and inert.

**Report `path:line` + the variable name only — never print the secret value** (redact to
first/last few chars). A secret that reached VCS is compromised: the fix is **rotate first,
then scrub history**, not delete-and-move-on. A confirmed live secret is a CRITICAL and
blocks the verdict.

---

## Phase 2 — Injection (command / SQL / path)

Untrusted input concatenated into a dangerous sink. See `reference/safe-patterns.md` for
the fix shape of each.

- **Command** — process/shell APIs invoked on a string built from input, or with a shell
  enabled. Safe shape: pass an argument vector, keep the shell off. `#command-injection`
- **SQL / query** — a query string interpolating input instead of using bound parameters.
  Safe shape: the driver's parameter binding, never string formatting. `#sql`
- **Path traversal** — a filesystem path opened from input without confining it to a base
  directory. Safe shape: resolve to a real absolute path, confirm it stays under the base,
  reject `..` and absolute escapes. `#path-traversal`
- **Template / eval** — input reaching an `eval`/exec/render-string sink.

```bash
# Triage — adapt the sink names to the stack (from PROJECT.md → Stack)
grep -rniE "shell\s*=\s*true|os\.system|popen|exec\(|eval\(" <src>          # command / eval
grep -rniE "execute\(.*(\+|%|\$\{|f['\"]|format\()" <src>                    # string-built query
grep -rniE "open\(|readfile|sendfile|createreadstream" <src>                 # path sinks — check the arg's origin
```

For each hit, trace whether the argument can carry untrusted input (Phase 0 boundaries).
No reachable untrusted path ⇒ it is a hardening note at most, or dropped.

---

## Phase 3 — Authorization & trust boundaries

Per `rules/_generic/code.md` → Authorization. Not a grep game — read the entry points
`PROJECT.md` → Architecture names and check:

- Every protected action verifies **authentication** (who) **and authorization** (may they,
  on *this* object) at the layer that owns the resource — not only in the UI/controller.
- Queries and mutations are **scoped to the caller's tenant/owner**; an id from the request
  is never trusted to already be in scope (IDOR).
- **Deny by default** — no rule matched ⇒ denied; the security decision **fails closed** on
  error, never silently allows.
- Outbound requests built from input allowlist host/scheme/port and forbid redirects to
  internal/metadata addresses (SSRF).

---

## Phase 4 — Unsafe deserialization & dangerous defaults

- Deserializing untrusted input with a format that can construct arbitrary objects or run
  code on load (native object serializers, unsafe YAML/XML loaders, arbitrary
  pickle/marshal). Safe shape: a data-only/safe loader, and never deserialize untrusted
  input with a code-capable format. `reference/safe-patterns.md#deserialization`
- Secrets or tokens reaching logs — cross-check `rules/_generic/observability.md`.
- Insecure defaults: debug/admin surfaces on in prod, TLS/cert verification disabled,
  verbose errors leaking internals, an over-broad CORS or permission default.

```bash
grep -rniE "pickle|marshal|yaml\.load\b|unserialize|readobject|xmldecoder" <src>     # deserialization
grep -rniE "(log|print|console)\.[a-z]*\(.*(password|secret|token|api[_-]?key)" <src> # secrets in logs
grep -rniE "verify\s*=\s*false|rejectunauthorized\s*:\s*false|debug\s*=\s*true" <src> # unsafe defaults
```

---

## Phase 5 — Dependency trust (delegate)

Do **not** re-audit packages here — CVE scanning and the safe upgrade path are `/deps`' job.

- Point the caller to run **`/deps`** for the full advisory audit (per-severity, direct vs
  transitive, expand→test→contract upgrade plan).
- In this report, note only what dependency *trust* posture you can see without a scanner:
  a committed lockfile present? security-sensitive deps pinned vs floating? obviously
  abandoned/unusual packages? Fold the rest in by reference to `/deps`.

---

## Phase 6 — Deep analysis (delegate)

For anything non-trivial, or when the scope is a whole subtree, hand the deep pass to the
tools built for it rather than eyeballing greps:

- Launch the **`security-reviewer`** agent on `$ARGUMENTS` — it runs the built-in
  `/security-review` and folds in the rule-based findings, read-only.
- Fold its findings into the tiered report below, de-duplicating against the Phase 1–4
  leads. Report each real issue **once**, attributed to its rule or concrete risk.
- Agents run in the **background** by default — launch them early (even before finishing
  the grep phases) and collect on notification. **Unless this skill is itself running inside
  an agent**, in which case that notification never arrives (`delegation.md`: 0 of 18 across
  the archive) — spawn with `run_in_background: false` and take the block. Prefer
  **structured output**: pass the installed `finding.schema.json`
  (`.claude/schemas/finding.schema.json`) so multiple agents' findings merge mechanically.
- **No deploy verdict while an agent is outstanding.** The notification is queued and only
  becomes a turn after the current one ends, so a run that keeps grepping, writes the report and
  finishes never receives it (`delegation.md`; measured 4 of 6 reports lost this way). Before the
  risk-tiered report: every spawned agent's findings are either in your context or pulled with
  `TaskOutput`. An uncollected scanner is an **unscanned surface**, and the report says so —
  a clean verdict over a lost report is the one failure mode this skill cannot have.
- **Loop until dry** (whole-tree scope, effort `high`): an audit has no known finding
  count. After the first pass, launch a follow-up round aimed at what the first round did
  NOT cover (entry points with no findings AND no evidence of scanning, categories that
  came back empty); stop when 2 consecutive rounds add nothing new. Dedup each round
  against everything already **seen** (including refuted leads), not just confirmed
  findings. At effort `low`, one pass is fine — state the coverage in the report.

---

## Phase 6.5 — Verify CRITICALs + completeness (before the verdict)

A CRITICAL here blocks a deploy — it must survive adversarial verification, and the
report must survive a completeness attack:

1. **Panel-verify every CRITICAL** (and HIGHs at effort `high`): spawn the
   **`finding-verifier`** in **panel mode** — 3 instances in parallel with
   *perspective-diverse* lenses suited to security claims: `correctness` (is the sink
   really reachable in current code), `does-it-reproduce` (can the attack path actually
   be traversed — trace input → sink), `prior-decisions` (isn't this a documented,
   compensated, or accepted risk). Majority decides; a finding that fails the panel is
   downgraded to a hardening note with a one-line reason, never silently dropped. At
   effort `low`, a single verifier per CRITICAL (still mandatory — an unverified
   CRITICAL never reaches the verdict).
2. **Completeness critic**: launch the **`completeness-critic`** agent on the draft
   report + the scope. Its gap list (entry point never scanned, checklist row silently
   skipped, category with zero findings and no scan evidence) becomes either another
   audit round or an explicit "not covered: …" section in the report — an audit that
   silently under-covers is worse than one that admits its bounds.

**Optional upgrade the *user* can run: this verification as a deterministic `Workflow`.** The
vote is already a fixed shape — N refuters per CRITICAL in parallel, majority decides, the
completeness critic as a final stage — and a script runs it with each verdict returned against a
`schema`, plus loop-until-dry rounds for the Phase 6 sweep. Two limits, both hard:
(1) **user-opt-in only** — it runs on the user's explicit ask and is never launched from this
skill, so name it in one line and run the agent panel above otherwise; (2) **read-only fan-out
only** — an audit qualifies because it reads source and returns *findings*, fixing nothing inside
the run; the deploy verdict (SECURE / NEEDS FIXES / DO NOT DEPLOY) is issued here, not by a
script. See `rules/_generic/delegation.md` → *Deterministic fan-out*.

---

## Output

Every reported issue carries `path:line` (from a file actually opened), a severity, and a
concrete attack scenario — who reaches the code with what input/privilege, and what they
get. A lead with no reachable attack path is a hardening note or is dropped.

```
## Security Audit — <target>

### Summary
- Risk level: CRITICAL / HIGH / MEDIUM / LOW
- Blocking issues: N   Total findings: N

### CRITICAL (block deploy)
- `path:line` — <issue>. Attack: <who + input → impact>. Fix: <concrete>. (source: rule | /security-review | agent)

### HIGH (fix before production)
- ...

### MEDIUM (fix soon)
- ...

### LOW / hardening
- ...

### Checklist
- [ ] Secrets: all from env/secret store, `.env` git-ignored, none in history
- [ ] Injection: no shell-string sinks, parameterized queries, confined paths
- [ ] Authorization: authn + authz at the owning layer, tenant-scoped, fail-closed
- [ ] Deserialization: no code-capable format on untrusted input
- [ ] Logging: no secrets/tokens in logs
- [ ] Dependencies: `/deps` run, lockfile committed, sensitive deps pinned
- [ ] Verification: every CRITICAL panel-verified (3 lenses, majority); completeness-critic
      gaps resolved or listed under "not covered"

### Not covered
- <scope the audit did NOT reach, from the completeness critic — or "none">

### Verdict: SECURE / NEEDS FIXES / DO NOT DEPLOY
```

End with one line: `X critical, Y high, Z medium — verdict: <…>`.

## Hard rules

- **Propose, never apply.** No edits, no key rotation, no upgrades — report so the user acts.
- **Never print a secret value** — `path:line` + name, redacted. A committed secret is
  compromised: rotate then scrub.
- **Don't reimplement** `/security-review` or `/deps` — orchestrate them.
- **Every finding traces** to `rules/_generic/code.md` (or a matched stack rule) or a
  real, reachable exploit — never a hunch.

## See also

- `security-reviewer` agent / built-in `/security-review` — the deep vulnerability pass this skill drives.
- `/deps` — dependency & CVE audit.
- `rules/_generic/code.md` — the baseline every finding traces to.
