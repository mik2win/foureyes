---
description: Create a GitLab merge request for the current branch
argument-hint: [target-branch]
allowed-tools: Bash(git status:*), Bash(git log:*), Bash(git diff:*), Bash(git branch:*), Bash(git push:*), Bash(glab mr create:*)
---

Create a GitLab merge request for the current branch.

Target branch: `$1` (default to `main` when no argument is given).

Steps:

1. Run `git status` and `git branch --show-current` to confirm the branch and a clean
   working tree. If there are uncommitted changes, stop and ask the user.
2. Run `git log <target>..HEAD --oneline` and `git diff <target>...HEAD --stat` to
   understand what the branch contains.
3. Push with `git push -u origin HEAD` if it has no upstream.
4. Derive the MR title from any ticket-prefix convention in `PROJECT.md` (e.g.
   `[XXX-NN]`) when present, followed by a concise summary.
5. Create the merge request. Prefer the GitLab MCP server when connected; otherwise use
   `glab mr create` with the target branch, title, and a description.
6. Write the description with a short summary, a bullet list of notable changes, and a
   test plan. Keep it factual, and never hard-wrap the prose — one paragraph is one line,
   the web UI wraps it.
7. Report the MR URL.

Do not merge. Do not force-push. Stop and ask if anything is ambiguous.
