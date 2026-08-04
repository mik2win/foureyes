---
description: Create a GitHub pull request for the current branch
argument-hint: [target-branch]
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch:*), Bash(git push:*), Bash(gh pr create:*)
---

Create a GitHub pull request for the current branch.

Target branch: `$1` (default to the repo's default branch when no argument is given).

Steps:

1. Run `git status` and `git branch --show-current`. If the working tree is dirty, stop
   and ask the user.
2. Run `git log <target>..HEAD --oneline` and `git diff <target>...HEAD --stat` to
   understand the branch contents.
3. Push with `git push -u origin HEAD` if there's no upstream.
4. Derive the title from the commits (honor any ticket-prefix convention from
   `PROJECT.md`), then a concise summary.
5. Create the PR with `gh pr create` (or the GitHub MCP server if connected). Body:
   **Summary**, a bullet list of notable **Changes**, and a **Test plan**. Keep it factual,
   and never hard-wrap the prose — one paragraph is one line, the web UI wraps it.
6. Report the PR URL.

Do not merge. Do not force-push. Stop and ask if anything is ambiguous.
