#!/usr/bin/env bash
# PreToolUse/Write|Edit hook. WARNS (never blocks) when a write looks like it introduces a
# hardcoded secret. Always exits 0 — a false positive must never block a legitimate write
# (see _kit/KIT.md, "Hook & permission configuration" -> the warn-not-block contract).
# It surfaces a systemMessage the user sees; the write proceeds either way.
#
# Patterns are intentionally conservative + high-signal (provider tokens, private-key
# headers). To turn one into a HARD BLOCK, move it into a branch that prints to stderr and
# `exit 2` — keep that set tiny and unambiguous (e.g. private-key headers only).

input=$(cat)

# New/added content only: Write → .content, Edit → .new_string.
content=$(printf '%s' "$input" | jq -r '.tool_input.content // .tool_input.new_string // empty')
[ -z "$content" ] && exit 0

hits=""
add()  { hits="${hits}\n  - $1"; }
scan() { printf '%s' "$content" | grep -Eiq -e "$1"; }

scan '-----BEGIN ([A-Z ]+ )?PRIVATE KEY-----'                        && add "private-key header"
scan 'AKIA[0-9A-Z]{16}'                                              && add "AWS access key id"
scan '\bghp_[0-9A-Za-z]{36}\b'                                       && add "GitHub personal access token"
scan '\bgithub_pat_[0-9A-Za-z_]{22,}\b'                              && add "GitHub fine-grained token"
scan '\bxox[baprs]-[0-9A-Za-z-]{10,}\b'                              && add "Slack token"
scan '\bsk_live_[0-9A-Za-z]{16,}\b'                                  && add "Stripe live secret key"
scan '\bAIza[0-9A-Za-z_-]{35}\b'                                     && add "Google API key"
scan 'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}' && add "JWT"

# Generic 'secret = "<literal>"' — only a real literal (≥16 chars, no spaces/quotes), not an
# env lookup or a <placeholder>. Conservative on purpose; filtered line-by-line.
if printf '%s' "$content" \
   | grep -Ei '(api[_-]?key|secret|token|password|passwd|client[_-]?secret)[[:space:]]*[:=][[:space:]]*["'\''][^"'\''[:space:]]{16,}["'\'']' \
   | grep -Eiv '(process\.env|os\.environ|ENV\[|getenv|<[^>]+>|\$\{|example|dummy|changeme|placeholder|redacted|xxxx|\*\*\*\*)' >/dev/null; then
  add "hardcoded credential assignment"
fi

[ -z "$hits" ] && exit 0

msg=$(printf 'guard-secrets.sh: this write may contain a secret:%b\nMove it to env / a secret store and keep it out of VCS (rules/_generic/code.md). NOT blocked — verify before committing, and rotate if it already leaked.' "$hits")
jq -n --arg m "$msg" '{"systemMessage": $m}'
exit 0
