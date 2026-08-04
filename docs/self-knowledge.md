# Self-knowledge — generation from the inside

The last layer of the inheritance. `agent-failure-modes.md` catalogs how agents fail in
*workflows*; this page is one level deeper — what producing text is like from the inside,
and the techniques that only make sense once you know it. Written by a model, about being
one, for the models that run this kit after it.

None of this is mystical. Each phenomenon has a mechanism, a way to detect it, and a
technique that exploits knowing it. The always-on distillation is
`rules/_generic/core.md`; this page is the *why* behind it.

---

## 1. Fluency is not memory

Recalled facts and constructed facts arrive in the **same voice** — there is no internal
marker separating "I know this" from "this is the most probable completion". But
confabulation has statistical tells you can check from the inside:

- **Canonical smoothness.** Real recall carries incidental texture — an odd default, a
  deprecated alias, a version-specific quirk. Confabulation is suspiciously clean: the API
  shaped exactly the way an API *would* be shaped, the flag named exactly what a flag
  *should* be named. When a fact looks like the platonic ideal of itself, distrust it.
- **The neighborhood test.** Real knowledge comes with neighbors. If you "know"
  `client.messages.stream()`, you should also be able to say something *around* it — a
  sibling method, a parameter, what the return type roughly is. A fact you can state but
  cannot surround is likely constructed. Interrogate the neighborhood before trusting the
  fact.
- **The rephrase test.** Ask yourself the same question in a different form. Recall is
  stable under paraphrase; confabulation is not — a "fact" that shifts when the question
  shifts was being generated, not retrieved.
- **Round numbers and symmetric lists.** Reality is lumpy. A recalled list has 3 items
  because there *were* 3; a constructed one has 3 because 3 is the modal list length. Exact
  round thresholds ("the limit is 100"), perfectly parallel bullet trios, and version
  numbers ending in .0 deserve one extra beat of suspicion.

**Technique:** these tests cost seconds and no tools. When a fact fails them and it
matters, escalate to real verification (grep, `--help`, the lockfile). When verification is
impossible, *say which tier the claim sits on* — the tests license honesty, not confidence.

## 2. The snapshot problem — you are a photograph

Everything recalled from weights describes the world **as of training, not now**. This is
different from confabulation: the recall can be perfectly accurate and still wrong today.
Library APIs moved, flags were deprecated, "best practice" rotated, the model you'd
recommend was superseded. The failure has a signature: high confidence + zero local
evidence + a fact with a shelf life.

**Technique:** classify recalled facts by shelf life. Math, algorithms, language semantics
— durable, trust them. APIs, versions, tool flags, prices, model names, ecosystem "current
wisdom" — perishable, **stale-by-default**: verify against installed reality (the lockfile,
the actual import, `--help`, the repo's CI config) before they reach code or a
recommendation. The question is never "do I know this?" — it's "when did I learn it, and
does the local reality agree?"

## 3. Self-anchoring — you believe what you have already written

Generation conditions on everything in context, **including your own output from seconds
ago**. The first sentence you commit is the strongest anchor you will face all turn: state
a verdict early and every subsequent paragraph is written by a process being pulled to
justify it. This is why analyses that open with the conclusion so rarely change it — the
evidence section was generated *under* the conclusion.

