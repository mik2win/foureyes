#!/usr/bin/env bash
# PreToolUse/Bash hook. Blocks or gates dangerous commands.
#
# Decision channels (Claude Code hook spec):
#   exit 2                          -> HARD BLOCK; stderr is shown to Claude. Irreversible / code-publish actions.
#   stdout JSON permissionDecision  -> "ask" = force a confirm prompt even under auto-accept / bypass mode.
#   exit 0 (no output)              -> allow; normal permission flow continues.
# (exit 1 is non-blocking — the command still runs — so it is never used here.)
#
# The universal blocks and the ask-tier below are stack-agnostic. /bootstrap injects project-specific
# blocks (forbidden package managers, server start, destructive db tasks, precious gitignored dirs)
# into the marked regions from PROJECT.md.

input=$(cat)
command=$(printf '%s' "$input" | jq -r '.tool_input.command // empty')
[ -z "$command" ] && exit 0

block() {
  echo "BLOCKED by .claude/hooks/guard-bash.sh: $1" >&2
  echo "This command is prohibited. Do not retry it without explicit user approval." >&2
  exit 2
}
# ask: force a confirmation prompt even under auto-accept / --dangerously-skip-permissions.
# Use for reversible-but-risky actions that would discard uncommitted work.
ask() {
  jq -n --arg r "$1" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"ask",permissionDecisionReason:$r}}'
  exit 0
}

# `rm` as a command word (matches /bin/rm, /usr/bin/rm too); recursive flag in any spelling.
rm_re='(^|[^[:alnum:]_])rm([[:space:]]|$)'
rec_re='(^|[[:space:]])(-[a-zA-Z]*[rR]|--recursive)'
# Bare root / home target (allows rm -rf ~/.cache, blocks rm -rf ~ and rm -rf /).
root_re='([[:space:]]|^)(/|/\*|~|~/|~/\*|\$HOME|\$HOME/|\$HOME/\*)([[:space:]]|$)'

# --- Universal hard blocks (always on) ---
# Recursive force-delete of a root/home path, in any rm spelling (rm -rf /, rm -fr ~, /bin/rm --recursive /).
if printf '%s' "$command" | grep -qE "$rm_re" \
   && printf '%s' "$command" | grep -qE -- "$rec_re" \
   && printf '%s' "$command" | grep -qE "$root_re"; then
  block "recursive force-delete of a root/home path"
fi
case "$command" in
  *"git push --force"*|*"git push -f "*)
    block "force-push (use --force-with-lease and user approval)" ;;
  *"git reset --hard origin/"*)
    block "hard reset to a remote ref discards local work" ;;
esac
# Destructive SQL (case-insensitive).
if printf '%s' "$command" | grep -qiE 'DROP[[:space:]]+(TABLE|DATABASE)|TRUNCATE[[:space:]]+TABLE|DELETE[[:space:]]+FROM.*WHERE[[:space:]]+(1=1|true)'; then
  block "destructive SQL (DROP/TRUNCATE/unbounded DELETE)"
fi
# `git clean -x` / `-X` deletes GITIGNORED files — local databases, caches, build output, .env.
# Not domain-specific and NOT covered by the CLI's built-in gate, which confirms plain `git clean`
# (untracked files, usually recoverable) without distinguishing the -x/-X spellings that also take
# out everything git was told to ignore. That set is by definition not in version control.
if printf '%s' "$command" | grep -qE 'git[[:space:]]+clean' \
   && printf '%s' "$command" | grep -qE '(^|[[:space:]])-[a-zA-Z]*[xX]'; then
  block "git clean -x/-X deletes gitignored files (local DBs, caches, .env) — they are not in version control"
fi

# --- __VCS_PUBLISH_BLOCKS__ (default ON — suggest-only) ---
# Code must not leave the machine (stage/commit/merge/push) without explicit user action.
# The agent OUTPUTS these commands for the user to run; it never runs them itself.
# /bootstrap relaxes this region per the "VCS / code-publish policy" survey (e.g. a team that
# lets the agent commit locally but never push). Read-only git (status/diff/log/branch) is allowed.
case "$command" in
  *"git add"*)     block "git add — the user stages code themselves; output the command, don't run it" ;;
  *"git commit"*)  block "git commit — output the message + command for the user; do not commit" ;;
  *"git merge"*)   block "git merge — integrating code is the user's call; propose it, don't run it" ;;
  *"git push"*)    block "git push — never publish code to a remote without explicit user action" ;;
