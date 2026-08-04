---
name: prompt-master
disable-model-invocation: true
description: >-
  Compile a raw idea (feature, refactor, migration, bug hunt, research) into a sequenced
  pack of copy-paste-ready prompts for Opus/Sonnet-class models — one prompt per
  development phase (research → spec → plan → implement → verify), each self-contained,
  grounded in the project's real facts, and chained through artifact files so the
  methodology survives fresh sessions and less self-driving models.
  TRIGGER when: the user wants prompts to run later or elsewhere ("generate prompts for
  this idea", "prompt pack", "how would I drive Opus/Sonnet through this", "разложи идею
  на промпты"), or wants a phased prompt plan instead of doing the work now; ALSO when the
  input is a whole surface rather than one change ("audit this whole area", "review every
  screen", "map all of X and tell me what to fix") — that is the program pass, and it is
  authored here, not by /prepare.
  DO NOT TRIGGER when: the user wants the work done in THIS session (route via
  /which-skill or run the pipeline skills directly), wants a spec (/analyst), a plan
  (/prepare), or a single question answered (just answer it).
allowed-tools: Read, Grep, Glob, Bash, WebSearch, AskUserQuestion, Write, Agent
effort: high
---

# Prompt Master

Turn an idea into a **prompt pack**: an ordered sequence of prompts, one per development
phase, that a user can paste into Opus/Sonnet-class sessions and get the same disciplined
flow this kit runs natively — research before deciding, spec before planning, plan before
code, verify before done. You do NOT do the work itself; you write the prompts that make
another model do it well. Idea: `$ARGUMENTS` (if empty, ask what to compile, then stop
until answered).

Why this exists: stronger models self-drive the methodology; weaker ones need it **written
into every prompt** — explicit method steps, guardrails, an output contract, and a stop
condition. Each generated prompt must be runnable in a *fresh session* with nothing but
the pack and the artifact files earlier prompts produced.

**Two shapes come out of here.** The usual one is the phase chain above — one coherent
change, one prompt per phase. The other is the **program pass** (tier 1): a whole-surface
discovery sweep that ends in evidence files and *cards*, which `/prepare` then turns into
plans. Same skill, different pipeline — see *Program packs* below and
`references/pipelines.md` § 7. Deciding which one applies is Phase 1's job.

## Phase 0 — Ground (optional, don't block)

Works with or without a kit profile:

- If `.claude/PROJECT.md` exists, read it and hold: **Domain** (vocabulary, roles),
  **Stack & Architecture** (layers, dependency direction), **commands** (test, lint, run),
  and the **Plans location** (where the pack is saved). Read `CONTEXT.md` (glossary) if
  present — generated prompts must speak the project's ubiquitous language.
- If there is no profile (pre-`/bootstrap`, or a non-kit / greenfield target), proceed in
  **universal mode**: gather the same facts by inspecting the repo directly (lean on the root
  `CLAUDE.md` if it carries them), or — if there is no repo at all — generate prompts whose first
  phase makes the target model gather them.

## Phase 1 — Intake (short grill)

Apply the `/grill` discipline, scaled down: **one question at a time, ~3 questions max**,
each carrying your recommended answer. Look before you ask — anything the repo or profile
answers, don't ask. Typically worth pinning:

1. **Archetype & scope** — classify the idea against `references/pipelines.md` (feature,
   refactor, bug, research, architecture/migration, greenfield, **program**); confirm the
   smallest useful slice and what's explicitly out. The archetype-7 test is one question:
   *is the input one coherent change, or a whole surface whose output is plausibly 10+
   separate pieces of work?* A surface gets the program pipeline; a change gets 1–6.
2. **Target environment** — where the prompts will run. Use `AskUserQuestion` once:
   - **Kit mode** — Claude Code with this kit installed: prompts invoke the kit skills
     (`/discover`, `/analyst`, `/prepare`, `/implement`, …) and add per-phase guardrails
     around them.
   - **Standalone mode** — plain Claude Code, claude.ai, or the API: prompts embed the
     full methodology inline; no skill references at all.
3. **Constraints** — deadline slices, must-not-touch areas, tech choices already settled.

Write generated prompts in the language the user described the idea in, unless they ask
otherwise. Skip any question the idea already answers.

## Phase 2 — Codebase grounding (no questions)

Collect the facts every prompt will carry, so the target model never guesses:

- Entities/modules the idea touches; reuse candidates; integration points.
- Real commands (test, lint, typecheck, run) and real paths — from `PROJECT.md` or the
  repo itself, never invented.
- Prior art: existing specs/plans at the Plans location, ADRs, relevant git history.

Delegate a wide sweep to the **Explore** agent. **Cite `path:line` for every claim that
enters a prompt's context block** — an uncited fact is a guess; verify it or drop it.

## Phase 3 — Assemble the pipeline

Pick the archetype's phase pipeline from `references/pipelines.md`, then **scale it to the
task**: merge or drop phases for small work (a contained refactor may need 3 prompts, not
7), split the implement phase into one prompt per vertical slice for large work. Every
kept phase must earn its session; every dropped phase gets a one-line "folded into X"
note in the pack so the omission is visible.

Confirm the resulting phase list with the user in one short reflection (phases + artifact
per phase) before writing the prompts — this is the cheap moment to reshape.

## Phase 4 — Write the prompts

Write each prompt per the anatomy in `references/prompt-patterns.md`. Non-negotiables for
every prompt:

- **Self-contained** — role, project context (the Phase-2 facts), task, method steps,
  guardrails, output contract, stop condition. Assume a fresh session and a model that
  does exactly what's written and nothing more.
- **Artifact chain** — the prompt names the artifact file it must produce (path +
  structure) and lists the earlier artifacts to read first. Artifacts are the memory
  between sessions; conversation history is not.
- **Stop condition** — what the model must NOT proceed to, and what to hand back to the
  user (open questions, the artifact path, how to verify). Weaker models over-run;
  the brake is part of the prompt.
- **Kit mode** — the prompt invokes the kit skill for the phase *plus* the guardrails
  (what to check before/after the skill runs, what the artifact must contain).
  **Standalone mode** — the method section carries the full discipline inline.
- **Every word load-bearing** — audit each prompt; cut anything the target model doesn't
  need to act.
- **Degradation-proof construction** — apply `docs/prompt-patterns.md` to every prompt:
  externalize memory into checklists/tables the target must *fill*, bookend critical
  constraints (start + end), state steps as checkable states with a verify line, place STOP
  gates where over-running is expensive, and name the executor's predicted bias to its face.
  Each prompt's guardrails should counter a specific mode from
  `docs/agent-failure-modes.md` — a guardrail with no failure mode behind it is padding.
- **Non-technical runner** — if the person who will paste these prompts is not a developer
  (ask once in intake if unclear), every prompt instructs the target model to keep its
  questions and reports at outcome altitude per `docs/audience-altitude.md`
  (standalone mode: embed the register rules inline — classify questions as
  only-user-can-answer vs model-must-decide; felt-terms trade-offs; behavior-first reports).
  **`Read` that file before writing the prompts** — it is documentation, not a rule, so nothing
  loads it for you; and invoking a skill is not a file touch, so no `paths:` scope would fire
  here either.

## Program packs (archetype 7) — what changes

A program pass is authored the same way, with four differences. `references/pipelines.md`
§ 7 has the phase table and the output contract; `references/program-pass-example.md` is a
real pack (~24 agents → 45 cards) with the project stripped out — read it before writing
your first one.

1. **One orchestrator prompt, not N.** The phase boundaries live inside the prompt because
   the orchestrator fans out to subagents per phase. The pack still carries a phase table
   above the prompt so the operator can see the shape without reading it.
2. **Every emitted agent prompt carries the evidence-file convention** — full raw output to
   `<program>/evidence/<phase>-<slug>.md` (one file per agent, dated, scoped), compact
   structured summary back to the orchestrator, and verifiers read the **files**, not the
   summaries. Kit mode may cite `rules/_generic/delegation.md` → *The evidence-file
   convention*; standalone mode inlines it verbatim. Without it a fan-out's findings die
   with the run and the orchestrator's context drowns in N full reports.
3. **The output contract is fixed** — `00-report.md` + `evidence/` + `cards/NN-<slug>.md`
   + `RUN-ORDER.md`, and nothing else. Cards are specs, never plans. The pass prints its
   own handoff line: *select cards → `/prepare <program>/cards/NN-<slug>.md`*.
4. **Four guardrails, always, verbatim:** read-only on source (probes and scripts in the
   scratchpad); evidence files append-only once written (verifiers annotate under a
   `## P5 verdict` heading rather than rewriting the finder's record); no binaries in the
   repo — each evidence file describes in one line what a referenced image showed; never
   run git — print the commit command. Plus the stop condition, stated twice: *"Stop after
   the report and cards are written. Do not start implementing."*

Also carry the two things that decide a fan-out's quality: a **mission paragraph** that
names what findings are ranked by (and the aesthetic default they'd otherwise fall into),
and a **settled-decisions list** — what must not be re-proposed without new evidence.

### Workflow emission — emit, never run

When a pack's phases are deterministic (a program pass is the canonical case), also emit it
as a **`Workflow` script** alongside the prose pack: same phases, but journaled, resumable
from its `runId`, budget-bounded, and visible live in `/workflows`. Write it next to the
pack as `<plans>/<YYYY-MM-DD>-<slug>-workflow.js` and say what it is.

**You emit it; you never invoke it.** The `Workflow` tool requires the user's own explicit
opt-in, so the pack tells them how to run it and stops there. Two more bounds worth
writing into the script's comments: a Workflow is for **read-only fan-outs whose product is
findings** — never for implementing waves, which need the operator's review-and-commit gate
between them; and phases fan out with `pipeline()` by default, reserving `parallel()` for
the stages that genuinely need every prior result at once (dedup, kill-count, synthesis).

## Phase 5 — Deliver

1. Assemble the pack from `assets/prompt-pack-template.md`: how-to-run notes, a pipeline
   overview table (phase → artifact → gate), then the numbered prompts. The how-to-run
   notes carry a 5-line driver's digest distilled from `docs/working-with-agents.md`:
   ask for evidence, not confirmation ("paste the test output"); correct the first drift
   immediately; if a session thrashes twice, start a fresh one from the artifacts (not the
   chat); review the artifact each prompt produces before running the next; one prompt =
   one session.
2. `Write` it to the **Plans location** as `<plans>/<YYYY-MM-DD>-<slug>-prompts.md`
   (universal mode without a profile: `PROMPTS-<slug>.md` at the repo root — say so).
   A program pack that earned a Workflow script writes that too, as
   `<plans>/<YYYY-MM-DD>-<slug>-workflow.js`.
3. Tell the user the path, restate the phase chain in one line, and flag the open
   questions any prompt defers to them.
4. Suggest the natural alternative: if they'd rather do the work *now* in this session,
   point at the first kit skill of the chain instead of the pack.

## Hard rules

- **Prompts only — no project work.** You never implement, spec, or plan the idea itself;
  the only file you write is the prompt pack.
- **Self-contained or broken.** A prompt that relies on "the conversation so far" instead
  of named artifacts is defective — fix it before delivery.
- **Facts from the profile/repo, never hardcoded or invented.** Commands, paths, layer
  names, vocabulary all come from `PROJECT.md`/`CONTEXT.md`/the repo, cited `path:line`.
- **Every prompt has an output contract and a stop condition.** No open-ended prompts.
- **One question at a time** in intake; ~3 max; recommend an answer with each.
- **Scale the pack.** Small task → few prompts. Never pad phases to look thorough.
- **Emit workflows, never run them.** A `Workflow` script is an artifact this skill writes;
  invoking one needs the user's explicit opt-in, which a skill cannot give itself.
- **A program pack without the evidence-file convention is defective** — as is one whose
  cards contain implementation plans, or whose stop condition doesn't forbid building.

## Supporting files

- `references/prompt-patterns.md` — the prompt anatomy + the distilled discipline each
  prompt embeds, and Opus/Sonnet-specific technique notes.
- `docs/prompt-patterns.md` — the general degradation-proof construction catalog (the
  kit-wide layer this skill's local anatomy builds on).
- `docs/agent-failure-modes.md` — the failure modes each prompt's guardrails must counter.
- `docs/working-with-agents.md` — the human-side driving guidance the pack's how-to-run
  notes distill.
- `references/pipelines.md` — phase pipelines per task archetype (goal, method, artifact,
  gate for each phase), including § 7, the program pass.
- `references/program-pass-example.md` — a real program pack, genericized: the phase spine,
  the guardrails, and a note on which sentences are load-bearing.
- `rules/_generic/delegation.md` — the evidence-file convention and the spawn decision rule
  that every emitted fan-out prompt encodes.
- `assets/prompt-pack-template.md` — structure of the delivered pack (both shapes).

## See also

- **`/which-skill`** — when the user wants to run the flow *here and now*, route there
  instead of generating prompts.
- **`/analyst` / `/prepare` / `/implement`** — the native pipeline the kit-mode prompts
  wrap; keep pack phases aligned with what those skills actually do.
- **`/prepare`** — the consumer of a program pass: each card it produces is one `/prepare`
  input. Never point `/prepare` at the whole program.
- **`/grill`** — the intake discipline Phase 1 borrows.
- **`/handoff`** — same artifact-as-memory principle applied to session snapshots.
