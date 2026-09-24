#!/usr/bin/env bash
# SessionStart hook. Injects current branch and recent commit as system context.
# Stack-agnostic — no project facts. Safe to copy as-is.

input=$(cat)
dir=$(printf '%s' "$input" | jq -r '.workspace.current_dir // "."')

branch=$(git -C "$dir" branch --show-current 2>/dev/null)
[ -z "$branch" ] && exit 0

recent=$(git -C "$dir" log --oneline -1 2>/dev/null)
stat=$(git -C "$dir" diff --stat HEAD 2>/dev/null | tail -1)

# Commits that exist only locally. Silent when there is no upstream (a fresh or purely local
# branch is normal, not a finding) and when nothing is ahead. This lives here rather than in
# verify-stop.sh because that hook exits early on a clean tree — which is exactly the state a
# branch is in when it has unpushed commits and nothing else to report.
ahead=$(git -C "$dir" rev-list --count '@{u}..HEAD' 2>/dev/null)

msg="Branch: \`${branch}\`."
[ -n "$recent" ] && msg="${msg} Last commit: ${recent}."
[ -n "$stat" ] && msg="${msg} Uncommitted: ${stat}."
[ -n "$ahead" ] && [ "$ahead" -gt 0 ] 2>/dev/null && msg="${msg} Unpushed: ${ahead} commit(s) ahead of upstream."

# --- __BOOTSTRAP_EPIC_STATUS__ (default OFF — generic kit ships it commented) ---
# If the project has a tool that prints active-epic progress / status drift, /bootstrap wires
# its command here (PROJECT.md -> Plans / backlog, and Commands). Report-only: it must never
# block, never write, and must stay silent when the tool is absent or fails — a session banner
# that errors is worse than no banner. Keep the output to a few lines; this is a banner, not a
# report. Uncomment and replace both placeholders:
#
#if [ -f "$dir/__EPIC_STATUS_PROBE__" ]; then
#  epic=$(cd "$dir" && __EPIC_STATUS_CMD__ 2>/dev/null | head -4)
#  [ -n "$epic" ] && msg="${msg} Epics: ${epic}"
#fi
#
#   __EPIC_STATUS_PROBE__ = a path that must exist for the tool to be usable (the script or
#                           binary itself), so an un-bootstrapped copy stays silent.
#   __EPIC_STATUS_CMD__   = the one-line status command, with its own fallback if the primary
#                           runner may be missing, e.g. `<runner> <tool> status --oneline
#                           || <plain-interpreter> <tool> status --oneline`.
#
# The kit ships one such tool: `tools/lint-board.py`, for projects whose backlog is
# wave-structured (`<epic>/RUN-ORDER.md`). For those, the two placeholders are
# `tools/lint-board.py` and `python3 tools/lint-board.py status --oneline`. Its per-edit half
# is `hooks/lint-board.sh` (PostToolUse, also default OFF).

jq -n --arg m "$msg" '{"systemMessage": $m}'
exit 0
