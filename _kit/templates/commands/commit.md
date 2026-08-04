---
description: Draft a well-formatted git commit message + command (does NOT run git add/commit)
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*)
---

Draft a clean git commit for the user to run. Per the user's global rule, you NEVER run
`git add` or `git commit` yourself — you only OUTPUT the message text and the command.

Steps:

1. Run `git status` and `git diff --staged` (and `git diff` for unstaged) to see what
   would be committed. If nothing is staged, show the unstaged changes and note which
   files the user will need to stage.
2. Run `git log --oneline -10` to match the repo's existing commit style.
3. Write a Conventional Commits message: `<type>(<scope>): <subject>` under ~70 chars.
   - types: feat, fix, refactor, test, docs, perf, chore, build, ci.
   - scope: a module/area from `PROJECT.md` → Architecture (omit if unclear).
   - Honor any ticket-prefix convention from `PROJECT.md` → Conventions notes.
   - Do NOT add a `Co-Authored-By` trailer.
4. Add a short body only if the *why* isn't obvious from the subject.
5. If the change spans unrelated concerns, say so and suggest splitting into multiple
   commits (give a message + command per split).

Then OUTPUT, for the user to copy and run themselves — do not execute:

- The commit message in a fenced block.
- A ready-to-run command, e.g.:

  ```
  git add <paths>   # only if files still need staging
  git commit -m "<subject>" -m "<body>"
  ```

Do not run `git add`, `git commit`, or `git push`. Do not stage anything. Stop after
printing the message and command.
