# Changelog

All notable changes to FourEyes are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Because the kit is installed by copying files into a project's `.claude/`, "version" means *the kit source you copied from* — `/update-kit` reconciles a newer version against the manifest written at install time.

## [Unreleased]

## [0.1.0] — 2026-08-04

First public release. Everything below is the initial contents rather than a diff.

### Added

- **The pipeline** — `/discover → /analyst → /prepare → /implement`, plus `/idea` as a plain-language front door and `/scaffold` for "add another one like the existing one".
- **49 skills** across the pipeline, orientation (`/onboard`), explore-first (`/spike`, `/prototype`, `/select-tech`), alignment and design (`/grill`, `/domain-model`, `/codebase-design`, `/api-design`), quality (`/code-review`, `/refactor`, `/diagnose`, `/test`, `/tdd`, `/test-spec`, `/arch-health`, `/clean-mvp`, `/sweep`, `/perf`), architecture evolution (`/decompose`, `/revisit`, `/distill`), ship-and-learn (`/rollout`, `/preflight`, `/incident`, `/retro`), security (`/threat-model`, `/audit-security`, `/deps`), a local backlog tracker (`/to-prd`, `/to-issues`, `/triage`, `/epic-status`, `/close-epic`), and meta skills (`/which-skill`, `/prompt-master`, `/writing-skills`).
- **16 subagents** — reviewers, the adversarial verification pair `finding-verifier` + `completeness-critic`, `plan-challenger`, analysis agents, writers, and `backlog-researcher`. All share one **Finding Contract**, also shipped as `schemas/finding.schema.json`.
- **14 generic rule files** in three load tiers: `core.md` alone is always-on (~950 tokens), code rules are `paths: "**/*"`-scoped, and authoring/planning rules are scoped to where they fire.
- **5 stack rule packs** — `python`, `react-ts`, `ruby`, `rails`, `postgres`.
- **8 hooks** — `guard-bash`, `guard-secrets`, `format-file`, `sessionstart`, `precompact`, `subagent-stop`, plus the opt-in, off-by-default `verify-stop` and `skill-hint`. Every hook but `guard-bash` follows the **warn-not-block** contract.
- **Lifecycle skills** — `/bootstrap` (detect stack, write `PROJECT.md`, install and reconcile rule packs, wire `CLAUDE.md` and `settings.json`), `/update-kit` (3-way merge against `.kit-manifest.json`, preserving local adaptations), `/teardown` (clean up or fully uninstall).
- **Code-publish control** — `git add`/`commit`/`merge`/`push` denied in `settings.json` and hard-blocked by `guard-bash.sh`; the agent suggests the command, you run it.
- **Docs** — `self-knowledge.md`, `decision-craft.md`, `agent-failure-modes.md`, `working-with-agents.md`, `prompt-patterns.md`, `audience-altitude.md`, `observability.md`, `agent-teams.md`.
- **English and Russian READMEs**, kept in structural parity.
- **MIT license**, and a stdlib-only structural validator (`tools/validate-kit.py`) wired into CI.

### Notes

- **The always-on tier is deliberately one file.** Three A/B rounds measured no quality gain from a larger always-on rule tier and a ~13% cost increase, so it was cut to `core.md` alone. The honest claim is *the same result for less money*, not *it works better* — the README publishes the results that argue against the kit alongside the ones that don't.
- **Copy-in is the only install path.** The Claude Code plugin model carries no `rules/` component and mandatorily namespaces commands, so a plugin cannot deliver either the always-on rules or an unprefixed `/discover`. An installer plugin is the likely future addition and ships only after an end-to-end smoke test. See [Distribution model](README.md#distribution-model).

[Unreleased]: https://github.com/mik2win/foureyes/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mik2win/foureyes/releases/tag/v0.1.0
