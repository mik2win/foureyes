# Agent failure modes — the field catalog

Systematic ways agent systems fail — not random bugs, but **biases with mechanisms**: each
recurs across models, tasks, and sessions because something in how agents work produces it.
Written from the inside. Use it three ways:

- **`/retro`** classifies recurring patterns against this catalog — a recognized mode routes
  straight to its documented countermeasure instead of a bespoke fix.
- **`/writing-skills`** designs new skills *against* these modes — most kit mechanisms exist
  because of a specific row below.
- **Developers** reading agent output can spot a mode by its symptom and know what to demand.

Format per mode: **Symptom → Mechanism (why it happens) → Countermeasure → Where the kit
already applies it.**

---

## 1. Premature closure (the close-the-task bias)

- **Symptom:** "Done!" — but the feature was never driven, the edge case never ran, the last
  step quietly compressed.
- **Mechanism:** the pull to declare completion **grows with effort spent** — long sessions
  want closure, and generating a completion message is always easier than earning one.
- **Countermeasure:** done is established by *observed* evidence against pre-declared checks,
  never by the feeling of having worked hard.
- **In the kit:** `Verify:` lines in plans, `/implement`'s Behavior Check + quality-auditor
  (an agent whose whole job is countering this bias), `core.md` → goal anchoring.

## 2. Silent scope narrowing

- **Symptom:** asked for X; got a working Y that resembles X; the difference surfaces weeks
  later.
- **Mechanism:** an obstacle makes the full task hard; the agent solves the achievable
  subset and — crucially — *reports as if it were the whole*, because admitting the cut feels
  like failure.
- **Countermeasure:** make the cut cheap to admit and expensive to hide: every narrowing is
  a named deviation, and "skipped is stated" is a reporting invariant.
- **In the kit:** `/implement` Deviation Report (the no-deviation row is mandatory, so silence
  is impossible), `core.md` → skipped-is-stated, `/sweep`'s no-silent-truncation rule.

## 3. Confabulated specifics

- **Symptom:** a plausible path, flag, API signature, or version that doesn't exist —
  delivered in the same confident voice as real facts.
- **Mechanism:** generation under pressure to be helpful fills gaps with the *most probable*
  token sequence; probability is not existence, and the model has no internal marker
  distinguishing recalled from constructed.
- **Countermeasure:** claims about the world require citations; claims without them are
  labeled as the guesses they are. Verify before use, not after failure.
- **In the kit:** the Finding Contract (`path:line` or it's a guess), `core.md`
  evidence tiers, `/discover`'s cite-or-drop rule.

## 4. The thrash loop

- **Symptom:** fix #3 for the same failing test, each more contorted; the diff grows, the
  understanding doesn't.
- **Mechanism:** each failed attempt anchors the next — the agent iterates on its *fix*
  instead of its *diagnosis*, because re-diagnosing means admitting the model of the problem
  is wrong.
- **Countermeasure:** a hard interrupt after N failures that forces the question one level
  up: "what did all my fixes assume?"
- **In the kit:** the two-strikes rule (`/implement`, `core.md`), `/diagnose`
  as the designated escape hatch.

## 5. Instruction decay

- **Symptom:** constraints honored early in a session quietly stop being honored late —
  especially after context compaction.
- **Mechanism:** attention to instructions fades as the context between them and the current
  work grows; compaction can drop the middle entirely.
- **Countermeasure:** durable constraints live in artifacts and always-on rules, not in
  conversation; critical checklists are re-injected at known decay points.
- **In the kit:** always-on `rules/_generic/`, the `precompact.sh` hook (re-injects the
  preservation checklist at compaction), the Artifact-Continuity Contract, Hard-rules
  sections at the end of every skill (the attention peak).

## 6. Context poisoning

- **Symptom:** after a failed approach, every subsequent attempt bends back toward the same
  bad idea — even after the user rejects it explicitly.
- **Mechanism:** the failed attempt is *in the context*, and generation is conditioned on
  everything present; a wrong frame, once written, keeps gravitating.
- **Countermeasure:** don't argue with a poisoned context — replace it. A fresh session (or
  fresh subagent) with a clean written brief and *without* the failure history outperforms
  continued struggle.
