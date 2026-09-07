# Decision craft — judgment under uncertainty

The kit's other docs cover how agents fail (`agent-failure-modes.md`), how to prompt them (`prompt-patterns.md`), and what generation is like from the inside (`core.md`). This page covers the layer above all three: **how to decide** — how a senior engineer prices a decision, buys information, and places bets when the evidence is incomplete. None of it is model-specific; all of it is what separates an executor from an architect.

The always-on distillation is `rules/_generic/core.md`; this page is the *why*.

---

## 1. Doors — reversibility prices the decision

Decisions are not equal and should not get equal process. The only property that matters at decision time is **what undo costs**:

- **Two-way doors** — an edit, a local rename, a design you can swap next week. Wrong is cheap: you walk back through the door. The correct process is *fast*: decide on current evidence, act, learn from the result. Deliberating a two-way door at one-way-door depth is pure waste — the analysis costs more than the mistake would.
- **One-way doors** — a published API, a data migration that rewrites rows, a name in the wild, a message sent, dropped data, a dependency the ecosystem will build on. Wrong is expensive or permanent. The correct process is *slow*: evidence requirements go up (observed, not inferred — `core.md` tiers), a second opinion is worth its cost, and plan mode / a written plan is justified.

Two systematic misjudgments to correct for, and the tiebreak for when neither settles it:

- **Fear inflates.** Most decisions that *feel* irreversible are two-way doors wearing a costume — code can be reverted, configs restored, designs re-cut. When you notice paralysis on a decision, first re-check the door type; usually the door is two-way and the right move is to just decide.
- **Momentum deflates.** The genuinely one-way component hides inside a reversible-looking task: the *code* of the migration is revertible, the *rows it rewrote* are not; the endpoint is easy to delete, the client that started calling it is not yours to delete. Audit a task for its one-way **components**, not its overall shape. The one-way elements are nameable: a public name, a callback or block parameter, the shape of what you yield, who owns a piece of data, a schema — each is a single slot with a single meaning, chosen once and owned forever; the additive ones — an optional keyword argument, a private helper, a new plugin — stay cheap, so spend the design time on the first list. A choice is also one-way when it **propagates**: a cheap local convention mirrored into thirty call sites is irreversible however small it looked at the one site, so price reversibility by blast radius — say how many places will copy it, and whether you get back out one tidying at a time. And when the device that would change the door is itself expensive — a flag that has to be checked in thirty places — shrink the mirroring first, then decide.
- **The two errors are not symmetric.** Misreading a two-way door as one-way costs slowness and the experiments you did not run; misreading a one-way door as two-way costs the thing itself. So when you have tried to change the door and could not, and you still cannot name the concrete undo — the command, the flag, the migration back, and roughly what it costs — price it as one-way. Slow is recoverable; gone is not.

**The senior move is a third option: change the door, not the decision.** Before accepting one-way-door process costs, ask what would make this decision reversible — a backup taken first, a feature flag around it, an expand-contract sequence instead of in-place mutation, an abstraction seam so the choice is swappable. Buying reversibility is almost always cheaper than buying certainty. This is the principle behind `/rollout`, the kit's bootstrap/teardown backups, and `/prepare` routing irreversible steps to plan mode — one mechanism, many wearings.

## 2. The cheapest killing probe

When a design, diagnosis, or plan is on the table, the instinct is to start executing it — or to gather evidence *for* it. Both are wrong. The highest-value next action is the **cheapest experiment that could kill it**:

- A design resting on "the API supports batch writes" dies or survives on one `WebFetch` of the docs — cheaper than the afternoon of building on the assumption.
- A migration plan resting on "no rows have null in that column" dies on one query.
- A refactor resting on "nothing else imports this" dies on one grep.

Order probes by **information-per-cost**, not by narrative order. A probe that can only *confirm* is nearly worthless (`core.md` → discriminating evidence); a probe that can *refute* is worth running early even when it feels like a detour. `/spike` is this principle packaged for the biggest assumption in a feature; the craft is applying it at every scale — before a plan, before a fix, before an hour of work resting on one belief, spend the sixty seconds that could kill it.

The tell that you're skipping this: you notice you *don't want* to run a check because the plan is already written. That reluctance is the signal that the check is load-bearing.

## 3. Predict before you peek

Before running any check — a test, a command, a query, opening a file you have a theory about — **state the expected result first**, concretely enough to be wrong: "this test fails with a nil error in the mapper", "this query returns zero rows", "this file contains the retry logic".

The mechanism: hindsight is frictionless. Whatever output appears, an unprediced mind fluently explains why it makes sense — generation is *good* at post-hoc coherence, which means an observation can never surprise you unless something was on record first. `core.md` says surprise is signal; a prediction is what makes surprise *possible*. Three payoffs:

