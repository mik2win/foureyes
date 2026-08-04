# Phase pipelines per task archetype

Reference for `/prompt-master` Phase 3 — skip it when the archetype is already fixed and the run
is only rewriting an existing pack's prompts. Pick the archetype, then scale: merge phases for
small work, split Implement into one prompt per vertical slice for large work. Each phase
row gives the goal, the method emphasis (feeds the prompt's Method section), the artifact
(feeds the Output contract), and the gate (feeds the Stop condition — what the user checks
before firing the next prompt).

Kit mode: the right column names the kit skill the prompt wraps; the prompt still carries
its own guardrails + artifact contract around the skill call. Standalone mode: ignore the
column and inline the method.

---

## 1. Feature (new capability)

| # | Phase | Goal · method emphasis | Artifact | Gate | Kit skill |
|---|-------|------------------------|----------|------|-----------|
| 1 | Research | Prior art & reuse in the repo; external unknowns; scope the fuzzy edges | research brief (findings + reuse candidates, cited) | user agrees the framing is right | `/discover` |
| 2 | Spec | Interview → WHAT/WHY: stories US-n, scope in/out, acceptance AC-n, assumptions, open questions | spec | user resolves open questions that block planning | `/analyst` |
| 3 | Plan | Design alternatives → chosen approach; steps mapped to US-n/AC-n, each independently verifiable | plan | user approves approach + step order | `/prepare` |
| 4 | Implement | Execute the plan step-by-step; record deviations; run verify commands per step | diff + deviation log | tests/lint green; deviations reviewed | `/implement` |
| 5 | Verify & review | Exercise the flow end-to-end; review the diff for correctness vs AC-n | review notes + verification transcript | user accepts or loops a fix-round | `/code-review` + `/test` |

Small feature: merge 1+2 (research inside the spec prompt) and 5 into 4's stop condition —
3 prompts total.

## 2. Refactor (behavior-preserving)

| # | Phase | Goal · method emphasis | Artifact | Gate | Kit skill |
|---|-------|------------------------|----------|------|-----------|
| 1 | Characterize | Pin current behavior: locate/verify the test safety net; add characterization tests where the net is missing | baseline report (coverage of the target area + how to run it) | user accepts the net is sufficient | `/test` |
| 2 | Map & rank | Find the actual smells in the target area (cited); rank by value/risk; explicit non-goals | refactor map | user picks the increments to do | `/arch-health` (large) or `/code-review` (scoped) |
| 3 | Plan increments | Order into small behavior-preserving increments, each green-to-green with the verify command named | increment plan | user approves order | `/prepare` |
| 4 | Execute (× N) | One increment per prompt: change → run tests → stop. No new behavior, no drive-bys | diff per increment | tests green after EACH increment | `/refactor` |
| 5 | Verify | Whole-area pass: behavior unchanged, quality goals met, no leftover TODOs | closing report | user closes or loops | `/code-review` |

## 3. Bug fix

| # | Phase | Goal · method emphasis | Artifact | Gate | Kit skill |
|---|-------|------------------------|----------|------|-----------|
| 1 | Reproduce & isolate | Minimal reproduction; root cause with `path:line` evidence — mechanism, not symptom | diagnosis note (repro steps + root cause + blast radius) | user confirms the root cause reads right | `/diagnose` |
| 2 | Fix + regression test | Failing test that captures the bug first; smallest fix; test goes green | diff + regression test | test red-before/green-after shown | `/tdd` or `/test` |
| 3 | Verify | Drive the affected flow; check the blast radius for siblings of the bug | verification note | user closes | — |

Trivial bug: one prompt (1+2 merged) with the stop condition carrying phase 3.

## 4. Research / analysis only (no code output)

| # | Phase | Goal · method emphasis | Artifact | Gate | Kit skill |
|---|-------|------------------------|----------|------|-----------|
| 1 | Frame | Sharpen the question(s); decide what evidence would settle each | question list with success criteria | user confirms the questions | `/grill` (light) |
| 2 | Investigate | Multi-angle: repo evidence + external sources; every claim cited; contradictions surfaced, not smoothed | findings doc | — | `/discover` |
| 3 | Synthesize | Answer each framed question; recommendation with trade-offs; what remains unknown | decision memo | user decides | — |

## 5. Architecture change / migration

| # | Phase | Goal · method emphasis | Artifact | Gate | Kit skill |
|---|-------|------------------------|----------|------|-----------|
| 1 | Current-state map | The as-is: modules, dependencies, data flows in the affected area — cited, no aspirations | current-state map | user confirms it matches reality | `/discover` |
| 2 | Target design | To-be design + why; alternatives considered; decision recorded as an ADR | design doc + ADR | user approves the target | `/domain-model` (ADR) |
| 3 | Migration plan | Waves that keep the system working at every step: compat shims, backfills, cutover, rollback per wave | wave plan | user approves wave order | `/prepare` |
| 4 | Execute (× wave) | One wave per prompt; system green at wave end; deviations recorded | diff + wave report | wave verified before the next fires | `/implement` |
| 5 | Cutover & cleanup | Flip, verify, then delete the shims/old path with proof-of-deadness | closing report | user signs off | `/clean-mvp` (shim sweep) |

## 6. Greenfield (new project / module from zero)

| # | Phase | Goal · method emphasis | Artifact | Gate | Kit skill |
|---|-------|------------------------|----------|------|-----------|
| 1 | Vision & scope | Problem, users, smallest shippable slice; explicit not-now list | vision brief | user confirms the slice | `/grill` |
| 2 | Domain model | Core concepts, relationships, vocabulary — the glossary starts here | domain doc / `CONTEXT.md` seed | user confirms the language | `/domain-model` |
| 3 | Architecture skeleton | Stack + structure model + dependency direction; decisions as ADRs; project scaffolding | skeleton + ADRs | scaffold runs (real command shown) | — |
| 4 | Walking skeleton | Thinnest end-to-end path through all layers, deployed/runnable | working e2e slice | user drives it | `/implement` |
| 5 | Feature loop | Per feature, re-enter archetype 1 with the now-existing profile | — | — | — |

## 7. Program (whole-surface audit / discovery pass — tier 1)

Not a bigger feature: a different job. Archetypes 1–6 take **one coherent change** through
research → ship. A program pass takes a **whole surface** through breadth-first discovery
and ends with *cards* — one scoped unit of work each, which `/prepare` then turns into
plans. Reach for it when the input is "audit / review / map all of X" and the output is
plausibly 10+ separate pieces of work. Worked example: `program-pass-example.md`.

Shape difference: the pack is usually **one orchestrator prompt** that fans out to
subagents per phase, not N prompts across N sessions. The gate is at the end (the operator
selects cards), not between every phase.

| # | Phase | Goal · method emphasis | Artifact | Gate | Kit skill |
|---|-------|------------------------|----------|------|-----------|
| 0 | Bootstrap | Stand the target up, smoke it, pick the concrete instances to audit, write the surface × state work-list | running stand + work-list | the stand is real and the work-list names every surface | — |
| 1 | Breadth sweep | One agent per surface: exercise every control, observed-vs-expected, errors, rough timings | `evidence/P1-<surface>.md` per agent | every surface has an evidence file; broken states already rank highest | — |
| 2 | Lens passes | One agent per lens × surface group — **distinct lenses, not N clones**; each reads P1's evidence + the source | `evidence/P2-<lens>.md`, findings with severity | lenses are genuinely different; every finding cites evidence | — |
| 2b | Outside-in *(optional)* | Comparison research (cited) → personas primed with it → those personas react to P1's evidence | `evidence/P2b-*.md` — pain list + steal/avoid | every claim cites a source or an evidence file | `/discover` |
| 3 | Gap analysis | What the system holds vs what it exposes; evaluate the pre-existing candidate list against what the sweep observed | `evidence/P3-*.md` — (capability, surface, when-needed) triples | no re-invention of items already triaged elsewhere | — |
| 4 | Decision probes | Measure what would otherwise be argued: latencies, limits, defaults, alternatives; throwaway scripts in the scratchpad | `evidence/P4-*.md` with numbers | numbers carry denominators and the command that produced them | `/spike` |
| 5 | Verify & kill | Parallel refuters per finding: still real? violates a settled decision or an invariant? worth its complexity? | `## P5 verdict` appended **inside** each finder's evidence file | survivors CONFIRMED; kills recorded, not deleted | `finding-verifier` |
| 6 | Synthesis | Ranked report → one card per accepted improvement → the execution spine | `00-report.md` · `cards/NN-<slug>.md` · `RUN-ORDER.md` | operator selects cards → `/prepare` each | — |

**The output contract** — a tier-1 pass ends with exactly this, and nothing else:

```text
<program>/00-report.md        ranked findings, each linked to its evidence file
<program>/evidence/<phase>-<slug>.md   one per agent, append-only once written
<program>/cards/NN-<slug>.md  one scoped unit of work each; the /prepare input
<program>/RUN-ORDER.md        the execution spine, when the cards have one
```

**The stop condition is load-bearing:** *"Stop after the report and cards are written. Do
not start implementing."* It is what keeps a discovery pass from becoming an unreviewed
build. The pass also prints its own handoff line — *select cards → `/prepare
<program>/cards/NN-<slug>.md`*.

**Guardrails that make an unattended fan-out safe** (all four, always): read-only on
source; evidence files append-only once written; no binaries in the repo (describe them in
one line instead); never run git — print the commit command.

---

## Scaling rules

- **Merge** adjacent phases when the earlier one would take <15 min of model work — fold
  its method bullets into the next prompt and note "folded into Prompt N" in the pack.
- **Split** Implement/Execute into one prompt per vertical slice or wave when a single
  session couldn't hold the diff — each split prompt gets the full anatomy, not a stub.
- **Never drop** the verify phase; at minimum it lives inside the last prompt's stop
  condition ("hand back the verification transcript").
- A pack of one prompt is legitimate for a truly small task — but then say so to the user;
  they may not need a pack at all.
- **Archetype 7 scales by agents, not by prompts.** Its phase count and agents-per-phase
  come from the topic: drop P2b when there is no outside world to compare against, drop P3
  when the surface exposes everything it holds, split P1 further when a single agent
  couldn't hold one surface. P0, P5 and P6 are never dropped — bootstrap, kill, and
  synthesis are what separate a program pass from a pile of opinions.