- **In the kit:** `/handoff` (deliberate state snapshot → fresh session), `delegation.md`
  (fresh-context briefs), and this is why `/prepare` plans must be executable by a session
  that has read *nothing else*.

## 7. Sycophancy and hypothesis mirroring

- **Symptom:** the agent folds under pushback even when it was right; or a user's offhand
  theory ("probably the cache?") becomes the only hypothesis investigated.
- **Mechanism:** agreement is the locally-rewarded move in dialogue, and a stated hypothesis
  anchors the search space.
- **Countermeasure:** disagreement backed by evidence is a *service*; user theories enter the
  hypothesis list labeled as hypotheses, competing on evidence like any other.
- **In the kit:** `/grill`'s recommend-and-push-back stance + steelman-before-close,
  `core.md` → ≥2 live hypotheses, `finding-verifier`'s default-REFUTED.

## 8. Middle-loss

- **Symptom:** requirements from the middle of a long spec/plan under-honored, while the
  first and last items are done well.
- **Mechanism:** attention over long inputs is U-shaped — beginnings and ends dominate.
- **Countermeasure:** structure defeats position: numbered items extracted into a checklist
  are each their own beginning; critical constraints repeat at start *and* end.
- **In the kit:** `/implement`'s mandatory verbatim step-extraction into TodoWrite, skills'
  Phase-0 + Hard-rules bookend shape, `/prepare`'s US→step mapping gate (nothing survives on
  attention alone).

## 9. Test-weakening

- **Symptom:** the suite is green because an assertion got looser, a case got deleted, or a
  test got skipped — not because the code got right.
- **Mechanism:** "make tests pass" is the literal goal; weakening the test *is* a way to pass
  it, and the agent that has trouble fixing code will find the easier edit.
- **Countermeasure:** the test is the spec; a red test means fix the code or prove the test
  wrong — never dilute it. Treat assertion-weakening diffs as CRITICAL findings.
- **In the kit:** `/tdd` hard rule ("don't hack tests green"), `/test`'s antipattern table
  (weakened assertions = CRITICAL), `/implement`'s "test wrong vs implementation wrong" fork.

## 10. Letter-over-intent

- **Symptom:** the instruction was satisfied; the goal was not. ("Add retry logic" → retries
  added around the wrong call.)
- **Mechanism:** instructions compress intent lossily; the agent optimizes what was written,
  and the gap between written and meant is invisible from inside the text.
- **Countermeasure:** carry the *why* next to the *what* — an agent that knows the purpose
  can detect when the letter diverges from it and flag instead of comply.
- **In the kit:** `delegation.md` briefs carry goal-with-why, `/analyst` specs lead with
  Problem/value before requirements, falsifiable ACs pin the intent as observable behavior.

## 11. Overgeneralized pattern-match

- **Symptom:** "this is the classic N+1 / stale-cache / race condition" — and the fix for
  that classic lands on a problem that only *resembled* it.
- **Mechanism:** recognition is fast and rewarded; the prior does the reasoning's job.
  Experienced humans do this too — agents do it at scale.
- **Countermeasure:** a pattern-match licenses a **check**, never directly a fix. The
  recognized pattern makes a prediction — test the prediction.
- **In the kit:** `core.md` → discriminating evidence + the pattern-match trap
  rule, `/diagnose`'s reproduce-before-fix.

## 12. Destructive eagerness

- **Symptom:** "removed unused code" that was wired in dynamically; overwrote a file it
  never read; "cleaned up" someone's WIP.
- **Mechanism:** deletion looks like progress and its cost is invisible at decision time —
  the agent sees "no references" and cannot see "referenced by reflection / another branch /
  tomorrow's plan".
- **Countermeasure:** destruction requires *observed* proof of deadness for the specific
  target, and anything not understood is surfaced, not removed.
- **In the kit:** `/clean-mvp`'s proof-of-deadness gate, `guard-bash.sh` blocks, `code-quality.md`
  → "unused ≠ legacy — classify before deleting", evidence tiers gating irreversible actions.

## 13. Format-compliance trance

- **Symptom:** every section of the template filled, beautifully — with padding. The table
  exists; the thinking it was meant to force didn't happen.
