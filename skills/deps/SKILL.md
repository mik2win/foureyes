---
name: deps
disable-model-invocation: true
description: >-
  Dependency & vulnerability hygiene — run the stack's vulnerability audit, summarize
  findings by severity, and propose pinning + a safe upgrade path. Reads the package
  manager and audit command from PROJECT.md; never auto-upgrades or commits.
  TRIGGER when: the user wants to audit dependencies, check for vulnerable/outdated
  packages, run `npm audit`/`bundler-audit`/`pip-audit`/`cargo audit`, or plan a safe
  dependency upgrade.
  DO NOT TRIGGER when: the user wants a code-level security review of their own code
  (use the `security-reviewer` agent / built-in `/security-review`), or wants to actually
  perform an upgrade they've already decided on.
allowed-tools: Read, Grep, Glob, Bash, AskUserQuestion
effort: medium
---

# Dependency Hygiene

Audit installed dependencies for known vulnerabilities and propose a safe response. This
skill **proposes** — it never edits manifests/lockfiles or upgrades anything. The user
decides.

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` → **Stack → Package manager** and **Commands**. The package
   manager determines the audit command; never guess it.
2. If `PROJECT.md` is missing or still `TEMPLATE`, fall back to the root `CLAUDE.md` (always in
   context) when it names the package manager / audit command — note you're running without a kit
   profile. Only if *neither* has them, run `/bootstrap` first.
3. Skim `rules/_generic/code.md` → *Dependency trust* for the principles this skill applies.

## Phase 1 — Resolve the audit command

Derive the audit command from the package manager. If `PROJECT.md → Commands` already names
an `audit` command, use that verbatim. Otherwise map from the package manager:

| Package manager | Audit command |
|-----------------|---------------|
| npm | `npm audit` |
| yarn (Berry) | `yarn npm audit` |
| yarn (classic) | `yarn audit` |
| pnpm | `pnpm audit` |
| bundler (Ruby) | `bundle exec bundler-audit check --update` (or `bundle-audit`) |
| pip / uv / poetry | `pip-audit` (or `uv pip audit`) |
| cargo | `cargo audit` |
| go | `govulncheck ./...` |

If the package manager isn't in the table, or the audit tool isn't installed
(`command -v` check fails), use **AskUserQuestion** to confirm the right command rather than
guessing. Note when an audit tool needs installing — propose, don't auto-install.

## Phase 2 — Run & summarize

- Run the resolved audit command from the repo root (read-only flags only — never `--fix`,
  `--force`, or anything that mutates the lockfile).
- Parse the output and summarize **by severity** (CRITICAL / HIGH / MEDIUM / LOW). For each
  advisory: the package, the vulnerable vs fixed version, and a one-line description of the risk.
- Separate **direct** dependencies (you can act on directly) from **transitive** ones (pulled
  in by a parent — note the parent that must move).

## Phase 3 — Propose (do not apply)

For each finding, recommend an action; do not perform it:

- **Pinning:** flag unpinned or floating ranges on security-sensitive packages; recommend a
  committed lockfile and explicit pins per `rules/_generic/code.md`.
- **Upgrade strategy — expand → test → contract:** add the fixed version alongside, run the
  project's **test** command (from PROJECT.md → Commands) to confirm nothing breaks, then drop
  the old version. Never blind-bump across a major version without this. The agent
  **proposes** these commands — the user runs them (code-publish policy: the agent never
  edits the manifest/lockfile or commits).
- **No fix available:** note mitigations (drop the dependency, restrict its input, or accept
  with a tracked exception) and surface it clearly rather than burying it.
- **Upstream has stopped:** a **direct** dependency whose upstream is archived, past its stated end
  of life, or superseded by a named successor is a HOLD, with the evidence cited (archive notice,
  EOL date, the successor's own migration note); the replacement routes through `/select-tech`.
  Never by age alone — a stable library with no reason to release is not a finding.

## Output

```
## Dependency Audit — <package manager>
Command: <audit command run>

### CRITICAL / HIGH
- <package> <cur> → <fixed> — <risk>. (direct | via <parent>). Proposed: <expand→test→contract | pin | mitigate>

### MEDIUM / LOW
- ...

### Pinning & strategy
- <unpinned/floating packages and the recommended pins>
```

End with one line: `X critical, Y high, Z medium, W low — N have fixes available.` If the
audit found nothing, say so and note when it was last run is unknown (advise scheduling it).

## See also

- `security-reviewer` agent / built-in `/security-review` — for vulnerabilities in *your* code.
- `rules/_generic/code.md` — the dependency-trust principles this skill enforces.
