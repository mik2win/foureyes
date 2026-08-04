#!/usr/bin/env bash
# PreCompact hook. Fires right before context compaction (manual /compact or automatic — see
# .trigger), the moment multi-step state is most likely to be lost. Re-injects a short
# "what to preserve" checklist plus the live working state (branch, uncommitted summary,
# most-recent plan/backlog file) so the post-compaction context stays coherent. Mirrors the
# "Context compaction" section the kit merges into CLAUDE.md. Stack-agnostic, no project
# facts — safe to copy as-is.
#
# Output: emits the reminder via BOTH
#   - hookSpecificOutput.additionalContext  (documented field shape; for the model), and
#   - systemMessage                         (always surfaced to the user at compaction time).
# additionalContext is the documented injection field; the systemMessage guarantees the reminder
# is seen regardless of how the running Claude Code build treats PreCompact additionalContext.
# Unknown output fields are ignored by the harness, so emitting both is safe.
# ALWAYS exits 0 — a hook here must never block compaction.

input=$(cat)
dir=$(printf '%s' "$input" | jq -r '.cwd // .workspace.current_dir // "."')
trigger=$(printf '%s' "$input" | jq -r '.trigger // "auto"')

# --- live working state (cheap, like sessionstart.sh) ---
branch=$(git -C "$dir" branch --show-current 2>/dev/null)
stat=$(git -C "$dir" diff --stat HEAD 2>/dev/null | tail -1)
files=$(git -C "$dir" status --porcelain 2>/dev/null | sed 's/^...//' | head -10 | paste -sd ',' -)

# --- best-effort: most-recently-touched plan/backlog markdown (covers the template's
#     common Plans/backlog locations; "if discoverable", never authoritative) ---
plan=""
for d in "$dir/.claude/plans" "$dir/_backlog" "$dir/backlog" "$dir/docs/plans"; do
  [ -d "$d" ] || continue
  f=$(ls -t "$d"/*.md 2>/dev/null | head -1)
  [ -n "$f" ] && { plan="$f"; break; }
done

# --- build the preservation reminder ---
body="Context is about to be compacted (trigger: ${trigger}). Before the summary replaces the
transcript, make sure these survive in the post-compaction context — recorded in the active
plan/backlog file or CLAUDE.md, not only in the transcript:
  - active plan / backlog file path and the current step,
  - modified files and the latest test/lint status,
  - current branch + uncommitted-change summary,
  - open decisions / assumptions still unresolved.
If any of these are not already captured, record them now (or run /handoff for a durable snapshot)."

[ -n "$plan" ]   && body="${body}"$'\n'"Active plan (most recent): ${plan#$dir/}"
[ -n "$branch" ] && body="${body}"$'\n'"Branch: ${branch}.${stat:+ Uncommitted: ${stat}.}"
[ -n "$files" ]  && body="${body}"$'\n'"Changed files: ${files}"

jq -n --arg c "$body" '{
  systemMessage: $c,
  hookSpecificOutput: { hookEventName: "PreCompact", additionalContext: $c }
}'
exit 0
