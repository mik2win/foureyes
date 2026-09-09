---
name: bootstrap
description: |
  Adapt the feature-flow kit to THIS project — the front door for setting it up. Run on the
  FIRST install after dropping the kit into a project's .claude/ folder: detects the stack,
  writes the project profile (.claude/PROJECT.md), installs and reconciles stack rule packs
  against the real codebase, wires settings/hooks/commands, and writes the kit manifest. Backs
  up before writing and asks keep-or-rollback before cleaning up build-time files. On a project
  that's ALREADY adapted (profile_status: ACTIVE) it hands off to /update-kit instead of
  re-installing, so any later update or re-adapt goes through the safe staging + 3-way merge.
  Trigger when the user says "bootstrap", "adapt the kit", "set up .claude for this project",
  or when PROJECT.md is missing / still a TEMPLATE.
  DO NOT TRIGGER to remove or roll back the kit (that's /teardown). For a plain kit update
  or re-adapt you can go straight to /update-kit — running /bootstrap on an already-adapted
  (profile_status: ACTIVE) project is still safe: it detects that and hands off to
  /update-kit rather than re-installing.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Agent
effort: high
---

# /bootstrap — adapt the kit to this project

You turn the portable feature-flow kit into a project-specific `.claude/`. You are
interactive: detect what you can, **ask the user about anything ambiguous or where rules
diverge from the real code**, then generate the project layer. Read `_kit/KIT.md` and
`_kit/rules-library/PACKS.md` once at the start — they define the kit and the pack format.

Work top-to-bottom, naming each phase as you enter it — the phase headings below **are** the
checklist, and none is optional. Do not skip or reorder: this run is interactive and long, and
a run that loses its place re-asks the user questions they already answered.

---

## Phase 0 — Preconditions

1. **Dispatch on entry (this skill is the front door) — check this FIRST.** If
   `.claude/PROJECT.md` already exists with `profile_status: ACTIVE` **and** you were entered
   directly (the user ran `/bootstrap` — not `/update-kit` calling the reconcile phases 3–6), this
   is **not** a first install: the project is already adapted. **Hand off to `/update-kit`** and
   stop — it stages the new/current kit, 3-way merges so local adaptations survive, then re-adapts.
   Re-copying the kit over `.claude/` and re-installing would clobber local edits — never do that.
   (Re-adapting after structural changes also goes through `/update-kit`.) Check this *before* the
   kit-present precondition below, because an adapted project has already removed `_kit/` at cleanup.
2. Confirm the current directory is the project root and the kit is present: `_kit/KIT.md`
   exists under `.claude/` (or the cwd if the kit was dropped at repo root). If not, stop
   and tell the user to copy the kit into `<project>/.claude/` first.
3. Read the contracts: `PROJECT.template.md`, `settings.template.json`, and
   `CLAUDE.snippet.md`. Stack rule packs are vendored in `_kit/rules-library/`.

## Phase 0.5 — Back up before any writes

Before writing anything, snapshot what you are about to change so this run is reversible
(Phase 8). Create a timestamped backup dir plus a manifest of newly created paths:

```bash
TS=$(date +%Y%m%d-%H%M%S); BK=".claude/.bootstrap-backup/$TS"; mkdir -p "$BK"
for f in CLAUDE.md .gitignore .claude/PROJECT.md .claude/settings.json .claude/hooks/guard-bash.sh; do
  [ -f "$f" ] && mkdir -p "$BK/$(dirname "$f")" && cp -p "$f" "$BK/$f"
done
: > "$BK/created.txt"   # paths this run newly creates — for a clean rollback
```

- Back up every file you will **modify in place** into `$BK` *before* you touch it. The loop
  covers the always-touched ones; add any other existing file you end up overwriting.
- As you install in Phases 5–6, append each **newly created** path (pack rules, pack skills,
  commands, `PROJECT.md` if it didn't exist) to `$BK/created.txt`, one per line.
- On a **re-run**, add a new snapshot — never delete earlier ones.
- This snapshot reverses **bootstrap's own writes**. Restoring the project to its *pre-kit*
  state also needs the pre-copy backup taken before the kit was copied in (README "Quick start"
  step); `/teardown` uses whichever backup is present.

## Phase 1 — Detect the project

Decide **empty** vs **existing** (any source files tracked or present beyond `.claude/`).

Scan for stack markers and structure. For a non-trivial repo, delegate the heavy scan to
an **Explore** agent (read-only) and have it report; otherwise scan inline:

- **Language/framework markers:** `Gemfile`(+`rails`), `package.json`(+framework deps),
  `pyproject.toml`/`setup.py`, `go.mod`, `Cargo.toml`, `*.csproj`, etc.
- **Package manager / tooling:** lockfiles (`yarn.lock`, `package-lock.json`, `uv.lock`,
  `poetry.lock`, `Gemfile.lock`); presence of `make`, task runners, `bin/` scripts.
- **Test / build / lint commands:** infer from config (`Makefile` targets, `package.json`
  scripts, `pyproject` tool config) — capture exact strings.
- **Structure / layers:** top-level source dirs, module/layer layout, any existing
  architecture docs, `CLAUDE.md`, `.cursor/rules`, README.
- **Git host:** `git remote -v` → github / gitlab / none.
- **Integrations:** external SDKs/clients in deps and their official doc URLs.

## Phase 2 — Draft the profile

Fill `PROJECT.template.md` into a draft `.claude/PROJECT.md` from detection.

- **Existing project:** populate every section from evidence; mark anything you inferred
  but aren't sure of for confirmation in Phase 4.
- **Empty project:** you can't detect — ask the user. Use `AskUserQuestion` for: primary
  language/framework, package manager, test command, architecture style, and the business
  domain + roles. Keep it to a few focused questions.
- Always confirm the **Domain** section with the user briefly — it drives `/analyst` and
  can't be reliably detected from code.
- Set the **Domain → Glossary (CONTEXT.md)** and **ADR location** pointers (default `CONTEXT.md`
  at repo root and `docs/adr/`). Leave them `n/a` until `/domain-model` records the first
  term/decision — **do not create the files now** (they're created lazily by `/domain-model`).
  If the repo already has a `CONTEXT.md` or `docs/adr/`, point at it.
- Set **Plans / backlog → Issue tracker** = `local`, the **Issues directory** (default
  `<backlog>/issues/`, used by `/to-issues` and `/triage`), and the **Triage labels** state
  machine — offer the default `needs-triage → ready → in-progress → done` + `blocked` and let the
  user adjust. Don't scaffold the issues directory; `/to-issues` creates it on first use.
- Set **Plans / backlog → Small-debt register** — default `<backlog>/small-debt-register.md`, the
  path-keyed home for verified zero-consequence fixes that `/close-epic` refuses to card and
  `rules/_generic/code.md` tells a file-editing session to grep. **Don't scaffold it**; it is created
  from `skills/close-epic/assets/small-debt-register.md` on first use. `n/a` is a valid answer — the
  rows then stay as clauses in ledger rows, which is where they were before the register existed.
- Ask the **artifact git policy** and record it in `PROJECT.md` → "Artifact git policy". For each
  category of agent-generated artifact, the **user decides** whether it stays **local** (gitignored,
  never pushed) or is **committed** (shared) — explain the trade-off, don't impose. Group into a
  couple of `AskUserQuestion`s, e.g.:
  - *Working backlog* (briefs/specs/plans/PRDs/issues/handoff/diagnosis): "keep as **local** scratch
    that never leaves your machine, or **commit** them as shared docs?"
  - *Shared model* (`CONTEXT.md` glossary + ADRs): "**commit** as the team's shared language
    (recommended — that's the point of a ubiquitous language), or keep **local**?"
  Offer a sensible default (working backlog **local**, `CONTEXT.md`/ADRs **committed**) but the
  choice is the user's. The chosen **local** locations get added to `.gitignore` in Phase 6.
- Ask the **VCS / code-publish policy** and record it in `PROJECT.md` → "Security / VCS policy".
  The safe **default is suggest-only**: the agent never runs `git add` / `commit` / `merge` /
  `push` — it outputs the command for the user to run. Confirm the user wants that, or relax it
  (e.g. allow local commits but **never** push). Also ask for **any other commands to forbid
  entirely** — a deploy/publish CLI, `scp`/`rsync` to a remote, a package-publish command, etc.
  Both answers drive the `settings.json` `deny` list and the guard-bash blocks in Phase 5, so the
  user explicitly controls what the agent may run and what code can leave the machine.

Set `profile_status: ACTIVE` only at the end (Phase 5), not yet.

## Phase 3 — Select rule packs (from the rules library)

Stack rule packs are **vendored** in the kit at `_kit/rules-library/` — read them there,
no network needed. (If that folder is missing, proceed generic-only and tell the user.)

1. Always install the kit's `rules/_generic/*` (language-neutral; already in place).
2. Scan `_kit/rules-library/*/pack.yaml`; read `_kit/rules-library/PACKS.md` for the schema.
   Evaluate each `detect` against the target repo; select matching packs and pull their
   `depends_on`. If both `ruby` and `rails` match, choose ONE per their `notes` (ruby =
   comprehensive, rails = condensed) — ask the user if unsure. Compose freely across
   languages (e.g. `ruby` + `react-ts` + `postgres`, or `python` + `postgres`).
3. If a detected stack has **no pack** in the library, tell the user: the generic core
   works, but stack rules are missing — offer to (a) proceed generic-only, or (b) pause to
   add a pack under `_kit/rules-library/` per `PACKS.md`, then re-run.
4. Resolve each pack's `installs`: take always-entries; for conditional entries
   (`rule`/`when`/`probe`/`on_absent`) run the `probe` against the repo and honor
   `on_absent` (`skip`, or `ask`). Note each pack's `templates` (e.g. `project-overview.md`)
   for the fill step. Warn about any listed file missing from the library.

## Phase 4 — Reconcile rules with reality (key step)

Only for an **existing** project. For each selected pack, walk its `assumptions[]`:

1. Run the `probe` (a cheap Grep/Glob/Read check) to test whether the pack's `expects`
   holds in this codebase.
2. If reality **matches** → install the rule as-is.
3. If reality **diverges** and `on_divergence: ask` (the default) → present the divergence
   via `AskUserQuestion`: state what the rule expects vs what the code actually does, and
   offer:
   - **Adopt** — keep the rule; note that code should move toward it over time.
   - **Relax** — rewrite the rule to match the current code (edit the installed copy).
   - **Skip** — don't install this rule.
   (For `adopt`/`relax`/`skip` defaults in the pack, apply without asking.)
4. Batch related divergences into as few questions as is sensible — don't ask 20 separate
   questions if 4 grouped ones cover it.
5. Record each resolution (assumption id → decision) in `PROJECT.md` → a "Rules notes"
   subsection, so the choice is traceable and the next `/bootstrap` reuses it.

## Phase 5 — Generate the project layer

Write the project-specific files. As you go, log each newly created path to `$BK/created.txt`
and back up any pre-existing file into `$BK` before overwriting it (see Phase 0.5):

1. **`.claude/PROJECT.md`** — finalize all sections; set `profile_status: ACTIVE`.
2. **`.claude/rules/`** — copy the selected packs' resolved `installs` rule files
   (reconciled) from `_kit/rules-library/<stack>/claude/rules/` into `.claude/rules/`; keep the
   kit's `_generic/`. Copy each pack's `also_install` skills into `.claude/skills/`. Fold a
   pack's `CLAUDE.md` guidance into `PROJECT.md` rather than overwriting the project's
   CLAUDE.md. Copy `templates` (e.g. `project-overview.md`) and flag them for the user to
   fill. Update `PROJECT.md` → Rules to list what's installed.

   **Then narrow each installed rule's `paths:` to this project's actual layout — this is the
   step that turns the rule set into a context budget.** The kit ships `paths: "**/*"` as a
   deliberate template default: it means *"scope me, I don't know your tree yet"*, and a rule
   left that wide loads on every file touch. Walk the installed rules and rewrite each glob
   against the layout you surveyed:

   - **Match the rule's subject, not its tier.** A Python-convention rule takes the source
     globs for Python; a frontend rule takes the asset/template/script directories. Read the
     rule's own `description` to decide what it governs.
   - **Cover every language the rule's subject appears in.** The common failure is a glob that
     names one language and silently drops the rest — an observed project scoped five
     behavioural rules to `src/**/*.py`, and they were absent from **13** frontend-only
     sessions before anyone noticed. If a rule is about *how the agent behaves* rather than
     about a language, it belongs on the whole tree or in the always-on set.
   - **Leave `paths:` off entirely only for rules that must hold with no file open.** Those are
     the standing context tax — every session pays for them, so each one has to earn it.
   - **A rule whose spine must hold at a moment its `paths:` cannot see is mis-scoped.** Check
     the trigger against the *moment of application*, not the file where the rule is edited.
   - **`sql.md` — re-scope to where this project actually writes SQL:** migrations, models, raw
     `.sql`, seeds (Django `*/migrations/`, Rails `db/migrate/`, Alembic `alembic/versions/`) —
     but where SQL lives in ordinary application modules, **replace** the template globs with
     those directories rather than narrowing them, and accept the scope by measuring: it covers
     most files that carry SQL, and `**/models/**` is not collecting ML or asset directories.
   - Record the narrowing in `PROJECT.md` → Rules, so `/update-kit` can tell a deliberate
     project scope from a stale template default.
3. **`.claude/settings.json`** — copy `settings.template.json` verbatim (it is already a
   clean, valid settings file with `$schema` and no comment keys), then **append** the
   project-specific permission entries derived from the profile:
   - allow: `Bash(...)` patterns for the profile's test/lint/format/build/run/deploy commands.
   - allow: `WebFetch(domain:...)` for each Integrations doc URL. (Web search/fetch for research
     and implementation stay available — the policy below controls *code leaving the machine*, not
     reading the web.)
   - deny: the **code-publish commands** per the VCS / code-publish policy. The template already
     denies `git add` / `git commit` / `git merge` / `git push` (suggest-only default) — keep them,
     or relax to match the survey (e.g. drop `git commit` if the team lets the agent commit locally,
     but keep `git push`). Add any other user-forbidden commands (banned package manager, server
     start, destructive db tasks, a deploy/publish CLI, `scp`/`rsync` to a remote) — these also
     drive the guard hook (next).
   Keep the emitted file strictly valid JSON: no `//` comment keys, no unknown hook events,
   and resolve everything (the schema is strictly validated and rejected as a whole on error).
   Three conventions worth applying while writing the file (details in `_kit/KIT.md` → Hook &
   permission configuration): **every hook command path is
   `$CLAUDE_PROJECT_DIR/.claude/hooks/<name>.sh`** — never a bare relative path (it assumes the
   hook's cwd is the project root, which a worktree breaks) and never an absolute one (breaks on
   another machine); **duplicate every read-only `Bash(<cmd> *)` entry in its
   `cd`-prefixed spelling** (`Bash(cd * && rg *)`) — the whole command line is matched, so a
   session that writes `cd src && rg foo` misses the unprefixed rule and prompts every time; and
   use the per-entry `"if"` / `"statusMessage"` / `"async"` hook fields where they fit —
   `"if": "Edit(<the profile's source glob>)"` is the usual way to scope `format-file.sh` to real
   source files, and `"async": true` belongs on notifications but **never** on a guard (an async
   hook cannot block).
   Then offer the **opt-in hooks**, which the template deliberately leaves unwired. Ask them
   in one question, state the trade-off in one line each, and merge only what the user accepts.
   `Stop` is an array: merging two examples that both use it means **appending**, never replacing.
   - **post-turn verify gate** — merge the `Stop` block from `settings.stop-gate.example.json`
     into `hooks` (non-blocking lint/test after each turn; see `hooks/verify-stop.sh`).
   - **desktop notifications** (macOS only) — merge `settings.notifications.example.json`
     (`Notification` / `Elicitation` / `Stop`, `osascript`, all `async`). Offer it only on macOS;
     on other platforms say the equivalent is a one-line `notify-send`/toast command in the same
     shape, and leave it to the user.
   - **prompt→skill hint** — merge the `UserPromptSubmit` block from
     `settings.skill-hint.example.json` into `hooks` (see `hooks/skill-hint.sh`). Advisory only:
     it names the top 1–2 matching skills as context and never blocks or edits the prompt.
     Worth offering because most kit skills are manual-by-default, so a task request with a
     perfect skill match otherwise runs bare. Say the two limits out loud: matching is
     **English-token based** (a non-English prompt scores 0 and it stays silent), and it costs
     ~29 ms on every prompt. `SKILL_HINT_DISABLE=1` disables it later without unwiring.
4. **`.claude/hooks/guard-bash.sh`** — append project-specific `case` arms in the
   `__BOOTSTRAP_PROJECT_BLOCKS__` region from the deny decisions. The `__VCS_PUBLISH_BLOCKS__`
   region is **default-on** (blocks `git add`/`commit`/`merge`/`push`) — leave it as the safe
   default unless the VCS-policy survey said to relax a specific command, in which case remove only
   that one `case` arm. Leave `format-file.sh`, `sessionstart.sh`, `guard-secrets.sh`,
   `verify-stop.sh`, and `skill-hint.sh` as-is — the first three self-detect or are warn-only, and
   the last two are inert unless the user wired them in step 3 (the file being present is not the
   same as the hook being on). Optionally tighten `format-file.sh` to the profile's exact
   `format` command.
   Two regions in the generic hooks are worth filling when the project has the matching facts:
   - **`sessionstart.sh` → `__BOOTSTRAP_EPIC_STATUS__`.** If the project has a tool that prints
     active-epic progress or status drift (`PROJECT.md` → Plans / backlog and Commands — a plan
     CLI, a board script, a `make` target), uncomment the region and fill `__EPIC_STATUS_PROBE__`
     (the path whose absence keeps it silent) and `__EPIC_STATUS_CMD__` (the one-line command,
     with a fallback runner if the primary may be missing). No such tool → leave it commented and
     say nothing. Verify with `bash -n` and one manual run: it must stay **report-only**, print at
     most a few lines, and be silent on failure.
   - **`guard-bash.sh` → `__BOOTSTRAP_PROJECT_BLOCKS__` data-protection templates.** See the
     block library commented in that region, and step 4 below.
5. **`.claude/commands/`** — install `commit.md` always; install `pr.md` (GitHub) or
   `mr.md` (GitLab) per detected git host. Copy from `_kit/templates/commands/`.
6. **`.claude/agents/`** — keep the generic agents; remove any that don't fit (e.g. drop
   `arch-tracer` only if the project is genuinely single-layer). Default: keep all.

## Phase 6 — Wire up

1. Merge `CLAUDE.snippet.md` into the project's `CLAUDE.md` (create it if absent). The
   snippet is delimited by `feature-flow-kit:begin/end` — replace that block on re-run,
   never duplicate it.
2. **`.gitignore` — enforce the artifact git policy.** For every location the user marked **local**
   in `PROJECT.md` → "Artifact git policy", ensure it's excluded so it can't be pushed. **Show the
   exact lines and confirm before writing.** Append them to the project's `.gitignore` (create it if
   absent) inside a delimited block:

   ```
   # feature-flow-kit:begin — local agent artifacts (never pushed)
   <local plans/backlog location>/
   <local issues directory>/
   # feature-flow-kit:end
   ```

   Idempotent — replace this block on re-run, never duplicate; if all categories are **committed**,
   write no block (and remove an existing one). Back up `.gitignore` first (done in Phase 0.5) and,
   if you created it, log it to `$BK/created.txt`. Leave **committed** locations (e.g. `CONTEXT.md`,
   `docs/adr/` when chosen committed) tracked — never gitignore them.
3. Sanity-check that the installed skills can resolve everything they reference in
   `PROJECT.md` (Commands, Plans/backlog location, Architecture). Fix gaps in PROJECT.md.
4. **Write the kit manifest** `.claude/.kit-manifest.json` — the install baseline `/update-kit`
   needs to 3-way merge a future kit version without clobbering local edits. Hash every
   **persistent, pristine-by-default kit file** (`skills/**` kit skills, `agents/**`, `hooks/**`
   except `guard-bash.sh`, `rules/_generic/**`, `output-styles/**`, `schemas/**`, `docs/**` kit
   docs) and record it. It's local state (fine in a gitignored `.claude/`); log it to `$BK/created.txt`.

   ```bash
   hashof() { shasum -a 256 "$1" 2>/dev/null | cut -d' ' -f1 || sha256sum "$1" | cut -d' ' -f1; }
   ```
   Shape: `{ "kit_version": "<KIT.md version or date>", "installed_at": "<ISO>",
   "files": { "<relpath under .claude/>": "<sha256>", … } }`.

## Phase 7 — Report & verify

Output:
- **Installed:** profile, rules (generic + packs), settings, hooks, commands, agents.
- **Reconciliation summary:** table of assumption → decision (adopt/relax/skip).
- **Open questions / TODOs** left in PROJECT.md.
- **Smoke-test checklist** for the user:
  - `/analyst` starts and asks domain questions sourced from the profile.
  - the profile's `test` command runs.
  - `/prepare` assembles its rules checklist from the installed rules.
  - `/which-skill "where do I start"` routes to a sensible pipeline step.
  - `/domain-model` can record a first term into `CONTEXT.md` (creates it lazily).
  - **the hooks actually registered** — `/hooks` shows a non-zero count for each event you wrote
    and a source label pointing at your settings file. `/hooks` is TUI-only; when it is
    unavailable, provoke a hook into producing output and look for an `attachment` record
    (`hook_success`, carrying `hookEvent`/`hookName`/`command`) in the session transcript.
    Full procedure and its two measured blind spots: `_kit/KIT.md` § Hook & permission
    configuration. **A hook file on disk is not a registered hook** — silent kit hooks look
    identical either way, so this is the one item that cannot be checked by reading the tree.
- **Updating later:** to pull a newer kit version into this project without losing your
  adaptations, drop the new version into `.claude/.kit-incoming/` and run `/update-kit` — it
  3-way merges against the manifest and re-adapts in one pass. Don't re-copy the kit by hand.

## Phase 8 — Confirm: keep or roll back (ask)

After the Phase 7 report, ask via `AskUserQuestion`: **Keep** the adaptation, or **Roll back**.

- **Keep** → proceed to Phase 9.
- **Roll back** → undo this run from the Phase-0.5 snapshot `$BK`:
  1. Delete every path listed in `$BK/created.txt` (files, then any now-empty dirs this run
     created).
  2. Restore every backed-up file from `$BK` to its original location (overwriting the
     modified copy) — this includes `.gitignore`, so the `feature-flow-kit` block this run added is
     reverted with it.
  3. For any file that had **no** prior version in `$BK`, strip the `feature-flow-kit:begin…end`
     block this run added — in `CLAUDE.md` and in `.gitignore` (delete a file the kit created if
     it's now empty).
  4. Leave `_kit/` in place so the user can fix inputs and re-run. Report exactly what was
     undone.

## Phase 9 — Clean up build-time files (ask first)

Only after the user keeps the result. Ask to confirm, then remove build-time-only material:
`rm -rf .claude/_kit` and delete `.claude/*.template.*` and `.claude/CLAUDE.snippet.md`.
Offer to also remove the `.claude/.bootstrap-backup/` snapshots and any pre-copy backup once
the user is satisfied. Leave a clean project `.claude/`. (The rule packs lived under `_kit/`;
once it's removed, the selected rules already live in `.claude/rules/`.) `/teardown` runs this
same cleanup — and a full uninstall — on demand later.

---

## Hard rules

- **Detect, don't assume.** Every project fact written to PROJECT.md must come from
  evidence or from the user — never from a default framework guess.
- **Ask on divergence.** When installed rules contradict the real code, the user decides
  (adopt/relax/skip). Never silently install a rule the codebase violates.
- **First install is the front door; updates route to `/update-kit`.** On a fresh target,
  `/bootstrap` does the full install. On an already-adapted project (ACTIVE) it hands off to
  `/update-kit` rather than re-copying. The reconcile phases (3–6) stay idempotent — invoked by the
  install flow or by `/update-kit`, they update profile/rules in place and never duplicate the
  CLAUDE.md block, rules, or settings entries.
- **Don't touch app code.** Bootstrap only writes under `.claude/` (and the CLAUDE.md
  snippet). It plans refactors via rules; it does not refactor the project itself.
- **Reversible.** Back up before writing (Phase 0.5) and confirm keep-or-rollback (Phase 8)
  before any cleanup. A rolled-back run leaves no trace; never delete a backup the user
  hasn't approved removing.
- **Leave a manifest.** Always write `.claude/.kit-manifest.json` (Phase 6) — it's the baseline
  `/update-kit` uses to tell adapted kit files from pristine ones on a future version bump.
