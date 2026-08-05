![FourEyes — a disciplined feature pipeline for Claude Code. 49 skills, 16 subagents, rule packs, hooks, MIT.](assets/banner.png)

**English** · [Русский](README.ru.md)

# FourEyes 🤓

> A self-contained `.claude/` that turns any repo into a disciplined feature factory — one adaptive pipeline from discovery to shipped code, backed by a fleet of subagents that report signal, not noise.

*Two meanings, both meant. **Four-eyes** is the kid in glasses who actually read the manual. The **four-eyes principle** is the rule that no consequential work is accepted on one pair of eyes. This kit automates the second one so you can afford to be the first.*

Drop it into a project's `.claude/`, run `/bootstrap`, and you get a stack-adaptive feature pipeline (`/discover → /analyst → /prepare → /implement`), 49 skills, 16 subagents, always-on rules, and hooks — all tailored to *your* repo, with no per-project skill rewrites.

## Quick start

**1. Copy the kit into your project.** Replace `<project>` with your project's path and run this from anywhere *except* inside that project — the clone is temporary scaffolding, not something you keep:

```bash
# 1. Clone the kit to a temporary location — NOT inside your project
git clone https://github.com/mik2win/foureyes.git /tmp/foureyes

# 2. Back up everything the kit and /bootstrap can overwrite
[ -e <project>/.claude ]   && cp -r <project>/.claude <project>/.claude.bak
[ -f <project>/CLAUDE.md ] && cp <project>/CLAUDE.md <project>/CLAUDE.md.bak

# 3. Copy the kit into the project's .claude/ (repo infrastructure stays behind)
rsync -a --exclude='.git' --exclude='.claude' --exclude='_backlog' --exclude='tools' \
  --exclude='guide' --exclude='.github' --exclude='LICENSE' --exclude='CONTRIBUTING.md' \
  --exclude='CHANGELOG.md' --exclude='CODE_OF_CONDUCT.md' --exclude='SECURITY.md' \
  --exclude='.gitignore' \
  /tmp/foureyes/ <project>/.claude/

# 4. Drop the clone — the kit now lives in your project
rm -rf /tmp/foureyes
```

**2. Open the project in Claude Code and run `/bootstrap`.** It scans your stack, drafts `.claude/PROJECT.md` (asking you about the domain and anything ambiguous), installs matching rule packs, wires `CLAUDE.md` and `settings.json`, then asks **keep or roll back**. Nothing is written without a backup, and a rejected run leaves no trace.

**3. Try it.** Run `/analyst` and answer a few questions, or just ask `/which-skill "<what you're about to do>"` and let it route you.

Two things worth knowing before you run it: an existing `.claude/settings.local.json` **survives** (the copy adds files, it never deletes yours), and if your stack has no rule pack in the library, `/bootstrap` says so and offers to proceed with the generic rules only — it doesn't guess. Full walkthrough, update, and uninstall: [guide/en/install.md](guide/en/install.md).

## Where do I start?

| You're holding | Type this |
|---|---|
| a new feature, still fuzzy | `/discover` → `/analyst` → `/prepare` → `/implement` |
| a small, well-understood change | `/prepare` → `/implement`, then `/code-review` |
| a bug | `/diagnose`, then `/tdd` or `/test` to lock the fix |
| an unfamiliar or inherited codebase | `/onboard` |
| an outcome you can't spec technically | `/idea` — it asks in plain language and drives the pipeline itself |
| a whole surface to audit ("review every screen") | `/prompt-master` (program pass) → cards → `/prepare` each |
| no idea which of the 49 fits | `/which-skill "<your situation>"` |

