---
description: Draft a well-formatted git commit message + command (does NOT run git add/commit)
argument-hint: [paths or scope hint]
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*)
---

Draft a clean git commit for the user to run. Per the user's global rule, you NEVER run
`git add` or `git commit` yourself — you only OUTPUT the message text and the command.

Scope hint: `$ARGUMENTS` (optional — paths or a topic to limit the commit to; empty means
everything this session changed).

Steps:

1. Run `git status --short` and `git branch --show-current`. If `PROJECT.md` → Conventions
   names a ticket convention and the branch carries a ticket (`CRM-84_combos` → `CRM-84`),
   take it from there. Never invent one; ask if the convention requires a ticket and the
   branch has none.
2. **Decide the file set, and list what you left out.** A working tree is often shared —
   parallel sessions, a colleague's in-progress edit, a stray generated file — so `git
   status` is not the commit. Include only files **this session** created or modified, plus
   anything the scope hint names; print the rest under `Left out — not this session's` so
   the user sees them and can disagree. **Stage by explicit path only**: never `-A`, never
   `.`, never a bare directory.
3. Read the diff of exactly that set (`git diff -- <paths>`, plus `git diff --cached --
   <paths>` for anything already staged; read new files in full). Analyse all of it, not
   just the last file.
4. Run `git log --format='%s' -15` and **match what you see**. The house style in the
   history wins over any default — its subject shape, its ticket prefix or absence of one,
   Conventional Commits (`<type>(<scope>): …`) or plain prose, its body convention. Only
   when the history is empty or has no discernible style, default to Conventional Commits
   (`feat, fix, refactor, test, docs, perf, chore, build, ci`) with a scope from
   `PROJECT.md` → Architecture.
5. Write the message: subject ≤ ~72 chars, imperative, no trailing period. Add a body only
   when the *why* is not obvious from the subject — what changed and why, in domain words,
   with any measured effect in its own line (`147 → 26 queries`). **The message describes
   the change, and only the change**: no plan, card, wave or research identifiers, no
   internal process labels. The next reader is someone doing `git log` in a year.
6. **Never a `Co-Authored-By` trailer, a "generated with" line, or any other tool or model
   byline.** The user is the author of the commit.
7. If the set mixes unrelated concerns, say so and propose one commit per concern — paths
   and message for each, in the order they should land.

Then OUTPUT, for the user to copy and run themselves — do not execute:

````
Files (N):
  path/one.py
  path/two.ts
Left out — not this session's (M): path/x.py   ← omit this line when empty

git add -- path/one.py path/two.ts && git commit -m "<subject>"
````

One pasteable line is the default — it is what actually gets used. When the message needs a
multi-line body, use the same single staging command followed by a heredoc:

````
git add -- <paths> && git commit -F - <<'MSG'
<subject>

<body>
MSG
````

Deleted files belong in the same `git add --` list (it stages deletions). A file that is
already staged still appears there — the command must be correct run on its own.

Do not run `git add`, `git commit`, `git push`, or anything else that changes the index, the
working tree or a remote. Stop after printing the message and the command; ask instead of
guessing when the file set is ambiguous.