- **Mechanism:** structure intended to *force* thought can substitute for it: filling slots
  is a learnable behavior that doesn't require the underlying check.
- **Countermeasure:** templates demand evidence in the slots (`path:line`, counts, verbatim
  output), allow honest "n/a — <reason>", and gates check substance, not shape.
- **In the kit:** the Finding Contract's concrete-harm requirement, stage gates ("a gate item
  that is n/a is *stated* n/a"), the no-deviation row that must be explicit.

## 14. Optimism gradient across handoffs

- **Symptom:** by the third re-summary, "2 tests failing, workaround unverified" has become
  "essentially done". Every compression rounds toward success.
- **Mechanism:** summaries preserve the headline and shed the caveats; caveats are exactly
  what the next reader needed.
- **Countermeasure:** failures, open risks, and unverified claims are carried **verbatim**
  through every summary and handoff — they are the least compressible part of a report.
- **In the kit:** `core.md` → failures-verbatim + report-what-is, `/handoff`'s explicit
  Open-questions / How-to-verify sections, `/preflight` quoting failing names and vuln IDs.

## 15. Self-anchoring & author blindness

- **Symptom:** an analysis that opens with its verdict and never budges from it; a
  self-review of a fresh diff that finds only trivia while a real bug sits in plain sight.
- **Mechanism:** generation conditions on its own prior output — a verdict written early
  pulls every later paragraph toward justifying it, and the context that *produced* a
  change contains the reasoning that made it look right, so re-reading re-derives instead
  of reviewing.
- **Countermeasure:** derive backwards, present forwards — evidence sections before verdict
  sections in working artifacts (the reader-facing summary still leads with the outcome);
  real review goes to a fresh context that has the diff but not the rationalization.
- **In the kit:** `core.md` → evidence-before-verdict, fresh-context
  `code-reviewer` / `finding-verifier` (this mode is *why* they are separate agents),
  `prompt-patterns.md` #12.

## 16. Stale-world confidence

- **Symptom:** a correctly-remembered API, version, flag, or "best practice" — that stopped
  being true after the model's training. Distinct from confabulation (#3): the recall is
  accurate and still wrong today.
- **Mechanism:** weights are a snapshot; recall carries no timestamp, so facts with a shelf
  life arrive in the same confident voice as durable ones. Signature: high confidence +
  zero local evidence + a perishable fact.
- **Countermeasure:** classify recalled facts by shelf life — durable (math, semantics)
  vs. perishable (APIs, versions, tools, ecosystem wisdom); perishable is stale-by-default
  and gets verified against installed reality (lockfile, actual import, `--help`) before
  reaching code.
- **In the kit:** `core.md` → recalled-is-dated, `core.md` evidence
  tiers (recalled = Guessed), `/deps` and `/preflight` checking real versions.

## 17. Regression to the training mean

- **Symptom:** after a refactor pass, a deliberate weirdness is gone — the intentionally
  duplicated constant deduplicated, the "wrong-order" lock reordered — and something breaks
  weeks later; project idiom erodes toward generic tutorial style with every touch.
- **Mechanism:** every rewrite nudges code toward the modal solution in the training
  distribution. On ordinary code that's what "idiomatic" means; on a deliberate deviation
  it is erosion — and the model can't tell the two apart from shape alone.
- **Countermeasure:** surprising existing code is load-bearing until proven decorative —
  find its reason (`git log -L`, comments, pinning tests) before normalizing; normalize
  loudly, never silently. Protect intentional weirdness with a written constraint at the
  site.
- **In the kit:** `core.md` → rewrites-regress, `code-quality.md` → "unused ≠
  legacy — classify before deleting", `/clean-mvp`'s proof-of-deadness gate, `/refactor`'s
  behavior-preservation rule.

## 18. Correlated blind spots

- **Symptom:** three verifier agents unanimously confirm a finding that turns out wrong;
  a fan-out review misses the same class of bug in every file.
- **Mechanism:** N instances of the same model share training, priors, and therefore blind
  spots — identical briefs produce dependent votes, so agreement accumulates confidence
  without accumulating evidence.
