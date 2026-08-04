#!/usr/bin/env bash
# UserPromptSubmit hook — OPT-IN, OFF BY DEFAULT, ADVISORY, NEVER BLOCKS.
#
# Why it exists: most kit skills are manual-by-default (`disable-model-invocation: true` —
# 39 of 46 at the time of writing; the terminal/verification five plus the two routers are
# invocable), so a concrete task request that has a perfect skill match can silently run bare:
# the user asks "check if epic is done? backlog/foo" and the session reconstructs
# /close-epic's checklist by hand instead of invoking it. `/which-skill` is the designed net
# but its own trigger fires on *meta* questions ("which skill should I use for…"), and a task
# request reads as work-to-do, not routing-to-do. This hook injects the candidate names as
# context; the model still decides. A hook cannot be reasoned past the way a description can.
#
# DISABLED by default — the kit does NOT wire this hook in settings.template.json.
# To enable, merge the "UserPromptSubmit" block from settings.skill-hint.example.json into
# your .claude/settings.json. Once wired, `SKILL_HINT_DISABLE=1` turns it off again without
# unwiring, and SKILL_HINT_MIN_SCORE / SKILL_HINT_MIN_HITS tune the threshold.
#
# Silence is the default outcome. It emits nothing when: nothing scores over the threshold,
# the prompt already names an installed skill (`/close-epic …` — the user routed themselves),
# no `.claude/skills/` exists, or `jq` is missing. It ALWAYS exits 0 — exit 2 on
# UserPromptSubmit would erase the user's prompt, which no advisory hook may ever do.
#
# Scoring is deliberately crude: lowercase word tokens of the prompt (≥4 chars, stopwords
# dropped) matched as substrings against each skill's frontmatter, weighted
#   3 = hit in `name`   ·   2 = hit in the TRIGGER clause   ·   1 = hit elsewhere in the
# description (the DO-NOT-TRIGGER clause is stripped first — it names *other* skills'
# territory and would otherwise pull every router word toward the wrong skill).
# Top 2 survive. Matching is English-token based, so a non-English prompt scores 0 on its own —
# see the optional synonym map below, which is how a non-Latin prompt gets scored at all.
# Every pipeline stage runs under LC_ALL=C on purpose: see the note above `tokens=`.
#
# Stack-agnostic, reads no project facts. Safe to copy as-is.

[ -n "$SKILL_HINT_DISABLE" ] && exit 0
command -v jq >/dev/null 2>&1 || exit 0

input=$(cat)
dir=$(printf '%s' "$input" | jq -r '.cwd // .workspace.current_dir // "."')
prompt=$(printf '%s' "$input" | jq -r '.prompt // empty')
[ -z "$prompt" ] && exit 0

skills_dir="$dir/.claude/skills"
[ -d "$skills_dir" ] || exit 0

MIN_SCORE=${SKILL_HINT_MIN_SCORE:-5}
MIN_HITS=${SKILL_HINT_MIN_HITS:-2}

plow=$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')

