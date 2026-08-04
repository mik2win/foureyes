# Security Policy

FourEyes is a bundle of markdown instructions, shell hooks, and a stdlib-only Python validator. It
ships no service and no runtime dependencies — but it *does* run inside an agent that has your
shell, your filesystem, and your repository. That is where its security surface is.

## Supported versions

The latest release and the current `main`. There are no maintained release branches: fixes land on
`main` and go out in the next tag.

## What counts as a vulnerability here

Report it privately if you find any of the following:

- **A hook that can be made to run something it shouldn't.** `hooks/*.sh` receive attacker-shaped
  input — file paths, prompts, tool arguments — from the harness. Command injection, path escape,
  or unquoted expansion in a hook is a real vulnerability.
- **A `guard-bash.sh` bypass.** The kit denies `git add`/`commit`/`merge`/`push` and blocks
  destructive commands. A phrasing that slips past the guard defeats the kit's central promise:
  the agent never publishes code without you.
- **A `guard-secrets.sh` miss that leaks.** The hook is warn-only by design, so a *missed* secret
  pattern is a gap, not a breach — but a path where the hook itself writes a matched secret
  somewhere durable is a vulnerability.
- **Prompt injection through kit content.** A skill, rule, or agent brief that could be steered by
  repository content, a dependency's README, or fetched web text into exfiltrating code, weakening
  the publish guards, or acting outside the user's request.
- **Anything that makes the kit send your code off the machine** without an explicit user action.

## What is not a vulnerability

- **Claude Code harness bugs** — hooks not firing, permission prompts, MCP, plugins. Report those
  to [anthropics/claude-code](https://github.com/anthropics/claude-code/issues).
- **The agent doing something you didn't want** while operating inside the permissions you granted
  it. That's a bug or a prompt-quality issue — open a normal issue.
- **A warn-only hook warning too much or too little.** Warn-not-block is a deliberate contract
  (see [CONTRIBUTING.md](CONTRIBUTING.md)); tuning is a normal issue.

## How to report

**Do not open a public issue for a security report.**

Use GitHub's private reporting: go to the repository's **Security** tab → **Report a vulnerability**.
That opens a private advisory visible only to you and the maintainer.

Please include what you'd want to receive: the file and line, the input that triggers it, what an
attacker gains, and — if you have one — a minimal reproduction. A proof of concept that actually
runs is worth more than a description of one.

## What to expect

This is a single-maintainer project, so response is best-effort rather than contractual: an
acknowledgement within about a week, and a fix or an explicit "won't fix, here's why" once the
report is understood. You'll be credited in the release notes unless you'd rather not be.

Please give a reasonable window to ship a fix before disclosing publicly.
