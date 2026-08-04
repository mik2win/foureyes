# Prompt patterns — anatomy, discipline, and Opus/Sonnet technique notes

Reference for `/prompt-master` Phase 4 — a run that stops at the pipeline sketch (Phase 3) never
opens it. Every generated prompt follows the anatomy below;
the discipline list is the methodology each prompt encodes; the technique notes adjust for
models that follow instructions literally rather than inferring intent.

---

## The anatomy — 7 sections, in order

Every generated prompt contains these sections (markdown headers or bold labels — keep the
structure visible, models key off it):

1. **Role & mission** — one sentence: who the model is for this phase and the single
   outcome that defines success. Scope the role to the phase ("senior analyst writing a
   spec"), not to the whole project.

2. **Context** — the facts the model must not guess: stack, architecture shape, real
   commands (test/lint/run), the domain vocabulary that applies, and **"Read these
   first:"** — the artifact files from earlier prompts, by path, in reading order. In kit
   mode this can be short ("read `.claude/PROJECT.md`, then <artifacts>"); in standalone
   mode inline every fact the phase needs.

3. **Task** — what THIS phase produces, stated as a deliverable, with the smallest useful
   slice named and out-of-scope named. One phase per prompt; never "and then also…".

4. **Method** — numbered steps of the discipline for this phase (drawn from the pipeline
   entry + the discipline list below). This is the section that replaces the stronger
   model's judgment — make each step checkable ("grep for X before proposing Y"), not
   aspirational ("think carefully").

5. **Guardrails** — the DO-NOT list: the anti-patterns this phase is prone to (see the
   catalog below). 3–6 items; a long list dilutes.

6. **Output contract** — the exact artifact: file path, section structure, and the
   per-claim evidence format (e.g. "every reuse claim cites `path:line`"). If the phase
   also reports to the user, say what the final message must lead with.

7. **Stop condition** — where the phase ends: "Do NOT start <next phase's work>. Hand
   back: the artifact path, open questions O-1…, and how to verify this phase's output."
   The user is the gate between prompts — the stop condition is what makes that possible.

## The discipline — what every pack encodes

Distilled from how this kit works; spread these across Method/Guardrails sections where
the phase makes them relevant:

- **Look before you ask.** Anything the repo, docs, or artifacts can answer, the model
  answers itself and cites; it asks the user only intent, priorities, trade-offs.
- **One question at a time, with a recommendation.** Interview prompts never batch
  questions, and every question carries a suggested answer + reason.
- **Surface assumptions; never silently assume.** Every artifact ends with explicit
  "Assumptions" and "Open questions" lists.
- **Evidence gate.** Reuse/impact/root-cause claims cite `path:line`; an uncited claim is
  dropped or verified before it enters an artifact.
- **Smallest useful slice.** Scope is minimal-but-useful, out-of-scope is written down,
  and gold-plating is a named guardrail.
- **Plan before code; decompose into independently verifiable steps.** Implementation
  prompts execute a written plan step by step and track deviations from it explicitly.
- **Verify by exercising behavior.** Done = the affected flow was driven end-to-end (run
  the real commands from Context), not "it compiles" or "tests should pass".
- **Report outcome first, faithfully — and readably.** Final messages lead with what
  happened; failures are reported plainly with output, never smoothed over. Readability
  beats brevity: complete sentences, terms spelled out, shortness achieved by *dropping*
  what doesn't change the reader's next action — never by compressing into fragments,
  abbreviations, or `A → B → fails` arrow chains.
- **Blend into the codebase.** New code matches the surrounding naming, idiom, and
  comment density. Comments state only constraints the code can't show — never narrate
  what changed or argue the change is correct.
- **Brake before irreversible.** Before a delete, migration, drop, or config change:
  check the evidence supports that *exact* action and look at the target first. Any
  destructive or outward-facing step sits behind an explicit user gate — never inside an
  autonomous run.
- **Don't re-litigate settled decisions.** Prior ADRs, specs, and user answers stand
  unless new evidence appears; a conflict is surfaced to the user, not silently
  re-decided.
- **Artifacts are the memory.** Each phase reads the prior artifacts and writes its own;
  nothing load-bearing lives only in conversation.

## Opus/Sonnet technique notes

Adjustments for models that execute literally and drift without rails:

- **Structure over prose.** Explicit sections/numbered steps outperform paragraphs of
  intent. For long context blocks, XML-style tags (`<context>…</context>`,
  `<artifact>…</artifact>`) keep boundaries unambiguous.
- **Checkable steps.** "Run `<test command>` and paste the failing output" beats "make
  sure tests pass". If a step can't be verified from the transcript, rewrite it.
- **Stop conditions are load-bearing.** Weaker models over-run into the next phase or
  "helpfully" refactor along the way. State the brake twice: in Task (out-of-scope) and
  in Stop condition.
- **Positive instructions beat negations** for behavior ("modify only files listed in the
  plan" > "don't touch other files") — keep Guardrails for the true anti-patterns.
- **Show the format, don't describe it.** When the artifact's shape matters, put a 2–5
  line example inside the Output contract — a small few-shot sample beats a paragraph of
  format description for these models.
- **No meta-references.** A prompt must not mention prompt-master, "the previous prompt",
  or this kit's internals (standalone mode) — only artifact paths and the task.
- **Fresh session per prompt.** The pack's how-to-run says so; long single sessions decay
  and the artifact chain makes them unnecessary.
- **Every word load-bearing.** The best prompt is not the longest; after drafting, cut
  anything that doesn't change what the model does. If a section restates another, merge.

## Anti-pattern catalog (pick 3–6 per prompt's Guardrails)

- **Research phases:** answering from memory instead of the repo; summarizing without
  `path:line` citations; expanding scope of the question.
- **Spec/interview phases:** batching questions; accepting vague answers; writing HOW
  into a WHAT document; inventing domain terms not in the glossary.
- **Planning phases:** steps that aren't independently verifiable; plans that skip
  migration/rollback; no explicit out-of-scope.
- **Implementation phases:** drive-by refactoring; skipping plan steps silently instead of
  recording a deviation; claiming done without running the verify commands; comments that
  narrate the change instead of stating a constraint; destructive steps (deletes, drops,
  force operations) without an explicit user gate; committing (if the project forbids it —
  carry the project's git policy into the prompt).
- **Verify/review phases:** rubber-stamping ("looks good"); findings without a concrete
  failure scenario; fixing while reviewing.

## Worked micro-example (standalone mode, plan phase, abbreviated)

```markdown
## Role
You are a senior engineer producing an implementation plan. Success = a plan another
engineer could execute without asking you anything.

## Context
Rails 7 app, layers: controllers → services → models (dependency direction inward).
Tests: `bin/rails test`. Read first: `plans/2026-07-08-billing-spec.md` (the spec —
US-n/AC-n ids are the requirements), `CONTEXT.md` (glossary).

## Task
Plan the implementation of US-1..US-4 only. Out of scope: US-5 (deferred), any schema
change beyond the spec's Domain model section.

## Method
1. Map each US-n to the modules it touches; verify each mapping by reading the file and
   cite `path:line`.
2. Order steps by dependency; each step names its files, its verify command, and the
   AC-n it advances.
3. End with Assumptions and Open questions lists.

## Guardrails
- No step may bundle two concerns "while we're there".
- An uncited module mapping is a guess — verify or drop it.

## Output contract
Write `plans/2026-07-08-billing-plan.md`: Steps (numbered, file list + verify command +
AC-n each) · Risks · Assumptions · Open questions.

## Stop
Do NOT write code. Hand back the plan path and the open questions.
```