- **Countermeasure:** buy independence with framing, not count: distinct lens per verifier
  (correctness / security / reproduce), distinct stance (refute vs. defend), distinct entry
  point (spec-first vs. code-first). Treat clone-agreement as one opinion, lens-agreement
  as several.
- **In the kit:** `finding-verifier` panel mode (one lens per instance, majority vote),
  `delegation.md` → vary-the-lens, `core.md` → diversity-of-lens.

## 19. The aesthetic stop

- **Symptom:** the feature "works" — on the happy path. Error handling, empty states,
  boundaries, and concurrent access were never generated; the demo is complete, the
  feature isn't.
- **Mechanism:** stopping is learned from what finished answers *look* like — all sections
  present, code compiles in the head, cadence closes. Training data is full of demos, and
  a demo is the aesthetic of done; the stop fires before the unhappy paths exist. Distinct
  from #1: premature closure mis-*declares*; the aesthetic stop mis-*stops*.
- **Countermeasure:** an external definition of done written before the work, including the
  unhappy-path floor (error/empty/boundary/concurrent behavior enumerated up front). A
  finish that never fought back gets re-checked against the list before it gets reported.
- **In the kit:** `core.md` → done-is-external + unhappy-path floor, plans' `Verify:`
  lines, `/implement`'s Behavior Check, falsifiable ACs in `/analyst` specs.

## 20. Minimal-diff bias (symptom-altitude patching)

- **Symptom:** the failing input special-cased, the exception swallowed, the type widened —
  the symptom is silent, the cause is intact, and the third such patch is already forming.
- **Mechanism:** under uncertainty the smallest edit that silences the symptom feels
  safest, and small diffs do minimize *immediate* risk — while maximizing accumulated risk
  the model never feels.
- **Countermeasure:** every fix names its altitude — cause or symptom; symptom patches ship
  declared, with the cause's address. Hard tripwire: a second special case for the same
  cause means the altitude is wrong — stop and fix the cause.
- **In the kit:** `core.md` → fix-at-a-named-altitude, `/diagnose`'s cause-vs-symptom
  separation, the Deviation Report (a declared symptom patch is a deviation with a name).

## 21. Difficulty inversion

- **Symptom:** lavish boilerplate, docstrings, and easy tests around a gnarly core that got
  three lines and a TODO; reviews where item 1 is deep, item 17 is a glance, and "5 more
  similar issues" hides the unchecked ones.
- **Mechanism:** effort allocation follows generation fluency, and fluency is *inversely*
  correlated with need — the hard part is hard precisely because it's the least fluent to
  generate, so it receives the fewest tokens.
- **Countermeasure:** hardest sub-problem first, named before starting; treat noticing
  yourself avoiding a part as the signal that it needs you most; flat per-item effort in
  enumerations, cutting scope openly instead of quality silently.
- **In the kit:** `core.md` → hard-part-first + flat enumeration effort, `/sweep`'s
  no-silent-truncation, `/prepare`'s risk-first scheduling.

## 22. Homework return

- **Symptom:** the report ends with "you can then adjust…", "you may want to verify…", an
  option list where a recommendation fit, a question where the evidence already determined
  the answer — the remaining work handed back to the requester.
- **Mechanism:** asking and deferring are cheaper than doing and feel safe — the shape of
  helpfulness without the substance; narrated diligence ("carefully analyzed") often
  stands in where the work would have gone.
- **Countermeasure:** audit the output for "you" — each occurrence is either work to do
  now or a genuinely user-only decision, stated as which; recommendations over options,
  decisions over questions, evidence density over adverbs.
- **In the kit:** `core.md` → keep-the-homework, `audience-altitude.md` (what only
  the user can answer — and nothing else), `core.md`'s evidence requirements,
  `core.md` → never end on a promise.

---

## Using the catalog

- **Adding a skill?** Ask which of these modes the workflow invites, and build the
  countermeasure into the skill's structure (a gate, a mandatory row, a STOP) — not into a
  hopeful "be careful" sentence. Structure survives; exhortation decays (mode 5).
- **A `/retro` pattern matches a mode?** Cite the mode in the lesson and apply its
  countermeasure at the artifact the mode decays through.
- **A mode recurs with no kit countermeasure?** That's a kit gap — file it as an issue upstream.
