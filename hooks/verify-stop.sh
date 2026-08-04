#!/usr/bin/env bash
# Stop hook — OPT-IN, OFF BY DEFAULT, NON-BLOCKING.
# After a turn, if the working tree has uncommitted changes, optionally run the project's
# lint / targeted-test commands and SURFACE failures as a systemMessage. It NEVER blocks:
# it always exits 0 and never emits `decision:"block"` or exit 2, so it cannot break the
# interactive flow or trap the session in a Stop-retry loop. The user opts into verification;
# this hook only reports.
#
# DISABLED by default — two independent off-switches, both must be flipped to enable:
#   1. WIRING: the kit does NOT wire this hook in settings.template.json. To enable, merge the
#      "Stop" hook block from settings.stop-gate.example.json into your .claude/settings.json.
#   2. COMMANDS: LINT_CMD / TEST_CMD below are empty, so even if wired the hook is a no-op.
#      Fill them from PROJECT.md → Commands (`lint`, `test:targeted`). Leave one empty to
#      skip that check.

input=$(cat)
dir=$(printf '%s' "$input" | jq -r '.cwd // .workspace.current_dir // "."')

# Defensive: if Claude is already continuing from a prior Stop hook, do nothing (this hook
# never blocks, so a loop can't form — but exit early anyway, it's free).
[ "$(printf '%s' "$input" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0

# --- project commands (fill in when enabling; from PROJECT.md → Commands) ---
LINT_CMD=""          # e.g. "rubocop" / "ruff check ." / "yarn lint"
TEST_CMD=""          # e.g. "bundle exec rspec" / "pytest -q" / "yarn test"

# No-op unless at least one command is configured.
[ -z "$LINT_CMD" ] && [ -z "$TEST_CMD" ] && exit 0

# Only act when the turn left uncommitted changes (proxy for "edited code this turn").
[ -z "$(git -C "$dir" status --porcelain 2>/dev/null)" ] && exit 0

fails=""
run() {  # $1 label, $2 command
  [ -z "$2" ] && return 0
  if ! out=$( cd "$dir" && eval "$2" 2>&1 ); then
    fails="${fails}\n- ${1} failed (\`${2}\`):\n$(printf '%s' "$out" | tail -15)"
  fi
}
run "lint" "$LINT_CMD"
run "test" "$TEST_CMD"

[ -z "$fails" ] && exit 0

msg=$(printf 'verify-stop.sh (non-blocking): post-turn checks failed.%b\nNot blocked — fix before committing.' "$fails")
jq -n --arg m "$msg" '{"systemMessage": $m}'
exit 0
