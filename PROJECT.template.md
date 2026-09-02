# Project Profile

> Single source of truth about THIS project for all `.claude` skills and agents. Generated/updated by `/bootstrap`. Skills read this file at start instead of hardcoding any project facts. Keep it short and factual — it is referenced often. Replace every `<...>` placeholder; delete sections that truly do not apply.
>
> Status: `TEMPLATE` → bootstrap sets this to `ACTIVE` once filled.

```yaml
profile_status: TEMPLATE   # ACTIVE after /bootstrap
generated_by: bootstrap
schema_version: 1
```

---

## Identity

- **Name:** <project name>
- **Purpose:** <one line — what this project does>
- **Repo root:** <abs path or ".">
- **Git host:** <github | gitlab | none>

## Domain

> Feeds the `/analyst` interview and the `/grill` loop. Be concrete — this is the business context, not the tech.

- **Domain:** <e.g. logistics tracking / restaurant SaaS / internal billing>
- **Stakeholders / roles:** <e.g. end user, tenant admin, super-admin>
- **Core concepts / vocabulary:** <key nouns of the domain a newcomer must know>
- **Glossary (CONTEXT.md):** <path, e.g. `CONTEXT.md` at repo root — the living ubiquitous-language glossary maintained by `/domain-model`; `n/a` until the first term is recorded>
- **ADR location:** <e.g. `docs/adr/` — architectural decision records, also `/domain-model`; `n/a`>
- **Audience:** <technical (developer — full-register questions and reports) | non-technical (describes outcomes, not implementations — plain-language questions, agent owns all technical decisions) | mixed>. Sets the conversation register per `docs/audience-altitude.md`; artifacts stay full-fidelity technical regardless.

## Stack

- **Languages:** <e.g. Python 3.13 / Ruby 3.4 + TypeScript>
- **Frameworks:** <e.g. Rails 8.1 + Inertia + React / FastAPI / none>
- **Datastore:** <e.g. PostgreSQL (UUID PKs) / SQLite / none>
- **Key libraries:** <the few libraries whose conventions matter: e.g. pandas, Pydantic, Action Policy, Zustand>
- **Package manager:** <e.g. uv / yarn (npm forbidden) / bundler>

## Commands

> Exact shell strings. Skills run THESE, never guess. Leave `n/a` if none.

| Key             | Command                          |
|-----------------|----------------------------------|
| install         | `<e.g. uv sync / yarn install>`  |
| run             | `<e.g. uv run cli.py / bin/dev>` |
| test            | `<e.g. make test / bundle exec rspec>` |
| test:targeted   | `<run a single file/dir, e.g. pytest {path} / rspec {path}>` |
| lint            | `<e.g. make lint / rubocop>`     |
| format          | `<e.g. ruff format / prettier --write {path}>` |
| typecheck       | `<e.g. mypy / tsc --noEmit / n/a>` |
| build           | `<e.g. yarn build / n/a>`        |
| deploy          | `<e.g. make push / n/a>`         |
| browser-drive   | `<e.g. uv run --with playwright python {script} / npx playwright test {path} / n/a>` |
| remote-probe    | `<read-only, e.g. curl -fsS https://<host>/healthz / ssh <host> 'systemctl is-active <svc>' / n/a>` |

> **The last two are the verification drives** — `/prepare` Phase 6.4 writes an epic's `## E2E verify` block against them and `/close-epic` executes it, so they must be *exact*, not "run playwright somehow". Record the environment facts the command needs (interpreter, cached browser build, host alias) here rather than letting each session rediscover them. `browser-drive` is how a **UI** surface is driven end-to-end; `remote-probe` is how a **deployed** surface is inspected — keep it **read-only** (a probe never deploys, restarts, or mutates the remote; that is `deploy`'s job and the agent only suggests it). `n/a` is a real answer for a project with no browser or no remote, and it is what tells a close-out to say "no runtime surface" instead of manufacturing a drive.

## Architecture

> The layer/module model and dependency direction. Skills use this to place code and to detect violations. Describe what is true, not an ideal.

- **Structure model:** <e.g. 5-layer (core→domain→services→infra→entry) / FSD / bounded contexts / flat>
- **Layers / modules:** <list with one-line responsibility each>
- **Dependency direction:** <e.g. downward only; siblings don't import siblings>
- **Where domain logic lives:** <e.g. service objects in app/services/<context>/>
- **Where NOT to put logic:** <e.g. no I/O in domain layer; no business logic in controllers>
- **Canonical exemplars:** <for each recurring kind of extension, the one file/directory to mirror — e.g. adapters: `src/adapters/<name>/`; CLI commands: `cli_commands/_report.py`. `n/a` if this project has no repeating shape. Used by `/scaffold` and `/audit-quality`.>
- **Wiring / registration points:** <where a new artifact of that kind must be registered (registry file, composition root, plugin manifest, DI wiring) **and the command that proves the registration took** — `<cli> --help`, a list subcommand, a route dump. `n/a` if nothing needs registering.>

