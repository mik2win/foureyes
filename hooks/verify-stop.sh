#!/usr/bin/env bash
# Stop hook — OPT-IN, OFF BY DEFAULT, NON-BLOCKING.
# After a turn, if the working tree has uncommitted changes, optionally run the project's
# lint / targeted-test commands and SURFACE failures. It NEVER blocks: it always exits 0 and
# never emits `decision:"block"` or exit 2, so it cannot break the interactive flow or trap the
# session in a Stop-retry loop. The user opts into verification; this hook only reports.
#
# Output: emits the failure text via BOTH
#   - systemMessage                         (surfaced to the user), and
#   - hookSpecificOutput.additionalContext  (fed to the model, turn continues).
# Since Claude Code v2.1.163, Stop and SubagentStop hooks may return additionalContext to give
# Claude feedback and keep the turn going *without* being labeled a hook error — so reporting to
# the user alone is no longer forced. Warn-not-block is unchanged: additionalContext is feedback,
# not a decision, and this hook still exits 0 and never emits `decision:"block"`. The model may
# act on the failure or not; nothing here compels a retry. `hookEventName` echoes the incoming
# event, but wire this hook to **Stop only**: on SubagentStop the harness delivers
# additionalContext to the subagent that just stopped — not to the orchestrator such text
# addresses — and resumes that agent's turn (measured 2026-08-21 on 2.1.220). Unknown output
# fields are ignored by the harness, so emitting both channels is safe on older builds.
#
# A warn-only hook must not ping-pong with a failure the model cannot fix. The guard is
# `stop_hook_active` below: a turn already continuing from a Stop hook exits early, so the same
# failure is not fed back round after round. This covers the additionalContext path too, which is
# not obvious — the flag and its cap (`stop_hook_block_count`, `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`)
# are built around *blocking* continuations, and additionalContext is not a block. Measured
# 2026-08-21 on 2.1.220: the Stop event ending a turn that additionalContext continued carries
# `stop_hook_active: true`, so this hook speaks at most once per chain. It therefore needs no
# dedup state of its own, and keeps none.
#
# DISABLED by default — two independent off-switches, both must be flipped to enable:
#   1. WIRING: the kit does NOT wire this hook in settings.template.json. To enable, merge the
#      "Stop" hook block from settings.stop-gate.example.json into your .claude/settings.json.
#   2. COMMANDS: LINT_CMD / TEST_CMD below are empty, so even if wired the hook is a no-op.
#      Fill them from PROJECT.md → Commands (`lint`, `test:targeted`). Leave one empty to
#      skip that check.

input=$(cat)
dir=$(printf '%s' "$input" | jq -r '.cwd // .workspace.current_dir // "."')
event=$(printf '%s' "$input" | jq -r '.hook_event_name // "Stop"')

# Defensive: if Claude is already continuing from a prior Stop hook, do nothing. This hook never
# blocks, so the blocking loop cannot form; the additionalContext path is the unverified one above.
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

jq -n --arg m "$msg" --arg e "$event" '{
  systemMessage: $m,
  hookSpecificOutput: { hookEventName: $e, additionalContext: $m }
}'
exit 0
