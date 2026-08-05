---
name: teardown
disable-model-invocation: true
description: |
  Remove or roll back the feature-flow kit from THIS project, safely and reversibly. Two
  scopes: "clean up leftovers" deletes build-time material (_kit/, *.template.*,
  CLAUDE.snippet.md, old .bootstrap-backup snapshots) while keeping the working config;
  "uninstall" returns the project to its pre-kit state from a backup (or git). Trigger when
  the user says "remove the kit", "uninstall the kit", "clean up the kit leftovers",
  "roll back bootstrap", or "/teardown". DO NOT TRIGGER to INSTALL/adapt the kit (use
  /bootstrap) or to pull a newer kit version or re-adapt it (use /update-kit) — this skill
  only removes or rolls the kit back.
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
effort: medium
---

# /teardown — clean up or uninstall the kit

You remove kit material from the project safely. Confirm the exact scope first, prefer
restoring from a backup over guessing, never touch app code, and report precisely what you
removed or restored.

Work top-to-bottom.

---

## Phase 0 — Detect what's installed and what backups exist

- **Kit present?** Look for `.claude/_kit/`, `.claude/PROJECT.md`, `.claude/.kit-manifest.json`,
  kit skills under `.claude/skills/` (e.g. `bootstrap`, `discover`, `implement`), and the
  `feature-flow-kit:begin/end` block in `CLAUDE.md`. (`.claude/.kit-incoming/`, if present, is a
  leftover `/update-kit` staging dir — safe to remove.)
- **Backups?**
  - Bootstrap snapshots: `.claude/.bootstrap-backup/<ts>/` (with `created.txt`).
  - Pre-copy backup the user made before copying the kit in: e.g. `.claude.bak/`,
    `CLAUDE.md.bak` (README "Quick start" step).
- **Git?** Run `git rev-parse --is-inside-work-tree` — if tracked, git is the safest restore
  path; surface it as an option.

Report what you found before asking anything.

## Phase 1 — Choose scope (ask)

Ask via `AskUserQuestion`:

- **Clean up leftovers** (default) — delete build-time material, keep the working config.
  → Phase 2.
- **Uninstall the kit** — return the project to its pre-kit state. → Phase 3.

## Phase 2 — Clean up leftovers

Show the exact list, confirm, then remove only build-time material:
`.claude/_kit`, `.claude/*.template.*`, `.claude/CLAUDE.snippet.md`,
`.claude/settings.stop-gate.example.json`, `.claude/.kit-incoming` (a leftover `/update-kit`
staging dir), and old `.claude/.bootstrap-backup/*` snapshots. **Keep** `.claude/.kit-manifest.json`
— it's working state `/update-kit` needs for the next version bump (remove it only on a full uninstall).

Do **not** touch the working config: `.claude/rules/`, `.claude/skills/`, `.claude/agents/`,
`.claude/hooks/`, `.claude/commands/`, `.claude/PROJECT.md`, `.claude/settings.json`,
`CLAUDE.md`. And **never** touch project-owned content the kit's skills helped *author* but does
not own — `CONTEXT.md`, `docs/adr/`, and the issues under the backlog: that's the project's
domain knowledge and work, like app code. Report what was removed.

## Phase 3 — Uninstall (restore the pre-kit state)

Pick the safest available path, in this order:

1. **Pre-copy backup present** (`.claude.bak/`, `CLAUDE.md.bak`) → confirm, then restore it
   wholesale: replace `.claude/` with the backup and `CLAUDE.md` with `CLAUDE.md.bak`. Offer
   to delete the `.bak` copies once the user confirms the project looks right.
2. **Under git** → don't delete blindly; show the user the commands and let them run them:
   - tracked files: `git checkout -- .claude CLAUDE.md`
   - preview untracked kit files: `git clean -nd .claude` → then `git clean -fd .claude` to remove.
3. **No backup, no git** → best-effort manual removal. Confirm the list first, then delete
   kit-installed paths: `.claude/_kit`, the kit skills/agents/hooks/commands, `rules/_generic/`
   and installed pack rules, `.claude/PROJECT.md`, `.claude/settings.json`, `*.template.*`,
   `CLAUDE.snippet.md`, `.claude/.kit-manifest.json`, `.claude/.kit-incoming`, `.bootstrap-backup/`;
   and strip the `feature-flow-kit:begin…end` block
   from `CLAUDE.md` (delete the file if the kit created it and it's now empty). Then strip the
   matching block from `.gitignore`: since this path has no backup, **copy `.gitignore` aside first
   (or show the diff and confirm)**, remove only the delimited block, and leave the rest intact.
   **Warn the user:** without a backup, project-owned files that shared a name with kit files
   can't be told apart — review the list before confirming.

Report what was restored or removed, and what (if anything) the user should check by hand.

---

## Hard rules

- **Confirm before deleting.** Always print the exact path list and get an explicit yes.
- **Never touch app code** — or project-owned docs the kit authored but doesn't own
  (`CONTEXT.md`, `docs/adr/`, backlog issues). Only `.claude/`, the kit's `CLAUDE.md` block, and
  the kit's delimited block in `.gitignore` (the rest of `.gitignore` is the project's — leave it).
- **Prefer restore over guess.** Use a backup or git first; manual removal is the last resort
  and is always flagged as best-effort.
- **Idempotent.** Re-running after a partial teardown just removes whatever still remains.

## See also

- **`/bootstrap`** — install and adapt the kit (the inverse of teardown).
- **`/update-kit`** — pull a newer kit version instead of removing; needs `.kit-manifest.json`,
  which "clean up leftovers" deliberately keeps.
