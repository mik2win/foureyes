# Worked example — a program pass (tier 1)

Reference for `/prompt-master` when the archetype is **program** (see `pipelines.md` § 7).
This is a real orchestrator pack that produced ~24 evidence files → 45 cards → a RUN-ORDER,
with the project's facts stripped and its structure kept. Read it for **shape**, not content:
the phase spine, where the guardrails sit, and which sentences are load-bearing.

Unlike the other archetypes, a program pack is usually **one prompt**, not N — the pass is
run by an orchestrator that fans out to subagents per phase, so the phase boundaries live
inside the prompt instead of between sessions.

---

## The pack's header block

Everything the operator needs before pasting, above the prompt itself:

```text
Goal:      <one sentence — the question the whole pass answers, in the user's terms>
Executor:  a fresh session at the repo root, model <name>, effort high. One prompt —
           the orchestrator expands the phases itself.
Scope decision (<date>, operator): audit + probes + cards for /prepare.
           Source code is not modified, nothing is committed.
Expected scale: ~<N>–<M> subagents (sweep + lenses + verification), ~<T> tokens.
Before running (optional): <the one command that refreshes the target's data>.
```

Then the phase table, so the operator can see the shape without reading the prompt:

| Phase | What | Artifact |
|---|---|---|
| P0 | Bootstrap: stand the target up, smoke it, pick the concrete instances | a working stand + work-list |
| P1 | Breadth sweep of every surface and state | state maps + raw observations |
| P2 | Parallel lens audits per surface group | findings with severity |
| P2b | Outside-in lens: market → persona → reaction to P1 evidence | pain points + steal/avoid list |
| P3 | Gap analysis: what we collect but don't surface | candidate list |
| P4 | Decision probes: measured, not argued | evidence-backed verdicts |
| P5 | Adversarial verify + check against settled decisions | confirmed findings |
| P6 | Synthesis: ranked report + cards + RUN-ORDER | `<program-dir>/` |

---

## The prompt