esac

# --- Ask-tier: reversible-but-risky, discards uncommitted work ---
# RECONCILED with Claude Code's built-in destructive-command protection (2026): the CLI
# itself now confirm-gates `git reset --hard`, `git checkout -- / .`, `git restore`,
# `git clean`, and similar work-discarding commands — a hook `ask` on top produced a
# DOUBLE prompt for the same action. The kit therefore keeps only what built-ins do NOT
# cover: `git stash drop/clear` (permanent stash loss). Running on an older CLI without
# built-in protection? Uncomment the fallback block below.
printf '%s' "$command" | grep -qiE 'git[[:space:]]+stash[[:space:]]+(drop|clear)' && ask "git stash drop/clear permanently discards stashed work — confirm"
# Fallback for CLIs without built-in destructive-command protection — uncomment to restore:
#printf '%s' "$command" | grep -qiE 'git[[:space:]]+reset[[:space:]]+--hard'     && ask "git reset --hard discards working-tree changes — confirm"
#printf '%s' "$command" | grep -qiE 'git[[:space:]]+checkout[[:space:]]+(--|\.)' && ask "git checkout -- / . discards uncommitted changes — confirm"
#printf '%s' "$command" | grep -qiE 'git[[:space:]]+restore\b'                   && ask "git restore discards uncommitted changes — confirm"
#printf '%s' "$command" | grep -qiE 'git[[:space:]]+clean'                       && ask "git clean removes untracked files (with -x/-X, gitignored files too) — confirm"

# --- __BOOTSTRAP_PROJECT_BLOCKS__ ---
# /bootstrap appends project-specific arms here, e.g.:
#   *"npm "*|"npx "*)  block "use the project package manager" ;;
#   *"rails server"*)  block "do not start the server" ;;
#
# BLOCK LIBRARY — copy the ones that match what this project actually has, then edit the
# file/dir patterns to the real names. Each protects something that is *gitignored and therefore
# unrecoverable*, which is exactly what the universal blocks above do NOT cover: they guard the
# filesystem and the remote, not this project's precious local state.
#
# 1. rm touching a local database file (adjust the extensions to the engine in use; the -wal/-shm
#    companions matter — deleting one corrupts the set):
#if printf '%s' "$command" | grep -qE "$rm_re" \
#   && printf '%s' "$command" | grep -qiE '\.(db|sqlite3?)(-wal|-shm)?([^[:alnum:]]|$)'; then
#  block "rm referencing a local database file — it is gitignored and cannot be recovered"
#fi
#
# 2. In-place truncation / overwrite of that same database — `> x.db` destroys it as thoroughly
#    as `rm` does, and reads as a harmless redirect:
#if printf '%s' "$command" | grep -qiE '(>[[:space:]]*[^|&;[:space:]]*\.db|truncate[[:space:]].*\.db|cp[[:space:]]+/dev/null[[:space:]].*\.db)'; then
#  block "in-place truncation/overwrite of a local database file"
#fi
#
# 3. Recursive rm of a gitignored data directory — name the project's own (caches, downloaded
#    datasets, generated results, model artifacts, backups):
#if printf '%s' "$command" | grep -qE "$rm_re" \
#   && printf '%s' "$command" | grep -qE -- "$rec_re" \
#   && printf '%s' "$command" | grep -qE '(^|[^[:alnum:]_])(<dir1>|<dir2>|<dir3>)([/[:space:]"'"'"']|$)'; then
#  block "recursive rm of a gitignored data dir — unrecoverable"
#fi
#
# 4. Deploy / restart targets — ask, not block: legitimate, but never a side effect of some other
#    task. Match the project's real entry points (make targets, a deploy CLI, a restart script):
#printf '%s' "$command" | grep -qiE '(make|just)[[:space:]]+(deploy|push|rebuild|restart)' && ask "this touches the live environment — confirm"

exit 0