## Rules

> Filled by bootstrap. Always-on generic rules + selected stack packs (reconciled with this project). Skills load the applicable subset by `paths`.

- `rules/_generic/` — always on (code-quality, exception-patterns, testing, comments, observability, security, boundary-validation, external-api-integration)
- <e.g. rules/rails-*.md, rules/fsd.md — installed stack packs>

## Integrations

> External services this project talks to + their official doc URLs (used to seed the WebFetch allowlist in settings.json and the `/prepare` external-service check).

| Service        | Docs URL                         |
|----------------|----------------------------------|
| <e.g. Stripe>  | `<https://...>`                  |
| <e.g. Sentry MCP — optional> | `<https://docs.sentry.io/product/sentry-mcp/>` |

> **Error-tracking MCP (optional, not bundled):** a Sentry (or equivalent) MCP server lets `/diagnose` read production errors/issues directly instead of guessing from a stack trace. The kit does not ship the server — wire it yourself: add the MCP server to `.mcp.json`, then allowlist its tools and the docs domain above. See `rules/_generic/observability.md` for the logging/error discipline that feeds it.

## Plans / backlog

- **Plans location:** <e.g. .claude/plans/ — YYYY-MM-DD-<slug>.md>
- **Backlog / decomposition location:** <e.g. _backlog/ or backlog/<task>/>
- **Archive on done:** <e.g. _backlog/realised/ or n/a>
- **Issue tracker:** <local — markdown issues from `/to-issues`>
- **Issues directory:** <e.g. `_backlog/issues/` — `NNNN-<slug>.md`, the local issue tracker>
- **Small-debt register:** <e.g. `_backlog/small-debt-register.md` — one path-keyed row per verified, zero-consequence fix; created from `skills/close-epic/assets/small-debt-register.md` on first use, or `n/a` if the project keeps such rows in ledger clauses only>
- **Triage labels:** <the canonical `/triage` state machine, e.g. `needs-triage → ready → in-progress → done`, plus `blocked`>

## Artifact git policy

> Whether each kind of agent-generated artifact is kept **local** (gitignored — never pushed) or **committed** (shared in the repo). **The user chooses per category during `/bootstrap`**, with the trade-off explained. The agent never runs `git add`/`commit` regardless — this only controls what `.gitignore` excludes, so anything marked local cannot be pushed by anyone. `/bootstrap` appends the **local** locations to the project `.gitignore` (after confirmation). In each Policy cell below, the **first** option is the recommended default — bootstrap resolves it to one value.

| Artifact (skill) | Location | Policy |
|------------------|----------|--------|
| Briefs (`/discover`), specs (`/analyst`), plans & decomposition (`/prepare`), PRDs (`/to-prd`) | <plans / backlog location> | <local \| committed> |
| Issues (`/to-issues`, `/triage`) | <issues directory> | <local \| committed> |
| Handoff docs (`/handoff`); spike / arch-health / distill / decision-revisit / decomposition reports; grill alignment summaries | <plans / backlog location> | <local \| committed> |
| Glossary `CONTEXT.md` + ADRs (`/domain-model`) | <repo root / docs/adr/> | <committed \| local> |

## Deploy mapping

> Which kinds of change require which deploy command. Skip if no deploy step.

| Change touches…           | Action          |
|---------------------------|-----------------|
| <e.g. app code>           | `<make push>`   |
| <e.g. config only>        | `<make push-config>` |
| <e.g. local-only modules> | none            |

## Security / VCS policy

> Controls what the agent may run and what code may leave the machine. Set during `/bootstrap`; enforced by `settings.json` (`deny`) + `hooks/guard-bash.sh`. Web search/fetch for research and implementation stay available — this governs *publishing code*, not reading the web.

- **Code-publish policy:** <suggest-only (default — agent never runs `git add`/`commit`/`merge`/`push`, only outputs the command) | relaxed: <which commands the agent may run, e.g. local commit but never push>>
- **Forbidden commands:** <anything the agent must never run — e.g. a deploy/publish CLI, `scp`/`rsync` to a remote, a package-publish command; these are denied in settings + blocked in guard-bash; `n/a`>
- **Egress note:** <e.g. "web search allowed; no proprietary code in external API calls"; defaults n/a>

## Conventions notes

> Anything else a skill should respect that isn't in a rules file: e.g. "UI text in Russian, keys from locale files", "no README files", "commit prefix CRM-XX", "comments only for WHY".
