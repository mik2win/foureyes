# Contributing to FourEyes

Thanks for looking. FourEyes is a `.claude/` bundle, not an application — so "contributing" mostly means writing prompts, rules, and hooks that survive contact with a weaker model than the one you tested on. This document covers the local checks, the conventions the kit holds itself to, and the few rules that are non-negotiable.

## Quick start

```bash
git clone https://github.com/mik2win/foureyes.git && cd foureyes
python3 tools/validate-kit.py --stats     # stdlib only, nothing to install
```

The validator checks skill/agent frontmatter, the skill-listing budget, dead links (both markdown links and backticked kit paths), hook syntax and executable bits, JSON validity, and machine-local paths that leaked into committed files. CI runs exactly this, plus an advisory `shellcheck` pass over `hooks/`. **Run it before you open a PR** — a green local run is the whole gate.

To actually exercise a change, copy the kit into a throwaway project's `.claude/` and run it. Reading a skill is not testing a skill.

## The rules the kit holds itself to

These are the kit's own rules applied to the kit. A PR that breaks one will be asked to change.

**Warn, don't block.** A hook warns and exits 0. Blocking — `exit 2` or `permissionDecision: "deny"` — is allowed only on an *irreversible* action, and the kit ships exactly one such case (`guard-bash.sh`). Everywhere else a false positive costs more than the miss it prevents. If a proposed hook can only work by blocking, that is a reason to reject the hook.

**Evidence over assertion.** Claims in skills, rules, and the README are expected to be checkable. "Should work" is not a smoke test. If you measured something, say what you measured and on what; if you didn't, don't imply you did. The kit deliberately publishes results that argue *against* it (`guide/en/evidence.md`) — keep that habit.

**Skills carry invariant logic only.** Every project-specific fact (stack, paths, commands, layers, domain) belongs in `PROJECT.md`, which `/bootstrap` writes. If your change makes a skill know something about a particular stack, it probably belongs in a rule pack under `_kit/rules-library/` instead.

**Mind the always-on budget.** Only `rules/_generic/core.md` loads unconditionally, and three A/B rounds found that a *larger* always-on tier bought cost, not quality. Adding always-on text needs a reason beyond "it seems useful". Prefer a `paths:`-scoped rule, or a doc the rule points at.

**Respect the listing budget.** Every model-invocable skill's `description` is spent on every request. `validate-kit.py --stats` prints the per-skill budget; the cap is 1536 characters and the validator warns within 10% of it. Most skills should carry `disable-model-invocation: true` (41 of 49 do) — the kit is manual-first on purpose.

**Put the slash command first in any copy-paste prompt.** Claude Code expands a slash command only when the message **starts** with it, so in a prompt pack the command is the first line **inside** the fenced block and headings, hand-offs and notes stay **outside** it. Get this wrong and the failure is silent — the skill never loads, nothing errors, and the session runs a lookalike procedure. [The measured case and its cost](guide/en/evidence.md#skills-are-manual-by-default--and-the-three-escape-hatches).

**Never publish code on the user's behalf.** The kit denies `git add`/`commit`/`merge`/`push` and blocks them in `guard-bash.sh`. Do not add a code path that stages, commits, or pushes; suggest the command as text and let the user run it.

## Working on specific parts

| You're changing | Read first | Also update |
|---|---|---|
| a skill | [`skills/writing-skills/SKILL.md`](skills/writing-skills/SKILL.md) | the "What's in it" table and Layout tree in [`guide/en/reference.md`](guide/en/reference.md), `/which-skill`'s catalog, and any prose count (`N of the kit's M skills`) |
| an agent | [`rules/_generic/delegation.md`](rules/_generic/delegation.md) | check the harness doesn't strip tools you declared |
| a rule | [`_kit/rules-library/PACKS.md`](_kit/rules-library/PACKS.md) | the rule's `description:` frontmatter records what it absorbed — keep provenance greppable |
| a hook | the warn-not-block contract above | `settings.template.json`, or a `settings.*.example.json` if it's opt-in |
| the README or the guide | — | **both** languages: `README.md` + `README.ru.md`, `guide/en/*.md` + the matching `guide/ru/*.md` |

### Both languages, always

The README is the landing page — install first, everything else linked. Its long form lives in `guide/en/` (`reference.md`, `install.md`, `evidence.md`, `why.md`), which is repo documentation and is **not** copied into a user's `.claude/`. Each English file has a Russian twin at the same filename under `guide/ru/`, and the pairs are kept in structural parity — same sections, same tables, same code blocks. If you change one and cannot write the other, say so in the PR and it will be translated; an out-of-sync pair is worse than an untranslated note. Code identifiers, paths, commands, config keys, and established domain terms stay in English inside the Russian text.

### Prose is not hard-wrapped

In markdown that a human reads rendered — both READMEs, `guide/**/*.md`, `CHANGELOG.md`, `docs/*.md`, the root policy files, and PR descriptions — one paragraph is **one line**. No wrapping at 80 or 100 columns; the renderer wraps, and a re-wrapped paragraph turns a one-word fix into a diff over every following line. Line breaks stay where they carry meaning: list items, table rows, code blocks, frontmatter. Commit messages are exempt — wrap those as usual.

## Commits and pull requests

Commit messages follow Conventional Commits with the touched area as scope:

```
feat(kit): …    fix(rules): …    docs(readme): …    refactor(skills): …
```

In the PR description, state what you changed, how you verified it, and what you did *not* verify. An honest "I ran the validator but did not exercise this in a real project" is more useful than silence.

## Reporting bugs and proposing skills

Use the [issue templates](.github/ISSUE_TEMPLATE). For a bug, the single most valuable thing is the Claude Code version plus what the agent actually did versus what you expected. For a new skill, lead with the situation it serves — the kit already has 49 skills, and the bar for a fiftieth is that no existing one covers the case and `/which-skill` would genuinely mis-route without it.

## License

By contributing you agree that your contributions are licensed under the [MIT License](LICENSE).
