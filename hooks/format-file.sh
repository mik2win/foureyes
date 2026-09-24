#!/usr/bin/env bash
# PostToolUse/Write|Edit hook. Auto-formats the file Claude just wrote.
# Best-effort, never blocks. Always exits 0.
#
# Generic defaults below run a formatter only if it's installed (command -v guard).
# /bootstrap may replace this with the project's exact `format` command from PROJECT.md.

input=$(cat)
file=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')
[ -z "$file" ] && exit 0
[ -f "$file" ] || exit 0

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

has() { command -v "$1" >/dev/null 2>&1; }

case "$file" in
  *.rb)
    if has bundle; then bundle exec rubocop -a --no-color "$file" >/dev/null 2>&1 || true
    elif has rubocop; then rubocop -a --no-color "$file" >/dev/null 2>&1 || true; fi
    ;;
  *.py)
    # --unfixable F401: an import written before its first use looks unused to ruff, and the
    # autofix deletes it — the code then ships a call with no import that only fails at runtime.
    if has ruff; then ruff format "$file" >/dev/null 2>&1 && ruff check --fix --unfixable F401 "$file" >/dev/null 2>&1 || true
    elif has black; then black "$file" >/dev/null 2>&1 || true; fi
    ;;
  *.ts|*.tsx|*.js|*.jsx|*.css|*.scss|*.json|*.md)
    if has prettier; then prettier --write "$file" >/dev/null 2>&1 || true
    elif has npx; then npx --no-install prettier --write "$file" >/dev/null 2>&1 || true; fi
    ;;
  *.go)
    has gofmt && gofmt -w "$file" >/dev/null 2>&1 || true
    ;;
  *.rs)
    has rustfmt && rustfmt "$file" >/dev/null 2>&1 || true
    ;;
esac

exit 0