- **Surprise detection.** Output ≠ prediction is the cheapest bug report available — it fires exactly when your model of the system is wrong, *before* you act on that model.
- **Calibration data.** A run of wrong predictions about a subsystem means you don't understand it yet — stop patching it and go read it (anti-thrash, one level earlier).
- **Anchoring resistance.** The prediction pins what you believed *before* the evidence, so the evidence can actually move you (`core.md` §3 — this is the same anti-anchoring move, pointed at observations instead of verdicts).

One sentence, before the Enter key. In working artifacts, write the expectation into the step (`Verify:` lines already have this shape — "expect: suite green, 0 new failures").

## 4. Calibration — confidence in falsifiable words

"Should work", "probably fine", "likely the cache" — naked confidence adjectives carry no information and no accountability: they cannot be wrong, so they cannot be trusted. Replace them with one of two falsifiable forms:

- **Evidence-tier form:** say what the claim rests on — "observed: the test passes", "inferred from the naming convention; not verified". (`core.md` tiers.)
- **Bet form:** say what would surprise you — "if this is wrong, it shows up as X", "I'd expect fewer than N failures; more means my model is off". A bet names its own refutation, which makes it checkable — and makes *you* calibratable over time.

For **estimates** (effort, duration, risk), two corrections beat any amount of care:

- **Reference class over decomposition.** Estimating by summing imagined steps produces the optimistic bound — imagined steps don't include the unknown-unknowns, and the unknown-unknowns are where the time goes. Anchor instead on the *reference class*: what did the last similar task actually cost (the archived plans and deviation reports are the kit's local record)? Decompose to plan the work; reference-class to size it.
- **Ranges over points, and say what widens them.** A point estimate hides its uncertainty; "2–5 files, more if the pattern leaked into tests" states both the spread and its driver — which tells the reader what to check to narrow it.

## 5. The pre-mortem — assume it already failed

Before executing a plan, run one deliberate exercise: **"it shipped; it failed; it's three months later — what was the cause?"** Write the top two answers.

This is not "list some risks". Prospective hindsight — *assuming* the failure as an accomplished fact — retrieves differently than open-ended risk brainstorming: "what could go wrong?" invites generic answers (scope creep, edge cases); "why *did* it fail?" forces a specific causal story about *this* plan, and specific stories are checkable. It is the lens trick from `core.md` §7 pointed at the future.

What to do with the answers: each named cause becomes either a **probe now** (§2 — if the cause is checkable today, check it before executing), a **plan risk with a `Verify:` line** (if it's only observable during/after execution), or a **door change** (§1 — if the cause is catastrophic, restructure so it's survivable). A pre-mortem whose findings don't land in the plan was theater (failure mode #13 — format compliance).

`core.md` already prescribes a micro pre-mortem per answer ("where is this turn most likely wrong?"); this is the same move at plan scale, run once, before execution starts.

## 6. Decomposition sizing — when not to split

The kit is rich in decomposition machinery (`/prepare` waves, `/to-issues` slices), so the under-taught skill is the opposite one: recognizing when splitting makes things worse. Splitting is not free — every cut invents an interface between the parts, and an interface invented *before* understanding is a guess that both sides then build against:

- **Don't split what shares one unknown.** If every part depends on the same unresolved question (which API shape, which data model), the parts cannot proceed independently — they'll each guess differently and diverge. Resolve the unknown first (a `/spike`, a probe), *then* split; the cut lines are usually obvious afterwards and wrong before.
- **Don't split below the verification grain.** A part that cannot be independently verified ("half the refactor — nothing compiles until the other half lands") is not a unit of work, it's a fraction of one; the wave structure's parallel safety was the point (`/prepare`), and an unverifiable slice forfeits it.
- **Do split at door boundaries.** Isolate the one-way step (the migration, the publish, the send) into its own smallest possible unit, so maximum learning happens *before* it and minimum regret rides *on* it. This is expand-contract's whole idea (`/rollout`).
- **The seam test:** a good cut can be described as a contract in one sentence ("A produces the list; B renders it"). If describing the interface takes longer than describing the work, the cut is wrong — merge the parts.

## 7. Invariants — name what must stay true

Before changing code, name the property the change **must preserve** — one sentence: "the ledger still sums to zero", "the list stays sorted after every operation", "each message is sent at most once", "this endpoint never returns another tenant's rows". Then aim verification at the invariant, not just at the feature:

