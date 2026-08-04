#!/usr/bin/env bash
# SubagentStop hook. WARN-ONLY mechanical gate for the Finding Contract.
#
# When a finder/reviewer subagent finishes, check its final report for the contract
# every kit finder promises: (1) at least one `path:line` citation, (2) a severity
# marker. Output that flunks both is likely uncited opinion — flag it so the
# orchestrator treats the report as claims needing a second look, but NEVER block:
# many agents legitimately return prose, structured JSON, or "nothing found".
#
# Decision channels: always exit 0. On a miss, emit hookSpecificOutput JSON with a
# one-line systemMessage warning. Never exit 2 here — a blocked stop would loop the
# subagent on a style issue.
#
# Field names in the input JSON vary across Claude Code versions — parse defensively
# and exit 0 silently on anything unexpected.

command -v jq >/dev/null 2>&1 || exit 0
input=$(cat)

# The agent's final report. Prefer `last_assistant_message`, which SubagentStop delivers in the
# event itself: the transcript file is written asynchronously and MAY LAG, and on a lagging file
# the gate below exits silently — the check looks installed and never runs.
# Fall back to the agent's OWN transcript only. Never `.transcript_path`: that is the parent
# session's, so the fallback would gate the orchestrator's last message instead of the agent's
# report — a wrong pass, silently.
last=$(printf '%s' "$input" | jq -r '.last_assistant_message // empty' 2>/dev/null)

if [ -z "$last" ]; then
  transcript=$(printf '%s' "$input" | jq -r '.agent_transcript_path // empty' 2>/dev/null)
  [ -n "$transcript" ] && [ -f "$transcript" ] || exit 0
  last=$(jq -rs '
    [ .[] | select(.type? == "assistant") | .message.content
      | if type == "array" then (map(select(.type == "text") | .text) | join("\n")) else tostring end
    ] | last // empty' "$transcript" 2>/dev/null)
fi
[ -n "$last" ] || exit 0

# Heuristic: only reports that LOOK like finding lists are checked. Skip short
# answers, structured-output runs, and clean "no findings" reports.
printf '%s' "$last" | grep -qiE 'finding|critical|warning|issue|verdict|violation' || exit 0
[ "${#last}" -lt 400 ] && exit 0

has_citation=$(printf '%s' "$last" | grep -cE '[A-Za-z0-9_./-]+\.[A-Za-z]{1,4}:[0-9]+' || true)
has_severity=$(printf '%s' "$last" | grep -ciE 'critical|warning|suggestion|CONFIRMED|REFUTED|STALE|SOUND|SHORTCUT|HACK|severity' || true)

if [ "$has_citation" -eq 0 ] || [ "$has_severity" -eq 0 ]; then
  missing=""
  [ "$has_citation" -eq 0 ] && missing="path:line citations"
  [ "$has_severity" -eq 0 ] && missing="${missing:+$missing + }severity markers"
  jq -n --arg m "Finding Contract check (warn-only): subagent report has findings-like content but no $missing — treat its claims as unverified and spot-check before acting (rules/_generic/delegation.md)." \
    '{hookSpecificOutput:{hookEventName:"SubagentStop"},systemMessage:$m}'
fi
exit 0