```text
  MAIN PIPELINE
     /discover  →   /analyst   →   /prepare   →   /implement   →   /code-review + /test
     (research)     (spec)         (plan)          (build)           (verify)
                       ▲              ▲                │
                    /grill         /grill      test-first slice → /tdd
                       └──── /domain-model: CONTEXT.md glossary + ADRs (shared language) ────┘

  BEFORE COMMITTING  /spike (one risk) · /prototype (compare designs) · /select-tech
  PARALLEL WAVES     /prepare (decompose) → N × /implement → /epic-status (next wave?)
  SHIP               /close-epic → /preflight (suite · deps · security · docs → GO/NO-GO)
  LEARN              /retro — recurring lessons from deviation reports, back into your rules
```

The full map — every skill, every recommended chain, and the same flow as a Mermaid diagram — is in [guide/en/reference.md](guide/en/reference.md).

## What you get

- **A pipeline, not a pile.** `discover → spec → plan → build → review` as one self-propelling flow with stage gates, not 200 à-la-carte agents.
- **Subagents that respect your context window.** Every finder honors one **Finding Contract** — bounded, structured findings (`path:line` + severity + effort + concrete harm) — so a 10-agent review returns signal, not an 8k-token dump.
- **Drop-in and stack-adaptive.** `/bootstrap` reads your repo into `PROJECT.md`; skills stay generic and adapt at runtime. Porting = copy + bootstrap, never editing skills.
- **Survives long work.** The plan is the single source of truth across compaction and sessions, so you can resume mid-feature without re-explaining.
- **A learning loop.** Every `/implement` writes a Deviation Report; `/retro` mines them for recurring patterns and folds the lessons back into your rules.
- **The agent never publishes code without you.** `git add`/`commit`/`merge`/`push` are denied in `settings.json` and hard-blocked by a hook — it prints the command, you run it.

Skills are **manual by default**: 42 of 49 carry `disable-model-invocation: true` and run only when *you* type them. That is deliberate, it has a measured cost, and there are three escape hatches — [the whole trade-off, with numbers](guide/en/evidence.md#skills-are-manual-by-default--and-the-three-escape-hatches).

## Honest about what's proven

The kit was put on a blind A/B bench before it was published: two arms of the same real repository, a sealed mixing map, a 5-axis rubric, four rounds, ~40 judged sessions. The results that argue *against* the kit are published alongside the ones that don't — the always-on rule tier bought **no measurable quality gain** across three rounds (it is merely cheaper), which is why it was cut from 13 rules to 4. One Python repo, n=2 per cell, a model as judge: directional, not a benchmark. The stack packs (ruby / rails / react-ts / postgres) were never in an arm at all.

Read the full table, negatives included → [guide/en/evidence.md](guide/en/evidence.md).

## Learn more

| | |
|---|---|
| [guide/en/reference.md](guide/en/reference.md) | Every skill, agent, rule, hook, and the repo layout · recommended flows · design principles |
| [guide/en/install.md](guide/en/install.md) | Full install walkthrough · `/update-kit` (3-way merge) · `/teardown` |
| [guide/en/evidence.md](guide/en/evidence.md) | What the A/B bench measured, including the results against the kit |
| [guide/en/why.md](guide/en/why.md) | The discipline layer · how it differs from catalogs and methodologies · why copy-in, not a plugin |
| [docs/](docs/) | The reference material the kit itself reads: 22 agent failure modes, generation-from-the-inside, decision craft, prompt patterns |

Russian versions of all four live in [guide/ru/](guide/ru/).

**Lineage.** FourEyes builds on ideas popularized by [Matt Pocock's skills](https://github.com/mattpocock/skills) and [obra/superpowers](https://github.com/obra/superpowers) — the one-question interview, living ubiquitous language + ADRs, deep-module design, a discover→ship methodology. What it adds is a disciplined multi-agent layer and a portable, stack-adaptive distribution. Method is borrowed, not text; both upstreams are MIT, as is FourEyes ([LICENSE](LICENSE)). More: [guide/en/why.md](guide/en/why.md).

Contributions welcome — start with [CONTRIBUTING.md](CONTRIBUTING.md). The rule packs are the least-proven part of the kit and the most useful thing to fix.