# Optional synonym map — the ONLY non-English-aware part, and it is off unless a map exists.
# Why: the tokenizer below is `tr -cs 'a-z0-9-'`, so a prompt in any non-Latin script tokenizes
# to nothing and the hook stays silent. Measured on four real prompts: three Russian ones scored
# 0, the English one matched correctly. The map fixes that WITHOUT making the shipped hook
# language-specific: each line is `<stem> <english terms…>`, and a stem found in the prompt
# appends its English terms to the text the tokenizer then sees.
#   - default path is per-project, so the kit ships with no map and behaves exactly as before;
#   - stems are matched as raw byte substrings, which is why they must be written lowercase and
#     unprefixed ("эпик" catches "эпика", "эпику");
#   - lowercasing above is ASCII-only (`tr` is byte-based), so a capitalised non-Latin word would
#     miss — perl does the Unicode fold when present, and its absence only costs a hint.
SYN=${SKILL_HINT_SYNONYMS:-$dir/.claude/hooks/skill-hint.synonyms}
if [ -f "$SYN" ]; then
  if command -v perl >/dev/null 2>&1; then
    pfold=$(printf '%s' "$prompt" | perl -CSD -pe '$_ = lc $_' 2>/dev/null) || pfold="$plow"
  else
    pfold="$plow"
  fi
  extra=$(awk -v p="$pfold" '
    /^[[:space:]]*#/ { next }
    NF < 2           { next }
    {
      # The stem is everything before the first run of 2+ spaces, so it may itself contain a
      # space ("не публик"). Splitting on $1 instead would reduce every multi-word stem to its
      # first token: measured 2026-08-03, the four "не …" stems all collapsed to "не" and
      # injected "diagnose incident debug failure" into any negated Russian prompt, displacing
      # the correct candidate. Lines aligned with a single space still work via the fallback.
      if (match($0, /  +/)) { stem = substr($0, 1, RSTART - 1); rest = substr($0, RSTART + RLENGTH) }
      else                  { stem = $1; rest = substr($0, index($0, " ") + 1) }
      sub(/[[:space:]]+$/, "", stem)
      if (stem != "" && rest != "" && index(p, stem) > 0) print rest
    }
  ' "$SYN" 2>/dev/null | tr '\n' ' ')
  [ -n "$extra" ] && plow="$plow $extra"
fi

# Prompt tokens: ≥4 chars, de-duplicated, minus filler that would match half the catalog.
stop='^(this|that|with|from|into|have|been|will|your|just|like|some|more|than|then|there|here|what|when|where|which|while|also|only|very|please|thanks|okay|well|make|made|need|want|does|doing|dont|cant|about|would|could|should|going|thing|things|really|maybe|again|still|much|many|over|them|they|were|because|after|before|http|https)$'
# LC_ALL=C makes the pipeline byte-oriented, and that is a correctness fix, not a micro-opt.
# `tr -cs 'a-z0-9-'` splits multibyte characters mid-sequence; under a UTF-8 locale the orphaned
# bytes make `sort` abort with "Illegal byte sequence" and the hook emits NOTHING — a silent,
# total failure on exactly the non-Latin prompts the synonym map exists to serve. Reproduced
# 2026-07-31: same prompt, hook works with LANG unset and dies with LANG=*.UTF-8.
tokens=$(printf '%s' "$plow" \
  | LC_ALL=C tr -cs 'a-z0-9-' '\n' \
  | awk 'length($0) >= 4' \
  | grep -Ev "$stop" \
  | LC_ALL=C sort -u \
  | paste -sd ' ' -)
[ -z "$tokens" ] && exit 0

# One awk pass over every installed SKILL.md frontmatter. `find` (not a glob) so a project
# with no skills, or hundreds, behaves the same; -maxdepth keeps it to the skill roots. The
# empty-list check is load-bearing: `xargs` with no arguments would invoke awk with no files
# and leave it reading stdin.
files=$(find "$skills_dir" -maxdepth 2 -name SKILL.md \( -type f -o -type l \) 2>/dev/null | head -200)
[ -z "$files" ] && exit 0

matches=$(printf '%s\n' "$files" \
  | tr '\n' '\0' | xargs -0 awk \
    -v toks="$tokens" -v plow="$plow" -v minscore="$MIN_SCORE" -v minhits="$MIN_HITS" '
# Substring hit, with a bounded stem so an inflected prompt word still reaches the root in
# the description ("crashes" -> "crash", "verification" -> "verif"). Only tokens of 6+ chars
# are stemmed, and only to 5 chars — never below the 4-char floor the tokenizer already
# enforces, so the stem cannot be looser than an accepted whole token.
function hit(text, i,   s) {
  if (index(text, tok[i]) > 0) return 1
  if (length(tok[i]) < 6) return 0
  s = substr(tok[i], 1, 5)
  return index(text, s) > 0
}
function finish(   d, t, p, i, w, sc, hi, ol) {
  if (nm == "" || desc == "") return
  # The user already routed themselves — say nothing at all this turn.
  #
  # Must be a COMMAND, not any occurrence of "/name". A bare index() reads a file path as
  # self-routing and silences the whole hook: measured 2026-07-31 on the ad-hoc corpus, a prompt
  # mentioning `src/tests/live` matched the skill named `test` and suppressed every candidate.
  # `src/test*` is near-universal, and skills named test/deps/perf/spike/sweep/idea are all
  # reachable this way — so the failure is silent, common, and looks exactly like "no match".
  # A command is preceded by start-of-line or whitespace and not followed by a name character.
  if (plow ~ ("(^|[ \t])/" nm "([^a-z0-9-]|$)")) { named = 1; return }
  d = desc
  p = index(d, "do not trigger");  if (p > 0) d = substr(d, 1, p - 1)
  t = ""
  p = index(d, "trigger when");    if (p > 0) { t = substr(d, p); d = substr(d, 1, p - 1) }
  sc = 0; hi = 0
  for (i = 1; i <= ntok; i++) {
    w = 0
    if      (hit(nm, i))            w = 3
    else if (t != "" && hit(t, i))  w = 2
    else if (hit(d, i))             w = 1
    if (w > 0) { sc += w; hi++ }
  }
  if (sc < minscore || hi < minhits) return
  ol = d
  gsub(/[ \t]+/, " ", ol); sub(/^ /, "", ol); sub(/ $/, "", ol)
  if (length(ol) > 110) ol = substr(ol, 1, 107) "..."
  n++; out[n] = sc "\t" nm "\t" ol
}
BEGIN { ntok = split(toks, tok, " ") }
FNR == 1 { if (!closed) finish(); infm = 0; closed = 0; nm = ""; desc = ""; key = "" }
closed { next }
/^---[[:space:]]*$/ { if (infm == 0) { infm = 1 } else { finish(); closed = 1 } next }
infm == 0 { next }
{
  if ($0 ~ /^[A-Za-z_][A-Za-z0-9_-]*:/) {
    key = tolower(substr($0, 1, index($0, ":") - 1))
    v = substr($0, index($0, ":") + 1); sub(/^[ \t]+/, "", v); sub(/[ \t]+$/, "", v)
    if (key == "name") nm = tolower(v)
    else if (key == "description" || key == "when_to_use") {
      if (v != ">-" && v != ">" && v != "|" && v != "|-") desc = desc " " tolower(v)
    }
    next
  }
  if ($0 ~ /^[ \t]+/ && (key == "description" || key == "when_to_use")) {
    v = $0; sub(/^[ \t]+/, "", v); desc = desc " " tolower(v)
  }
}
END {
  if (!closed) finish()
  if (named) exit 0
  for (i = 1; i <= n; i++) print out[i]
}' 2>/dev/null | LC_ALL=C sort -rn -k1,1 | head -2)

[ -z "$matches" ] && exit 0

body="Candidate skills for this request (advisory, from .claude/hooks/skill-hint.sh — matched on
skill descriptions, not on understanding):"
while IFS=$'\t' read -r _score name oneline; do
  [ -z "$name" ] && continue
  body="${body}"$'\n'"  /${name} — ${oneline}"
done <<EOF
$matches
EOF
body="${body}"$'\n'"Invoke one only if it genuinely fits what was asked; otherwise ignore this line and proceed."

# Name the local synonym map when it contributed, so a wrong candidate is traceable to the line
# that caused it. Without this the map's effect on scoring is invisible and "the map pulls the
# wrong way" can only be diagnosed by reading the awk by hand.
[ -n "$extra" ] && body="${body}"$'\n'"(Local synonym map added: ${extra} — edit ${SYN} to adjust.)"

jq -n --arg c "$body" '{
  hookSpecificOutput: { hookEventName: "UserPromptSubmit", additionalContext: $c }
}'
exit 0
