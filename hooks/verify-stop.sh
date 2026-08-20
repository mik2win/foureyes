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
# event so the same script is correct wired to Stop or to SubagentStop; unknown output fields are
# ignored by the harness, so emitting both channels is safe on older builds.
#
# Feedback to the model is sent once per distinct failure: additionalContext continues the turn,
# so re-sending the SAME failure at every Stop is how a warn-only hook would start ping-ponging
# with a failure the model cannot fix. The signature of the last-reported failure is remembered
# per session; an unchanged failure goes to the user only, a changed one is fed to the model
# again. `stop_hook_active` below should already cover this — the marker just does not depend
# on it.
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

# Same failure as last time in this session? Report to the user only — do not re-feed the model.
sid=$(printf '%s' "$input" | jq -r '.session_id // "unknown"' | tr -cd 'A-Za-z0-9._-')
marker="${TMPDIR:-/tmp}/verify-stop-${sid:-unknown}.last"
sig=$(printf '%s' "$fails" | cksum | tr -d ' ')

if [ "$sig" = "$(cat "$marker" 2>/dev/null)" ]; then
  jq -n --arg m "$msg" '{"systemMessage": $m}'
else
  printf '%s' "$sig" > "$marker" 2>/dev/null || true
  jq -n --arg m "$msg" --arg e "$event" '{
    systemMessage: $m,
    hookSpecificOutput: { hookEventName: $e, additionalContext: $m }
  }'
fi
exit 0
