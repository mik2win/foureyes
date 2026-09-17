[← README](../../README.md) · **English** · [Русский](../ru/install.md)

# Install, update, remove

## Integrate into a new project

> **First install only.** The raw copy below is for a project that has **not** been bootstrapped yet. To pull a *newer* kit version into a project you already bootstrapped, do **not** re-copy by hand — use **`/update-kit`** (see [Update the kit](#update-the-kit)); it preserves your adaptations.

Run steps 1–4 from anywhere *except* inside `<project>`, replacing `<project>` with your project's path. Already have a clone of this repo? Use its path in step 3 and skip steps 1 and 4.

```bash
# 1. Clone the kit to a temporary location — NOT inside your project
git clone https://github.com/mik2win/foureyes.git /tmp/foureyes

# 2. (existing project) back up anything the kit might overwrite, so you can fully restore later
[ -e <project>/.claude ]   && cp -r <project>/.claude <project>/.claude.bak
[ -f <project>/CLAUDE.md ] && cp <project>/CLAUDE.md <project>/CLAUDE.md.bak

# 3. Copy the kit's contents into the project's .claude/ (skip git and repo infrastructure)
rsync -a --exclude='.git' --exclude='.claude' --exclude='_backlog' --exclude='tools' \
  --exclude='guide' --exclude='.github' --exclude='LICENSE' --exclude='CONTRIBUTING.md' \
  --exclude='CHANGELOG.md' --exclude='CODE_OF_CONDUCT.md' --exclude='SECURITY.md' \
  --exclude='.gitignore' \
  /tmp/foureyes/ <project>/.claude/

# 4. Drop the clone — the kit now lives in your project
rm -rf /tmp/foureyes
```

To undo everything up to this point: `rm -rf <project>/.claude && mv <project>/.claude.bak
<project>/.claude`, plus `mv <project>/CLAUDE.md.bak <project>/CLAUDE.md` if you backed one up.

5. Open the project in Claude Code and run **`/bootstrap`**. It will:
   - back up the files it's about to change, then detect empty vs existing and scan the stack;
   - draft `.claude/PROJECT.md` (asking you for domain + anything ambiguous);
   - select rule packs from `_kit/rules-library/` matching the stack;
   - on an existing codebase, **reconcile** each pack's assumptions vs the real code and ask how to resolve divergences (adopt / relax / skip);
   - generate `.claude/rules/`, `settings.json`, git commands, and wire `CLAUDE.md`;
   - ask **keep or roll back**, then **clean up** `_kit/` and `*.template.*`.
6. Smoke-test: run `/analyst` (it interviews from the profile's domain) and the profile's `test` command. On an existing project, also check `git diff` on `CLAUDE.md` and `.gitignore` — `/bootstrap` merges a block into each rather than replacing them, and that merge is the one thing worth reading with your own eyes.

## Update the kit

When the kit gets a newer version and you want it in a project you **already bootstrapped** — without losing skills you adapted, your `PROJECT.md`, `CONTEXT.md`, ADRs, or backlog — use **`/update-kit`** instead of re-copying:

```bash
# 1. Clone the new version to a temporary location
git clone https://github.com/mik2win/foureyes.git /tmp/foureyes

# 2. Stage it inside the project (skip git + repo infrastructure)
rsync -a --exclude='.git' --exclude='.claude' --exclude='_backlog' --exclude='tools' \
  --exclude='guide' --exclude='.github' --exclude='LICENSE' --exclude='CONTRIBUTING.md' \
  --exclude='CHANGELOG.md' --exclude='CODE_OF_CONDUCT.md' --exclude='SECURITY.md' \
  --exclude='.gitignore' \
  /tmp/foureyes/ <project>/.claude/.kit-incoming/

# 3. Drop the clone
rm -rf /tmp/foureyes
```
Then open the project in Claude Code and run **`/update-kit`** (or `/update-kit <path-to-new-kit>` and it stages for you). In one pass it:
- reads `.claude/.kit-manifest.json` (the install baseline) and does a **3-way merge** — BASE (what the kit shipped) vs MINE (your file) vs THEIRS (the new version) — so untouched files update silently and you're asked **only on real conflicts** (take-new / keep-mine / merge); BASE is always the file as the kit shipped it, so an adapted file stays yours until the kit changes it, and a kit file you removed on purpose can be **excluded** for good instead of coming back on every update;
- **never touches** project-owned files (`PROJECT.md`, `CONTEXT.md`, `docs/adr/`, the backlog, or skills you created) — they aren't in the kit source, so the merge can't reach them;
- **re-adapts inline** (no separate `/bootstrap`): regenerates `settings.json`, `guard-bash.sh`, the `CLAUDE.md`/`.gitignore` blocks, and re-reconciles rule packs against the new version;
- backs up first and asks **keep or roll back**, then writes a fresh manifest.

Detection is hash-based, so it works even when `.claude/` is in `.gitignore` (git is not used). A *legacy* project with no manifest yet falls back to a noisier 2-way diff once, then writes a manifest so future updates are quiet.

## Remove the kit

Run **`/teardown`** and pick a scope:
- **Clean up leftovers** — delete build-time material (`_kit/`, `*.template.*`, `CLAUDE.snippet.md`, old `.bootstrap-backup/` snapshots), keep the working config.
- **Uninstall** — restore the project to its pre-kit state from the `.claude.bak/` / `CLAUDE.md.bak` backup (or, under git, `git checkout -- .claude CLAUDE.md && git clean -fd .claude`).

Bootstrap is reversible on its own too: it backs up before writing and asks **keep or roll back** at the end, so a rejected run leaves no trace.