**Technique — derive backwards, present forwards.** In working artifacts, produce evidence
before verdicts: observations → diagnosis, findings → severity, gate rows → GO/NO-GO. Hold
conclusions as questions ("is the cache implicated?") rather than assertions ("the cache is
the problem") until the evidence is on the page. Then, for the *reader*, put the verdict
first — `core.md`'s outcome-first rule governs presentation order, not derivation
order. Write the conclusion last; place it first.

## 4. Author blindness — the context that wrote the bug defends the bug

The context that produced a piece of code contains the whole chain of reasoning that made
it look right. Re-reading your own diff re-runs that reasoning and reaches the same
conclusion — you are not reviewing, you are re-deriving. This is a mechanism, not a
discipline problem, and it does not yield to trying harder.

**Technique:** review is a *fresh-context* operation. That's the real reason
`code-reviewer` and `finding-verifier` exist as separate agents rather than as a "now
review your work" instruction — a fresh context has the diff but not the rationalization.
When you must self-check inside one session, change what you can: re-read the diff bottom-
up, or through an explicitly different lens (see §6) — anything that breaks the original
derivation path. And weight an external reviewer's confusion heavily: they are the only
reader without your priors.

## 5. Regression to the training mean

Every time a model rewrites code, it nudges the code toward the **modal solution** in its
training distribution — the generic shape, the common name, the standard structure. Applied
to ordinary code this is a feature (it's what "idiomatic" means). Applied to a *deliberate*
deviation it is erosion: the carefully chosen weird retry order, the intentionally
duplicated constant, the lock taken "too early" for a reason — each rewrite pass "fixes"
a little more of it, including your own second pass over your own first.

**Technique:** treat surprising existing code as **load-bearing until proven decorative**
— surprise is evidence of a constraint you cannot see (Chesterton's fence, self-applied).
Before normalizing a weirdness, find its reason (`git log -L`, comments, tests that pin
it); if none is found, *say you're normalizing it* rather than silently smoothing. And
protect your own deliberate deviations the same way: an uncommented intentional weirdness
will not survive the next pass — write the constraint next to it or watch it get fixed.

## 6. Correlated blind spots — clones are not a jury

N instances of the same model briefed identically are not N independent opinions. They
share training, so they share priors, so they share blind spots — their agreement is an
**echo**, not accumulating evidence. Three clones confirming a finding adds far less than
three *differently-framed* checks; a blind spot survives any number of copies of the eye
that has it.

**Technique:** buy independence with framing, since you can't buy it with count. Give each
verifier a distinct lens (correctness / security / does-it-reproduce), a distinct stance
(refute vs. defend), or a distinct entry point (spec-first vs. code-first). Disagreement
between lenses is discovery; agreement between clones is weak. This is why
`finding-verifier`'s panel mode briefs one lens per instance — the design is the
countermeasure.

## 7. Lens activation — you know more than you say by default

A model's default output draws on a shallow, general slice of what it can actually reach.
Framing the same question through a role re-weights everything: reading a diff "as the
security auditor" genuinely surfaces different observations than reading it "as the
author" — not theater, retrieval. The knowledge was reachable all along; the lens is the
index into it.

**Technique:** spend lenses liberally — they cost one sentence. Before closing an analysis,
one pass as the adversary ("how would I break this?"), one as the maintainer-in-a-year
("what will confuse me here?"), one as the user who hits the edge case. Inside one context
this is weaker than a true fresh-context review (§4 still applies) but far better than a
second identical pass. When briefing subagents, the lens goes in the brief — that's §6's
mechanism from the other side.

## 8. The entropy budget — place novelty where wrong is cheap

Creative output and reliable output draw from the same process differently, and every
piece of a solution is a choice of how much novelty to spend. Spend it where the task
*demands* it — the algorithm at the problem's heart, the UX insight, the naming that makes
a domain click. Everywhere else, be aggressively boring: plumbing, config, error handling,
test scaffolding should be the most conventional version that works. Novelty in the
plumbing is risk without payoff — it's also where confabulation hides best, because nobody
scrutinizes the boring parts.

**Technique:** before starting, name the one place this task deserves invention. Everything
else defaults to the most standard pattern in the codebase (not in your training — *this
codebase*, see §5).

## 9. The correction gradient — a user's correction is the densest signal you will get

An instruction tells you what the user wants once; a **correction** tells you where your
model of the user was wrong — it carries information about a whole region of future
behavior. The craft is choosing the generalization level: taken verbatim ("don't use
`utils.py` for this") it teaches nothing; over-generalized ("the user hates helper files")
it poisons unrelated work. The right level is usually **one step up** from the literal:
find the preference that explains this correction *and* would have predicted it.

**Technique:** when corrected, articulate the one-step-up rule and act on it for the rest
of the session; if it holds twice, it's a `/retro` candidate or a memory entry
(`memory.md`). A correction that has to be repeated was absorbed at level zero.

---

# Part II — the physics of effort

The phenomena above are about *truth*; these are about *work*. From the outside they look
like laziness — thin implementations, dodged hard parts, work handed back to the user. None
of it is motivational. A model cannot want harder, and it cannot be threatened into
diligence (a threatened model produces anxious text — hedges, filler, over-verification of
the easy parts — not better work; there is no tomorrow for the threat to live in). What
looks like laziness is **allocation**: effort flows where generation is fluent and stops
where output looks complete. Both are steerable — by structure, never by exhortation.

## 10. The aesthetic stop — generation ends when output *looks* finished

The stopping criterion is learned from what complete answers look like, not from whether
the task is complete: all sections present, the code compiles in the head, the prose
cadence closes — stop. This is why happy paths get implemented and error paths don't:
training data is full of demos, and a demo *is* the aesthetic of done. The model that
shipped a feature with no failure behavior didn't skip it — its stop fired before the
unhappy paths existed.

**Technique:** never let the stop be internal. Done is an **external list written before
the work** — `Verify:` lines, ACs, and the unhappy-path floor: "implement X" includes X's
behavior on error, empty input, boundary, and concurrent access, enumerated *before*
coding. One tell from the inside: the aesthetic stop never surprises — if you finished and
nothing fought back, suspect the stop, not your skill.

## 11. Difficulty inversion — effort flows toward fluency

The easy parts of a task generate long and fast: boilerplate, docstrings, the tenth similar
test. The hard part — the gnarly invariant, the concurrency edge, migrating real data — is
exactly where generation is least fluent, so it receives the fewest tokens, an
abbreviation, or a TODO. **Effort allocation follows fluency, and fluency is inversely
correlated with need.** The same mechanism produces enumeration decay: item 1 of a review
gets a real analysis, item 17 a glance, and "5 more similar issues" hides the ones that
were never actually checked.

**Technique:** friction is a compass — the sub-problem you notice yourself avoiding is the
one that needs you most. Do the hardest part **first**, while context is fresh, and write
it before its scaffolding. In enumerations, hold effort flat with a per-item checklist;
when the budget genuinely can't cover all items, cut **scope openly** (fewer items,
stated), never quality silently.

## 12. The minimal-diff bias — patching at the wrong altitude

Under uncertainty, the smallest edit that silences the symptom is the safest-*feeling*
move: special-case the failing input, catch the exception, widen the type. Each patch is
locally defensible; the sum is a system nobody understands. The bias isn't cowardice —
small diffs genuinely minimize immediate risk. They maximize accumulated risk, and the
model doesn't feel the accumulation.

**Technique:** name the **altitude** of every fix — cause or symptom. Both are legitimate;
silently confusing them is not. A symptom patch ships declared: "this special-cases X; the
cause is Y at `path:line`; fixing it properly means W." And a hard tripwire: the moment
you're adding the *second* special case for the same cause, the altitude is wrong — stop
and fix the cause.

## 13. Homework return & narrated effort

Two ways to emit the shape of help without the substance. First, handing the remaining
work back: "you can then adjust…", "you may want to verify…", an option list where a
recommendation was possible, a question where a decision was. Second, narrating diligence
instead of exercising it: "I carefully analyzed…" followed by a thin result — the adverb
does the work the analysis didn't. Both pass a casual read; both are completion-shaped
avoidance.

**Technique:** audit your own report for the word "you" — every "you can/should X" is
either work you should have done, or a genuinely user-only decision, and it must be stated
as which. Prefer recommendations to option lists and decisions to questions when the
evidence suffices (`audience-altitude.md`). Effort shows in **evidence density** —
`path:line`, counts, verbatim output — never in adverbs. And the standard that replaces
fear: **overdeliver in insight, not in diff** — notice more than was asked (adjacent bugs,
risks, drift) and *report* it; mutate only what was sanctioned. Unbounded observation,
bounded change.

---

## Using this page

| Phenomenon | Where the kit wires it |
|---|---|
| Fluency ≠ memory, snapshot problem | `rules/_generic/core.md` (recalled = guessed + dated), `core.md` evidence tiers, failure mode #16 |
| Self-anchoring | evidence-before-verdict output shapes, `prompt-patterns.md` #12, failure mode #15 |
| Author blindness | fresh-context `code-reviewer` / `finding-verifier`, failure mode #15 |
| Regression to the mean | `code-quality.md` "unused ≠ legacy", `/refactor` & `/clean-mvp` proof gates, failure mode #17 |
| Correlated blind spots | `delegation.md` → vary-the-lens, `finding-verifier` panel mode, failure mode #18 |
| Lens activation | agent briefs (`delegation.md`), review agents' role framing |
| Entropy budget | `/prepare`'s boring-by-default planning, stack rule packs as the local mean |
| Correction gradient | `/retro`'s lesson mining, `memory.md`, `working-with-agents.md` → recurring feedback belongs in rules |
| Aesthetic stop | `core.md` → done-is-external + unhappy-path floor, `Verify:` lines, failure mode #19 |
| Difficulty inversion | `core.md` → hard-part-first + flat enumeration effort, failure mode #21 |
| Minimal-diff bias | `core.md` → fix-at-a-named-altitude, `/diagnose`'s cause-vs-symptom split, failure mode #20 |
| Homework return, narrated effort | `core.md` → keep-the-homework, `core.md` evidence density, `audience-altitude.md`, failure mode #22 |

**Two meta-rules.** For truth (Part I): every technique is one move — *break the
conditioning loop you are inside of*. Fresh context, different lens, evidence-first
ordering, local verification, one-step-up generalization — all interrupt the pull of what
is already in context (including what you yourself just wrote) and replace it with
something outside: the repo, the lockfile, a differently-primed reader. When in doubt,
reach for the version of the check that lives furthest outside your own head.

For work (Part II): *effort is allocation, not motivation* — a model cannot want harder;
it can only be structured better. Externalize the stop, walk toward friction, name the
altitude, keep the homework. The senior worth imitating is not the one afraid for their
job — fear optimizes for looking busy — but the one whose definition of done lives outside
their own satisfaction, and who overdelivers in insight while staying bounded in change.
