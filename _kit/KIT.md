# feature-flow kit — manifest

Portable `.claude` set: a stack-agnostic feature pipeline (**discover → analyst →
prepare → implement → review/refactor/diagnose/test**, with an optional `/spike`
for quick hypothesis checks) plus a `/bootstrap` adapter that tailors it to any
project. Built to be dropped into a new project's `.claude/` folder and adapted
with one command.

## Design principle

Skills carry **only invariant workflow logic**. Every project fact (stack, paths,
commands, layers, domain, integrations) lives in one place: **`.claude/PROJECT.md`**.
Skills read that profile at start. Porting = copy the kit + run `/bootstrap`, which
fills the profile and installs project-specific rules — instead of editing skills.

## Layout

| Path | Kind | At install |
|------|------|-----------|
| `skills/bootstrap/` | adapter | invokable as `/bootstrap` (the "optimizer"); backs up before writing, asks keep/rollback, then cleans up |
| `skills/teardown/` | adapter | invokable as `/teardown` — clean up build-time leftovers, or uninstall & restore the pre-kit state |
| `skills/update-kit/` | adapter | invokable as `/update-kit` — pull a NEWER kit version into an already-bootstrapped project: 3-way merge against `.kit-manifest.json`, then re-adapt inline |
| `skills/{idea,discover,analyst,prepare,spike,prototype,select-tech,onboard,api-design,threat-model,implement,scaffold,code-review,audit-quality,refactor,diagnose,test,test-spec,tdd,perf,arch-health,decompose,revisit,distill,clean-mvp,sweep,audit-security,deps,rollout,deploy,preflight,incident,retro,handoff,grill,grill-with-docs,domain-model,codebase-design,to-prd,to-issues,triage,epic-status,close-epic,which-skill,prompt-master,writing-skills}/` | GENERIC | copied as-is (`audit-quality` = scoped SOUND/SHORTCUT/HACK architecture audit behind an evidence gate, with a phased refactor plan; the `quality-auditor` agent preloads it as its rubric · `deploy` = cheapest-sufficient deploy command per `PROJECT.md` → Deploy mapping, suggested as text, never run · `scaffold` = add a new module/component/command modelled on the profile's canonical exemplar, then prove every registration point with a command (the silent-failure class: a load-bearing side-effect import that never ran raises nothing — the artifact is just absent from `--help`) · `idea` = plain-language front door for non-technical users · `handoff` = snapshot session state · `select-tech` = library/framework/build-vs-buy selection with hard-case probe + adapter-seam contract · `onboard` = unfamiliar-repo orientation (run-first, traced flow, churn archaeology) · `api-design` = public-contract design with consumer's-eyes pass · `threat-model` = design-time STRIDE-lite, mitigations land as ACs/steps · `perf` = measurement-first optimization, budget-gated · `decompose` = monolith vs modular monolith vs service extraction, per-boundary STAY/MODULARIZE/EXTRACT verdict ("extract the seam before the service") · `revisit` = re-audit past decisions by testing their load-bearing assumptions against today (HOLDS/STRAINED/BROKEN, anti-relitigation gate) · `distill` = mine the repo's implicit conventions → BLESS/UNIFY/BAN/DEEPEN verdicts installed as project rules/CONTEXT.md · `rollout` = staged strategy for risky/irreversible changes (expand-contract, strangler, flags/canary) · `preflight` = release gate · `incident` = production-fire discipline, mitigate-first inversion of `diagnose` · `retro` = learning loop over deviation reports · `sweep` = batched mass migration) |
| `agents/*.md` | GENERIC | copied; bootstrap prunes irrelevant ones (keeps generic reviewers: `code-reviewer`, `security-reviewer`, the verification pair `finding-verifier` + `completeness-critic`, `plan-challenger` — `/prepare`'s pre-implementation challenge gate depends on it — and `idea-skeptic`, the same adversarial move one stage earlier: it attacks an *idea* on economics/supply/claim-honesty/measurability before `/idea` or `/discover` queues it, where `plan-challenger` attacks a *plan*; the skills' quality gates depend on them all). Per-agent `model:`/`effort:` frontmatter encodes depth (verifiers high, mechanical writers medium); `memory: project` agents follow `rules/_generic/memory.md` |
| `rules/_generic/*.md` | GENERIC | copied as-is — **15 files**, scoped by `paths:`, not all always-on. **Always-on (no `paths:`):** `core.md` alone — evidence tiers, done-is-external + unhappy-path floor, decision/reversibility pricing, competence-boundary routing to the right agent/spike/user, the hack tripwire, honest reporting. **Code-scoped** (`paths: "**/*"`, fire on file work): `code.md` (static navigability — one symbol = one exact-name-searchable definition site; comments; boundary validation; security), `code-quality.md`, `testing.md`, `exception-patterns.md`, `resilience.md`, `observability.md`, `service-layer.md`, `domain-events.md`, `external-api-integration.md`. **On-demand, authoring-scoped:** `delegation.md` + `memory.md` (`.claude/agents/**`, `.claude/skills/**` — fire when authoring agents/skills, not when a session merely spawns one), `planning-artifacts.md` + `parallel-wave-execution.md` (plan/spec/backlog paths — the Artifact-Continuity Contract, and the in-flight wave contract a concurrent session honours; the decomposition-time templates for the latter live in `skills/prepare/reference/`), and `sql.md` (SQL, migration, model, repository and query paths — engine-independent index ownership, plan reading, keyset pagination, read-check-then-write, natural keys; the stack pack carries the engine, and `/bootstrap` narrows its template globs to the project's DB directories). The 2026-08-01 tier cut folded nine former standalone rule files into `core.md` and `code.md` — each merged rule's `description:` frontmatter records exactly what it absorbed, so the provenance is greppable at the source rather than duplicated here. Their long-form treatments are **documentation, not rules** — see the `docs/` row |
| `docs/*.md` | GENERIC | copied — deep-dives the rules and skills point at, loaded on demand and never always-on: `self-knowledge.md` (author blindness, regression-to-the-mean, keep-the-homework mechanisms), `decision-craft.md` (doors, cheapest killing probe, pre-mortem), `audience-altitude.md` (conversation register per PROJECT.md → Audience), `observability.md`, `prompt-patterns.md`, `agent-teams.md`, `agent-failure-modes.md`, `working-with-agents.md`, `claims-audit-patterns.md` (how prose about the code goes false — the long form of `/audit-quality` Check 11) |
| `hooks/*.sh` | GENERIC | copied; bootstrap wires commands from profile. `sessionstart.sh` = per-session orientation banner (branch/dirty-state + bootstrap-configurable regions); `skill-hint.sh` = UserPromptSubmit routing hint, opt-in via `settings.skill-hint.example.json`, optional non-English synonym map (`skill-hint.synonyms.ru.example`); `format-file.sh` = PostToolUse formatter dispatch, command comes from the profile; `guard-secrets.sh` = warn-only secret scan; `precompact.sh` = re-injects the context-preservation checklist on compaction; `subagent-stop.sh` = warn-only Finding Contract check on subagent reports; `lint-board.sh` = PostToolUse board check after an edit to a board or a plan it cites, path-filtered in shell so ordinary edits never start an interpreter, off unless `/bootstrap` wires it; `guard-bash.sh` = reconciled with built-in destructive-command protection (kit keeps the publish policy + what built-ins don't cover); `verify-stop.sh` = opt-in, OFF-by-default non-blocking lint/test gate (enable by merging `settings.stop-gate.example.json`) |
| `schemas/finding.schema.json` | GENERIC | copied to `.claude/schemas/` — the Finding Contract as JSON Schema; orchestrating skills pass it to fan-out finders for structured, mechanically mergeable output |
| `output-styles/review.md` | GENERIC | copied as-is |
| `tools/lint-{board,refs}.py` | GENERIC, conditional | copied to the project's `tools/` when they have work to do (`/bootstrap` Phase 5, step 5a). `lint-refs.py` = repo paths cited by `CLAUDE.md` and `.claude/` that no longer exist, with a baseline for the deliberate ones; step in `/preflight`. `lint-board.py` = a wave board's mechanical half (`Owns` overlap between rows that may run concurrently, dangling deps, cycles, row↔plan status drift), only for a wave-structured backlog; becomes the `epic:status` command. Both stdlib-only and report-only. `tools/validate-kit.py` is NOT copied — it validates the kit itself |
| `PROJECT.template.md` | contract | bootstrap → `.claude/PROJECT.md` |
| `settings.template.json` | contract | bootstrap → `.claude/settings.json` (clean JSON, `$schema`, no comment keys) |
| `settings.stop-gate.example.json` | optional | merge into `settings.json` to enable the verify-on-stop gate |
| `settings.skill-hint.example.json` | optional | merge into `settings.json` to enable the `UserPromptSubmit` skill-routing hint |
| `settings.notifications.example.json` | optional, macOS | merge into `settings.json` for desktop notifications on `Notification` / `Elicitation` / `Stop` (`osascript`) — deliberately **not** in the main template, which stays OS-neutral |
| `CLAUDE.snippet.md` | contract | bootstrap merges into project `CLAUDE.md` |
| `_kit/rules-library/<stack>/` | RULE PACKS | bootstrap selects + reconciles → `rules/` |
| `_kit/templates/commands/*.md` | scaffolds | bootstrap installs `commit`/`pr`/`mr` |
| `_kit/KIT.md` (this file) | build-time only | removed at cleanup |

`_kit/` and `*.template.*` are **build-time only** — `/bootstrap` removes them at the
cleanup step, leaving a clean project `.claude/`.

`/bootstrap` also writes `.claude/.kit-manifest.json` — a content-hash baseline of the persistent
kit files (skills, agents, generic hooks/rules, output-styles, docs). It is **local state**, not
build-time: it persists so `/update-kit` can 3-way merge a future kit version against it without
clobbering local adaptations (works even when `.claude/` is gitignored). Each hash is the file **as
the kit shipped it**, never the adapted copy, and an `excluded` array lists kit paths the project
removed on purpose so no update re-adds them.

## How to use

1. (Existing project) back up first so you can fully restore:
   `cp -r <project>/.claude <project>/.claude.bak` and `cp <project>/CLAUDE.md <project>/CLAUDE.md.bak` (if present).
2. Copy the kit's contents into the target project: `cp -r foureyes/. <project>/.claude/`
   (or move it there).
3. Open the project in Claude Code and run `/bootstrap`. It backs up the files it touches,
   then at the end asks **keep or roll back** before cleaning up build-time files.
4. Answer the stack/domain questions and the reconciliation questions.
5. Smoke-test: `/analyst` then run the profile's `test` command.

To pull a **newer kit version** into this project later, drop it into `.claude/.kit-incoming/`
(or pass its path) and run `/update-kit` — it 3-way merges against `.kit-manifest.json` and
re-adapts in one pass, instead of re-copying by hand (`skills/update-kit/`).

To remove the kit later, run `/teardown` — it cleans up leftovers, or fully uninstalls and
restores the pre-kit backup (`skills/teardown/`).

## Hook & permission configuration (`settings.json`)

**The warn-not-block contract.** A kit hook **warns and exits 0**. Blocking — `exit 2` or
`permissionDecision: "deny"` — is allowed only on an *irreversible* action, and the kit ships
exactly one such case: `guard-bash.sh`. Everywhere else a false positive costs more than the
miss it prevents, so `guard-secrets.sh`, `verify-stop.sh`, `subagent-stop.sh` and `skill-hint.sh`
surface a `systemMessage` and get out of the way. Write a new hook against this contract, and
when a proposed hook can only work by blocking, that is a reason to reject the hook, not to
weaken the rule.

Three per-hook-entry fields the template does not use but every bootstrapped project should know
about — they turn a coarse `matcher` into a precise, quiet, non-blocking hook:

| Field | What it does | When to reach for it |
|-------|--------------|----------------------|
| `"if"` | A second, **tool-input-aware** condition on a single hook entry, written like a permission rule: `"if": "Edit(src/**/*.py)"`. The `matcher` selects the tool; `if` selects the *target*. | A formatter or guard that must fire only for one path/extension. Without it the hook runs on every `Edit` and has to re-derive the path itself. Project-specific by nature — the kit does **not** ship one in the template; `/bootstrap` adds them from the profile. |
| `"statusMessage"` | The line shown in the UI while the hook runs, instead of the raw command. | Any hook slow enough to be noticed. The template sets one on `format-file.sh`. |
| `"async": true` | Fire-and-forget: the turn does not wait for the command, and its exit code is ignored. | Notifications and other side effects (see `settings.notifications.example.json`). **Never** on a guard — an async hook cannot block, so `exit 2` from it does nothing. |

**Hook script paths: always `$CLAUDE_PROJECT_DIR/.claude/hooks/…`.** Not a bare relative path
(it silently assumes the hook's working directory is the project root — true in the common case,
not guaranteed, and false the moment the session runs from a git worktree or a subdirectory) and
never an absolute one (breaks on the next machine, and in every worktree). The generic hooks
defend themselves too — `format-file.sh` opens with `cd "${CLAUDE_PROJECT_DIR:-.}"` — but that
defense runs *after* the interpreter has already resolved the script path, so the invocation in
`settings.json` is the part that has to be right.

**Checking a hook is actually registered — the file being present is not the hook being on.**
A hook that never registered is indistinguishable from a hook working silently, and most kit
hooks are silent by design. Verify after `/bootstrap` and after `/update-kit`:

1. **`/hooks`** — the menu lists, per event, a hook count and a source label (`Project Settings` /
   `Local Settings` / `User Settings` / `Plugin Hooks`). For a copy-in kit that is the precise
   answer: count ≠ 0 **and** the label is the file you wrote to. Caveat: `/hooks` is **TUI-only** —
   in the VS Code extension and in non-interactive runs it answers *"isn't available in this
   environment"*, so it cannot be the only check.
2. **Fallback, when `/hooks` is unavailable — provoke output, then look for the record.** Trigger
   the hook with something it must speak on (edit a file for `PostToolUse:Edit`, start a session
   for `SessionStart`), then grep the session transcript under `~/.claude/projects/<slug>/*.jsonl`
   for an `attachment` whose `type` is `hook_success` / `hook_system_message` /
   `hook_additional_context`. The record carries `hookEvent`, `hookName` **and `command`** — the
   resolved script path, which answers "did *our* file register" more precisely than the source
   label does. Two measured limits: the harness records **only hooks that produced output** (a
   silent success leaves no trace, so a quiet hook must be provoked into speaking), and for the
   `Stop`/`SubagentStop` family the fallback is blind **by mechanism, not by sampling**. Measured
   2026-08-04 by instrumenting `subagent-stop.sh` in a consumer project: the hook fires on a
   synchronous, a background *and* a nested subagent (both levels), receives the report in
   `last_assistant_message`, and emits its `systemMessage` — and that message reaches **neither the
   transcript nor the orchestrator**. Three runs, three warnings emitted, zero `hook_success` and
   zero `hook_system_message` records, while `SessionStart` wrote both in the same sessions; asked
   directly, the orchestrator reported only the token-usage notice. So a `Stop`/`SubagentStop` hook
   cannot be verified from the transcript and cannot advise the session either — treat its output
   as a local side effect (write a file, exit non-zero) or do not rely on it. `/hooks` or a
   deliberately loud test hook is the only registration check for these two events.
3. A registry line in `--debug` output has been reported but is **not** in the documented
   contract and was not observed on 2.1.220 — treat it as version-unstable, never as a citable
   constant. The debug session must be started as `claude --debug -p "<prompt>"`; piping
   `claude --debug` into `head` puts the CLI in `--print` mode and never starts a session,
   producing a false negative.

**Merging the optional examples.** `settings.stop-gate.example.json` and
`settings.notifications.example.json` both write to `Stop`, which is an **array** — merge means
appending an entry, not replacing the key. Taking both gives one `Stop` array with two entries;
overwriting silently drops the verify gate.

**Permission allow-lists and the `cd` prefix.** A session often prefixes a read-only command with
a directory change (`cd src && rg foo`), and `Bash(rg *)` does **not** match that string — the
whole command line is matched, prefix included. So for every read-only command worth allowing,
allow the prefixed spelling too: `Bash(cd * && rg *)` alongside `Bash(rg *)`. Do this only for
genuinely read-only commands; a `cd * && <anything>` wildcard would allow far more than intended.

## Rules library

Stack rule packs live in `_kit/rules-library/` (`ruby`, `rails`, `python`, `react-ts`,
`postgres`) — a self-contained, drop-in bundle. Each `<stack>/` has a `pack.yaml`
(`detect` / `installs` / `assumptions`); the schema is in `_kit/rules-library/PACKS.md`.
Bootstrap selects packs matching the detected stack, resolves conditional installs, then
on an existing codebase **reconciles each pack's assumptions against reality** and asks
the user how to resolve divergences (adopt / relax / skip). Edit the packs here directly.

The kit also ships its own always-on, language-neutral `rules/_generic/*`, installed
alongside whatever stack packs apply.

## Extending

- New stack support → add a `<stack>/` pack under `_kit/rules-library/` (see `PACKS.md`).
- New generic skill → add `skills/<name>/SKILL.md`; make it read `PROJECT.md`; add
  it to the `allow` list in `settings.template.json` and to this manifest.
- Project-specific skills/agents → do NOT add them to the kit; create them in the
  project after bootstrap.