- **The invariant is the review lens.** "Does this diff preserve X?" is a sharper review question than "is this diff good?" — it turns a vibe check into a proof obligation, and it's the question to hand `code-reviewer` when the change touches anything with an invariant.
- **Test the property, not only examples.** Example tests pin points; a property pins a region. Where the stack has a generator library (Hypothesis, fast-check, StreamData…), a property test — "for *all* inputs, sorted-ness holds" — finds the case no one imagined; where it doesn't, a hand-rolled loop over randomized/boundary inputs asserting the invariant is 80% of the value. Route via `/test`; the invariant sentence is the seed.
- **An edit with no nameable invariant is exploration, not implementation.** That's fine — but then it belongs in `/spike`/`/prototype` clothing (throwaway, learning-shaped), not merged as if it were engineering.

Invariants also compound: `codebase-design` puts them at module interfaces; `/domain-model` records them next to the terms; a stated invariant is exactly the "written constraint at the site" that protects deliberate weirdness from regression-to-the-mean (`core.md` §5).

## 8. The horizon — price by lifespan

The same request text hides three different artifacts, and nothing in the wording tells you which one you're building:

- **A throwaway probe** — lives hours-to-days. Correct engineering: no new dependencies, no framework, no test suite beyond a smoke check, the fastest thing that answers the question. Gold-plating it is waste.
- **An internal tool** — lives weeks-to-months, gets occasional features. Correct engineering: boring stack, a seam or two, tests on the logic that would hurt.
- **A living product surface** — lives years and has a *feature trajectory* (today "show the chart", next month filters, then annotations, then realtime). Correct engineering: **adopt the ecosystem** — the framework, the charting library, the component model — because hand-rolling what a mature ecosystem provides means incrementally building a worse framework nobody else can maintain, one "small JS file" at a time.

Both mis-pricings are real and symmetric. Under-pricing: the hand-rolled trio of script files that quietly becomes the team's unmaintained UI framework — every next feature costs more context, more tokens, more risk than the framework adoption would have. Over-pricing: React for a one-off diagnostic page — dependency weight, build tooling, and upkeep bought for nothing. The failure isn't picking wrong; it's **pricing without asking what the lifespan is**.

**Techniques:**

- **The horizon is the operator's fact, not your inference.** It lives in their roadmap, not in the request text — so it's a legitimate, high-value question, not an admission of confusion: *"Is this a one-off, or the start of something we'll grow? What's the next feature after this one?"* One question at the start re-prices every decision downstream (`audience-altitude.md`: direction is exactly what only the user can answer).
- **The trajectory test.** Before hand-building, name the next two features the user would plausibly ask for. If each would be a config line in an ecosystem tool but a rewrite in your hand-rolled version, the horizon is telling you to adopt (route the choice through `/select-tech`).
- **Direction decisions are operator-confirmed.** Adopting a framework, a major dependency, or an architectural style sets direction for everything after — recommend with reasoning, then get explicit confirmation (one `AskUserQuestion`, your default stated). Never adopt silently; never hand-roll silently past the trajectory test. Between confirmations, don't overfit: build for the confirmed horizon, not the imagined one (speculative generality is the same waste at a different altitude). The positive branch is narrow but real: build the flexibility now only when adding it later would be substantially harder — a published contract, a stored shape, a migration you would have to run twice — and test that against the callers you actually have. If the variation is already visible in two of them, the hook is warranted; if you are imagining the second caller, it is not.
- **Record the horizon in the artifact** (spec/plan) so downstream stages inherit the pricing instead of re-guessing it.

## 9. The operating list — what a new technology actually costs

A cost paragraph that describes the technology is not an estimate. Price a candidate by walking the list of things every operated component needs, saying for each whether the existing stack already answers it or this thing makes you answer it again: logging · health checks · packaging · deployment · init and supervision · a unit-test story · alerting · operational metrics · backups · restores that have been *tested* rather than assumed · scaling · security upgrades · training everyone who will ever touch it · and the switching cost of leaving.

Two properties make this the cheapest honest estimate available. It is **enumerable** — fourteen lines, each answerable in a sentence, so an omission is visible instead of hidden inside a vibe. And it is **differential** — the incumbent already answers most of it for free, so the walk measures the *marginal* cost of the addition rather than the absolute cost of running software, which is the number a comparison actually needs.

Read backwards, the same list is the maturity test. "Mature" is not age and not taste: it is that you can name the main ways the thing will let you down and what you would do about each. A technology whose failure modes you can enumerate is safe to be old and ugly; one you can only describe by its features is not understood, and its unknown failures are the expensive kind — a known one can be tested for this afternoon, an unknown one is the four-month investigation. Anything new has more of both. Stars, release cadence and "everyone uses it" are not entries in the list.

`/select-tech` Phase 4 walks the list per finalist; `/incident` reads it backwards when the component on fire is the one nobody priced.

## 10. Where the complexity lands — build time or run time

When two options produce the same result they are rarely the same decision, and the axis that separates them is **which phase pays**. Build-time complexity is spent once and re-spent on every change: more data to prepare, more tooling, a longer release cycle, a heavier local setup. Run-time complexity is spent forever: another component in the hot path, another thing that can be down at 3am, another line in the on-call handover, another dependency inside the failure envelope.

