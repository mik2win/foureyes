# Pack metadata (`pack.yaml`) — for automated install / bootstrap

Each stack folder (`python/`, `react-ts/`, `ruby/`, `rails/`, `postgres/`) carries a
`pack.yaml` so an installer (e.g. the feature-flow kit's `/bootstrap`) can select and
apply it automatically. Manual install (plain `cp`, per the README) ignores this file.

## Layout assumed

```
<stack>/
├── CLAUDE.md            # lean entry index
├── pack.yaml            # this metadata
└── claude/
    ├── rules/*.md       # path-scoped rules (frontmatter `paths:`)
    └── skills/*/SKILL.md
```

(All packs are Claude-only — rules live under `<stack>/claude/`.)

## Rule vs. skill — keep always-on context lean

A path-scoped rule loads **in full** every time Claude reads a matching file, so it is a
recurring context cost. Triage each topic:

- **Always-apply principle** (shapes every line you write in that layer — naming, OOP,
  security, the layer's conventions) → keep it a **rule**, scoped to the tightest `paths:`
  that still covers where it applies (e.g. `app/jobs/**/*.rb`, not `**/*.rb`).
- **Reference / how-to catalog** (API tours, idiom lookups, checklists you consult
  occasionally) → make it an **on-demand skill** under `claude/skills/`, not an always-on
  rule. It loads only when invoked or when its description matches the task. Per the Claude
  Code docs: "For task-specific instructions that don't need to be in context all the time,
  use skills instead."

For a large rule that is mostly worked examples, keep a **lean always-apply rule** (imperative
bullets + a one-line pointer) and move the GOOD/BAD code into a companion **reference skill**:
a short `SKILL.md` index plus `references/*.md` files the skill reads on demand. Group related
layers under one skill (e.g. `rails-reference` with `references/{models,queries,...}.md`) to
avoid skill-sprawl. The packs do this for the `ruby`/`rails`/`postgres` layer + convention
rules; the always-on rule then carries only the *what*, the skill carries the *how*.

When a pack ships skills, list `claude/skills/` in `also_install` so they get installed.

## `pack.yaml` schema

```yaml
name: python
description: One-line summary.
detect:                       # installer selects this pack if ANY matches the target repo
  any_of:
    - file: "pyproject.toml"  # file exists (optionally + `contains: "<substr>"`)
    - glob: "**/*.py"         # any file matches glob
    - path_exists: "config/application.rb"
depends_on: [ruby]            # other packs to also select (optional)

installs:                     # rule files (relative to claude/rules/) → target .claude/rules/
  - python-style.md           # string = always install
  - rule: python-data.md      # object = conditional install
    when: "project uses pandas/numpy"
    probe: "grep -Eq 'pandas|numpy' pyproject.toml requirements*.txt 2>/dev/null"
    on_absent: skip           # skip | ask

also_install:                 # non-rule files to copy alongside (optional)
  - CLAUDE.md
  - claude/skills/            # whole dir

templates:                    # files to copy but flag for the user to fill in (optional)
  - project-overview.md

assumptions:                  # reconcile each against an EXISTING codebase before install
  - id: layering
    rule_file: python-design.md
    expects: "Pure-core/domain separated from I/O edges; no I/O in domain."
    probe: "Inspect package layout for a domain/core layer vs I/O modules."
    on_divergence: ask        # ask (default, preferred) | adopt | relax | skip
```

## How the installer uses it

1. **detect** → pick packs matching the target repo; pull `depends_on`.
2. **installs** → copy rule files; for conditional entries run `probe` and honor
   `on_absent`.
3. **also_install / templates** → copy CLAUDE.md, skills; copy templates and flag them
   for the user to fill (`project-overview.md` holds project-specific context).
4. **assumptions** → on an existing repo, run each `probe`; if reality diverges from
   `expects`, resolve per `on_divergence` (default `ask`: adopt / relax / skip). Record
   the decision so re-runs are idempotent.

See the feature-flow kit's `skills/bootstrap/SKILL.md` for the consuming workflow.