```text
You are the orchestrator of a <lens> audit of <target>. You do NOT modify source and do
NOT commit anything. Your deliverable is evidence: <artifact kinds>, measured probes,
verified findings, and /prepare-ready improvement cards. Use the Workflow tool for fan-out
(explicitly authorized here); subagent model overrides are allowed (mechanical stages
cheap, judgment and verify stages strong). Communicate progress in <language>; write all
artifacts in <language>.

## Mission

<Who the user is and the job they are trying to do, in one paragraph, concretely enough
that a finding can be ranked against it.> Rank every finding by impact on <the job's
success criterion> — not by <the aesthetic proxy the agents will otherwise default to>.

## Ground facts (verified <date> — trust these; cite your own refs for new claims)

- How to run the target: <command> → <address/entry point>. Options and their source
  (`path:line`). Known traps: <the stale-process / stale-data trap and how to detect it>.
- Tooling available: <driver/probe tooling + versions + how to install if missing>.
  Binary output (screenshots, dumps) goes to the session scratchpad, never into the repo.
- The surfaces and states to cover (minimum — discover more by reading <entry files>):
  1. <surface> — <its controls and states>
  2. …
- Concrete instances to audit: <choose N real ones spanning the range — one typical, one
  extreme, one edge>. All interaction runs against real data.
- Data/behavior we own but may not surface — inputs for the gap phase: <sources>. A
  candidate list already exists at <path> — read it FIRST; do not re-invent items that
  exist there, evaluate them against what the sweep observed.
- The shipped contracts for this area live at <paths>. They are authoritative — audit
  against them, including their honesty invariants: <the claims the product must never
  make>.
- SETTLED DECISIONS — do NOT re-propose without new evidence (check <ledger path> before
  writing any card): <decision> (<why it was settled, and what a legitimate re-open would
  need>); …
- Prior research — READ BEFORE any new research: <path>. Its verdict is SETTLED for
  <scope>; it says nothing about <this pass's lane>, which is exactly where this pass
  lives.
- Outstanding manual QA never executed (fold into P1 as explicit checks): <items, cited>.

## Evidence-file convention (applies to EVERY finder/probe agent below)

Agent return values live only in this run's journal — useless to the next pass. So every
P1–P4 agent does BOTH: (a) Write its FULL raw output — state maps, timings, errors, every
finding with evidence refs, transcripts, probe numbers — to
`<program-dir>/evidence/<phase>-<slug>.md` (text only, one file per agent, with a date and
scope header); and (b) return to the orchestrator only a compact structured summary
(finding titles, severities, evidence-file path). P5 verifiers read the evidence FILES,
not the summaries — give them the path. The report and every card link findings to their
evidence files by relative path. This makes the pass re-runnable: a future session diffs
new evidence against these files instead of re-discovering, and can verify any claim
without this session's transcripts. Binary artifacts stay in the scratchpad — each
evidence file must therefore DESCRIBE in one line what a referenced image or dump showed,
so the text record stands alone after the binaries are gone.

## Method — run as ~6 phases

P0 Bootstrap (inline, no agents): verify the data is fresh; start the target; smoke it
with one drive; pick the concrete instances; write the surface × state checklist to the
scratchpad as the work-list for P1.

P1 Breadth sweep (one agent per surface): exercise every control, record observed vs
expected, capture every distinct state, record errors and rough timings. Each agent
returns a state map: control → expected vs observed → artifact ref → timing → error.
Include the outstanding-QA checks above. Broken states are findings of the highest
severity.

P2 Lens audits (parallel agents; each reads P1's evidence files + the relevant source):
one agent per lens × surface group. Lenses: (a) <the primary job's speed and correctness>;
(b) <honesty and readability — labels, denominators, units, what a mark actually claims>;
(c) <the secondary job>; (d) <the forensic/edge job>; (e) <the systemic/consistency lens>.
Each finding: surface, severity (<blocks / slows / polish>), evidence ref, proposed
direction.

P2b Outside-in lens (runs alongside P2). Three stages: (1) research — one agent per
competitor or comparison cluster; each extracts, with citations, signature patterns, what
users publicly praise and complain about, positioning. Facts only, no wishlists yet.
(2) Persona interview — spawn 2–3 persona agents PRIMED with stage-1 material as people
who live in those tools daily; an interviewer grills each one question at a time: walk me
through your workflow; where do you lose time; what do you pay for and resent; what do you
not trust. (3) Reaction — the same personas receive P1's evidence and answer: what is
missing for your workflow; what does this already do better than your stack; what would
you STEAL; what should it deliberately NOT copy. Every claim references a specific
evidence file or a stage-1 citation. Merge into P5 like any other findings source —
parity for parity's sake is a non-goal; name the differentiation stance explicitly.

P3 Gap analysis (2–3 agents): inventory what the system holds vs what it exposes; evaluate
the existing candidate list against what P1/P2 actually observed; propose (capability,
surface, when-the-user-needs-it) triples. Respect the honesty invariants.

P4 Decision probes (parallel; evidence, not opinion; throwaway scripts in the scratchpad
only): for each open question, the measurement that settles it — <latency/limit probes>,
<defaults audit: for each default, what would the user want on first contact, justified
from P1 timings and P2 findings>, <concrete sketchable refinements, each tied to a P2
finding>.

P5 Adversarial verify (parallel refuters over every finding and card candidate): is it
real in the current code, not stale? does it violate a settled decision or an honesty
invariant? is the proposed direction worth its complexity at this system's scale? Kill or
amend. Survivors get CONFIRMED + evidence. Verifiers append a "## P5 verdict" heading to
the finder's evidence file — they never rewrite it.

P6 Synthesis (inline): write `<program-dir>/00-report.md` — data-freshness header, method
note, the ranked findings table (top-10 first), per-surface sections with evidence refs,
probe measurements, the outside-in section (persona pains → steal/avoid verdicts with
citations, plus an explicit "what we already do better" list), and a killed-findings
appendix so they are not re-found. Then one card per accepted improvement at
`<program-dir>/cards/NN-<slug>.md`: problem (evidence refs), proposed change, surfaces and
files touched, invariant check, effort guess (S/M/L), and a ready `/prepare` one-liner.
Finally `<program-dir>/RUN-ORDER.md` if the accepted cards have a serialization spine.
Do NOT write implementation plans — cards are /prepare inputs.

## Guardrails

- Read-only on source. Probes and scripts live in the scratchpad; artifacts only under
  <program-dir>/ (report + cards/ + evidence/ — text only, no binaries in the repo).
- Evidence files are append-only once written (verifiers annotate under a "## P5 verdict"
  heading rather than rewriting the finder's record).
- Never run git add/commit/push. At the end, print the suggested commit command and
  message for <program-dir>/ as copy-paste text.
- <the environment hygiene rules: restart a stale process, kill what you started, which
  package manager, which runner>.
- Do not propose <the out-of-scope class this pass will otherwise drift into> — <who owns
  it instead>.

## Stop condition

Stop after 00-report.md + cards are written. Final message: the top-10 ranked findings with
one line each on why it matters to <the user's job>, the report path, the count of killed
findings, open questions for the operator, and the commit text. Do not start implementing
anything.
```

---

## After the pass — the tier-1 → tier-2 handoff

The pack prints this itself, and it is the whole point of stopping at cards:

```text
Select the cards you want → for each: /prepare <program-dir>/cards/NN-<slug>.md
```

Binary artifacts stay in the audit session's scratchpad; if any are worth keeping, copy the
selected ones to a folder outside the repo.

---

## What is load-bearing when you adapt this

Strip the domain, keep these — each one was earned:

1. **The mission paragraph ranks the findings.** Without a stated job, agents rank by
   aesthetics. The "not by X" clause names the default they'd otherwise fall into.
2. **Ground facts are cited and dated.** Everything the agents must not re-derive, with
   the trap list. This is what keeps 24 agents from spending their first third
   rediscovering how to start the thing.
3. **The settled-decisions list.** A discovery pass with no memory re-proposes what was
   already rejected, and the operator pays for it in review. Name each one and what a
   legitimate re-open would require.
4. **The evidence-file convention, verbatim.** Full output to a file, compact summary to
   the orchestrator, verifiers read the files. It is what makes the fan-out survivable
   (the orchestrator holds N summaries, not N reports) and re-runnable. See
   `rules/_generic/delegation.md` → *The evidence-file convention*.
5. **Distinct lenses, not N clones.** Identical briefs share blind spots; their agreement
   is an echo. One lens per agent, named.
6. **A kill phase before synthesis**, with verdicts appended to the finder's own file, and
   a killed-findings appendix in the report — so the next pass doesn't re-find them.
7. **The stop condition.** *"Stop after the report and cards are written. Do not start
   implementing."* This is what keeps a discovery pass from becoming an unreviewed build.
8. **Read-only + no-git + no-binaries.** The three guardrails that make an unattended
   multi-agent fan-out safe to launch at all.