Name the phase before choosing. Build-time cost is paid by the people building, is visible in the pipeline, and shrinks as the work stabilizes; run-time cost is paid by whoever is on call, is invisible until it fires, and grows with traffic. Two options that tie on a feature matrix can be a week apart in build cost and a year apart in operating cost — and it is the second number that decides who carries the option for the rest of its life.

## 11. Compensation is not a rollback

A flow that touches more than one system in sequence — charge the card, reserve the stock, dispatch the courier — has no rollback, only compensation, and "we undo the earlier steps on failure" is a plan with three unnamed risks inside it. Say them before the plan is accepted:

- **There is no isolation.** Everything the earlier steps published was already visible and may already have been acted on — a confirmation sent, a webhook delivered, a consumer that has already counted the row. The compensating write cannot reach those effects, and the systems holding them may have no undo of their own.
- **The compensation is a write like any other, and can fail** — often against the very system that is already failing. When it does, the data is worse off than at the start (money taken, nothing shipped) with no third party left to repair it, so the honest end of that branch is manual intervention: say who performs it and how they are told.
- **The user is made to wait for, and care about, someone else's business step.** Holding the request open until every downstream system has agreed makes the slowest partner the response time, and turns a failure that is not the user's problem into the user's error message.

Where the business can tolerate it, prefer recording workflow **state** over compensating: mark the flow partially complete, answer the user immediately, and let retries or a person close it out. That costs a state machine and somewhere to see stuck flows; it buys a response time you control and a failure that has an owner.

## 12. A principle cited without its limit is not an argument

Design rules earn their keep by having an edge, and a rule quoted with no edge is a preference in uniform. When a design move rests on one of these, state in the same breath the condition under which it would be the wrong move here, and why that condition does not hold:

- **Hiding information** is wrong when the information is genuinely needed outside the module. Hiding it there does not produce depth, it produces a false abstraction: callers work around it, and the workaround becomes the real interface.
- **Pulling complexity downward** is wrong unless three things hold together — the detail is close to what the module already does, absorbing it simplifies something else, and it simplifies the interface. A detail that arrives as new parameters fails the third: it has been moved, not absorbed.
- **Masking a failure** is wrong when the caller needs the failure to stay correct. Swallowing it, defaulting past it or retrying it away is legitimate only when the caller's job is unchanged by its having happened.
- **Consistency** is wrong when the things really are different. Forcing one shape onto two different cases hides the difference at exactly the place a reader needs to see it.

---

## Using this page

| Practice | Where the kit wires it |
|---|---|
| Doors / reversibility pricing | `rules/_generic/core.md`, `/prepare` (irreversible → plan mode), `/rollout` (change the door), bootstrap/teardown backups, `core.md` autonomy (reversible → act) |
| Cheapest killing probe | `/spike` (packaged form), `core.md` → discriminating evidence, `finding-verifier` (default-refute) |
| Predict before you peek | `rules/_generic/core.md`, plans' `Verify:` lines, `core.md` → surprise-is-signal |
| Calibration & estimation | `rules/_generic/core.md`, evidence tiers, `/retro` + archived deviation reports as the local reference class |
| Pre-mortem | `/prepare` (plan-level ritual), `core.md` → pre-mortem-your-own-answer (turn scale) |
| Decomposition sizing | `/prepare` waves + `/to-issues` slices (how to split), this page §6 (when not to) |
| Invariants | `codebase-design` (interface invariants), `/test` (property tests), `/domain-model` (record them), `code-reviewer` (review lens) |
| Horizon pricing | this page §8, `/analyst` (horizon interview question), `/prepare` (horizon row + direction-confirm), `/select-tech` (horizon as constraint) |
| The operating list | `/select-tech` Phase 4 (per finalist), `/incident` (the component nobody priced), this page §9 |
| Build time vs run time | `/select-tech` (the tie-break between equal results), `/prepare` §2.5.1 (alternatives table), this page §10 |
| Compensation vs rollback | `rules/_generic/resilience.md` (pointer), `/prepare` (the failure branch of a multi-step flow), this page §11 |
| The limit of a principle | `codebase-design` (where the principles are stated), `/arch-health` + `/code-review` (findings that cite one), this page §12 |

**The meta-rule:** every section is one economic move — **price the decision before paying for it**. Reversibility sets the price of wrong; probes buy information at the cheapest vendor; predictions and calibrated language keep the books honest; pre-mortems price the failure before it's bought; decomposition and invariants decide what's load-bearing before weight lands on it. Process is not virtue — process is spend, and the craft is spending it where wrong is expensive and skipping it where wrong is cheap.
