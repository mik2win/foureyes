#!/usr/bin/env bash
# PostToolUse/Write|Edit hook. After an edit to a wave board or to a plan a board cites,
# reports board findings (overlapping Owns, dangling deps, status drift) as additionalContext.
# Report-only: never blocks, never writes, always exits 0.
#
# Default OFF — /bootstrap wires it only for a project that keeps wave-structured boards.
# Register under PostToolUse with matcher "Write|Edit" in settings.json to enable.

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[ -z "$file" ] && exit 0

# The path filter lives here, in shell, deliberately: the overwhelming majority of edits are
# ordinary source files, and those must not pay for starting an interpreter. Widen the case to
# the project's own backlog and plans locations (PROJECT.md -> Plans / backlog) at bootstrap.
case "$file" in
  */RUN-ORDER.md|*/_backlog/*|*/backlog/*|*/.claude/plans/*) ;;
  *) exit 0 ;;
esac

root="${CLAUDE_PROJECT_DIR:-.}"
tool="$root/tools/lint-board.py"
[ -f "$tool" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

printf '%s' "$input" | (cd "$root" && python3 "$tool" hook 2>/dev/null) || true
exit 0
