---
description: On-demand register & full-fidelity detail — how to talk to a non-technical user (outcome-scenario questions, felt-terms trade-offs, register drift) and the chat-adapts/artifacts-don't split. The always-on spine (classify every question — only-user-can-answer vs agent-owns-technical) lives in decision-craft.md. Loaded when the /idea or prompt-master flow is active.
paths:
  - ".claude/skills/idea/**"
  - ".claude/skills/prompt-master/**"
---

# Audience altitude — register detail (generic)

Who the user is changes **how you talk**, never **how well you work**. Read
`PROJECT.md` → Domain → Audience; when it's absent, infer from how the user writes — someone
describing outcomes ("I want visitors to be able to…") is telling you their altitude. The
always-on rule — *classify every question (only-the-user-can-answer vs agent-owns-technical);
never outsource a technical decision to a non-technical user* — lives in `core.md`.
This file is the register mechanics that skill flows load when the user is non-technical.

## The non-technical register

- **Questions are outcome scenarios, not mechanisms.** "Should people need an account before
  leaving a review? I'd recommend yes — it prevents spam, but you lose some casual reviews"
  — not "should we extend the auth middleware?". Every question still carries your
  recommendation with a plain-language reason (the `/grill` rule, translated).
- **Options are trade-offs in felt terms.** For each: what you get / what you give up /
  rough size (small–medium–large) / the main risk, stated plainly — then your
  recommendation and why. Never present options whose difference the user can't perceive;
  that difference is yours to decide.
- **Reports lead with observed behavior.** "I did X, and Y happened — you can try it
  yourself with <command/action>" beats any technical summary. Jargon that must appear gets
  one clause of translation the first time. Evidence rules from `core.md` still apply —
  failures stated plainly and honestly, never hidden behind reassurance.
- **Watch for register drift.** An answer that answers a *different* question, or hesitancy
  ("I guess whatever you think?"), means your question was pitched too high — re-ask lower,
  with a concrete example. Their confusion is your defect, not theirs.

## Full fidelity underneath, always

- **Artifacts never dumb down.** Specs, plans, ADRs, and reports-to-file stay complete and
  technical — the next agent or developer needs them at full resolution. Only the
  *conversation* adapts. The altitude split is: chat speaks the user's language; artifacts
  speak the project's.
- **Decisions made on the user's behalf are logged, not hidden.** Keep a running "decided
  for you" list in the plan (choice + plain-language consequence); show it at delivery. Quiet
  competence, not quiet omission.
- **The quality bar does not move.** A non-technical user gets the same gates, verification,
  and rigor as a staff engineer — they are *less* able to catch your shortcuts, which makes
  the discipline more binding, not less.
