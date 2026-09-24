# Claims audit — how prose goes false

A catalog for `/audit-quality` **Check 11** (and for anyone re-reading a changed file): the recurring ways a docstring, comment, help string, operator doc or plan sentence stops being true while the code around it stays healthy. Mined from a 287-entry agent-memory corpus on one Python project (2026-09): roughly **60 of 109 stack-neutral lessons** were this class, and its top entry — *a rule rewrite leaves a twin docstring behind* — recurred **43 times**, the highest count in the whole corpus.

Why it is a class and not a rash of mistakes: a contract change is greppable **by its symbol**, and the sentence that repeats the contract contains no symbol. Every search the author runs is blind to it by construction. The countermeasure is always the same shape — grep the *claim*, not the identifier — but it takes a different form per pattern, so the patterns are worth knowing by name.

Each row: **the shape → what falsifies it → the probe.** Nothing here is stack-specific; the examples are de-domainized.

---

## 1. The twin sentence (43×)

**Shape.** A rule lives in two places: the code that enforces it, and a sentence that restates it — a module docstring, a CLI help string, a rule file, a test name, an operator runbook. The change touches the enforcer.

**What falsifies it.** Any contract edit. The twin survives in: the old condition's wording ("skips rows below the floor" after the floor became inclusive), a cardinal ("four routers" after the fifth), an enumerated member list, the old text embedded as a quoted literal in a test, a CLI flag token that was renamed, a header's "limits" list, the comment sitting directly above a changed constant.

**Probe.** After the diff, grep the *prose* of the rule across code, tests, rules and docs — one grep per surface above, not one grep for the symbol. **A fix round is a first-class occurrence site**: in this corpus, seven of the 43 occurrences were created by the round that fixed an earlier one.

## 2. The quantifier over a finished list

**Shape.** "Both handlers validate the payload." "All three writers take the lock." "The only caller is the scheduler."

**What falsifies it.** One added member — and adding a member is exactly what a healthy codebase does. The sentence is false the moment the list grows, and nothing in the adder's diff mentions it.

**Probe.** A completed enumeration gets either the members named or no count at all; "both/all/every/the only" over an extensible list is a finding on sight. Conversely, when you *add* a member, grep the universally quantified headers above the list you joined.

## 3. The numberless premise under a changed constant

**Shape.** `TIMEOUT = 30  # one retry fits comfortably inside the caller's budget`. The constant becomes 300.

**What falsifies it.** A change of more than ~2× in either direction. The number in the code is updated by definition; the sentence explaining *why that number* carries no number, so no reviewer's eye catches it, and it now argues for the old magnitude.

**Probe.** When a constant moves by more than ~2×, read its comment as two separate claims — the value and the premise — and re-derive the premise. **Paired constants** (a deadline and the interval of the job it waits on; a buffer and the batch size that fills it) are re-checked together or not at all.

## 4. The comparative with one population

**Shape.** "Stricter than the old gate." "This path is cheaper." "Errs high."

**What falsifies it.** Nothing — it was never checkable. Stricter over which inputs? Cheaper than which alternative, measured on what? A comparative with one named population is unfalsifiable prose that later reads as a measured result.

**Probe.** Demand both populations and the axis. The same defect wearing a number: **a before/after delta labelled as one job's cost**, measured on a store several jobs write to. List every writer of the measured thing and say which ones were serialized against the job; if none were, the delta is an upper bound, not a cost.

## 5. The absolute guarantee over a producer with branches

**Shape.** A summary sentence states a guarantee without qualification — "every record carries a source stamp". The guard it refers to is honest; the overclaim sits one level up, in the caller's summary or the plan's abstract.

**What falsifies it.** The producer's non-happy branches: the legacy rows written before the stamp existed, the default that fills in when the field is absent, the inferred value, the re-stamped row, the empty collection that passes a truthiness test. Each is a live counter-example the guarantee's author never enumerated.

**Probe.** For every absolute contract sentence, list the producer's branches and walk them. **Where a document both claims a guarantee and elsewhere lists a residual, the residual wins** — the guarantee is the sentence that is wrong.

## 6. The licence to delete

**Shape.** "X is now redundant." "No longer load-bearing." "Carried by Y since the refactor." "Measured: 0 live callers, revisit if that changes." "AC-3 satisfied."

**What falsifies it.** Time, and the fact that these read as *permission*. A later session deletes X, or builds on the claim, without re-checking — that is what the sentence is for. In this corpus roughly half of them were false by the time they were acted on, and the "revisit if" trigger had usually already fired.

**Probe.** Treat each as a claim someone will act on: exercise the property on one concrete input, or date the census so its staleness is visible. The tense variant is the sharpest: **operator docs written in the past tense** ("the table was repaired on <date>") shipping in the same change as the migration they describe, before anyone has run it. Check the target store for the migration's artifact before accepting the tense.

## 7. Position claims that a move voids

**Shape.** "Safe because it is a sibling of the validator." "This mounts the provider itself." "Pulled up into the base class, so subclasses inherit the check." "`Sub::method` does the normalizing."

**What falsifies it.** Relocation — of the node, the component, the method. The claim stays *true-sounding* and becomes unverifiable: after a method is hoisted into a base, `Sub::method` citations elsewhere are still semantically right and no longer greppable, so the next reader concludes the citation is stale and deletes it, or trusts it and looks in the wrong file.

**Probe.** A move or delete sweeps four spellings — the dotted path, the slashed path, the bare filename, and the moved concern's vocabulary — across code, tests, rules and docs. A surviving "this is safe because…" next to a moved thing is the highest-value hit in the sweep.

## 8. The behaviour-preserving split that mints new claims

**Shape.** One module becomes three. The move is verbatim, so the proof of correctness covers the moved code entirely.

**What falsifies it.** The **only-in-new** lines — the three new module docstrings, which nobody moved and nobody verified. They carry exactly the claims that a split invites: "mirrors the reader in X", "kept under the size budget", "the counterpart of Y".

**Probe.** After a behaviour-preserving split, audit only-in-new prose as fresh claims: open every "X mirrors this" and check it, and recompute every size justification from the file as it now stands.

## 9. The cited precedent that argues the other way

**Shape.** "Precedent: the ingestion path makes the same trade." "Same approach as the reporting module."

**What falsifies it.** Reading the precedent. Commonly it makes the opposite trade on the axis being justified, or makes the same trade *with* a safeguard the citer omits, or rests on a measurement that has since gone stale. The sharpest version: the citing change adopts the option the cited decision record explicitly **rejected** — because only the verdict was read, not the rejected-options section.

**Probe.** Open every cited precedent and check it on the axis being justified. Re-derive any number it rests on. In a decision record, read the rejected options before the verdict.

## 10. The hardened surface with quiet twins

**Shape.** A "no vacuous green" or "honest error" fix lands on the surface the author was looking at — the verbose report, the one syscall they traced.

**What falsifies it.** Every other output surface: the one-line summary, the quiet mode, the JSON payload, the exit code, the persisted artifact as opposed to the console banner. They keep the defect, and the fix's prose says the defect is gone. Related: a **user-facing string shortened** in a layering fix — the banner still reads well, the persisted report has silently lost the policy text.

**Probe.** Drive the adversarial input through every output surface and every syscall on the path. When a string is shortened, grep its consumers by field name and ask which of them persists.

## 11. The narrowness claim over a family

**Shape.** "Narrow catch — only the transient timeout." "The matcher was tightened to drop the false positive."

**What falsifies it.** The hierarchy, and the word family. A catch clause named for one member usually names the library's *base* class and swallows every subclass, some of them fatal. A matcher narrowed to kill a false positive also drops real inflected hits, and the plan's expected count bakes the loss in as if it were the target.

**Probe.** Enumerate the caught class's subclasses at runtime and ask which are transient and what the handler destroys on each. For a narrowed matcher, diff the old and new match sets item by item over the real corpus: the searched vocabulary is a word family, not a token.

## 12. The boundary word that is exact in two directions

**Shape.** "Below the threshold" vs "at or below the threshold", applied by one global find-and-replace across the surfaces that describe a gate.

**What falsifies it.** The surfaces mean different things. "What is missing" and "what is absent" sit on opposite sides of the same boundary, so a single consistent word swap makes one of them exactly wrong — and it is exactly wrong, not approximately, which is why no test notices.

**Probe.** Before a one-word boundary edit, classify each surface (missing / absent / complete) and read the gate beside the string, not the string alone.

## 13. The parity claim over a hand-rolled validator

**Shape.** "Re-states every rule in the schema." "Equivalent to the library check, without the dependency."

**What falsifies it.** A differential run. Hand validators characteristically check required fields and nothing else, crash on inputs the real validator tolerates, and conflate an explicit null with an absent key.

**Probe.** Fuzz the hand validator against the real one in a throwaway environment before believing the claim. **An explicit null is not absence** — assert on that case specifically.

## 14. The one term with two producers

**Shape.** A glossary defines a term; two parts of the code compute it, over different spans or populations. The glossary holds whichever definition was written first.

**What falsifies it.** Any change that extends a body sentence using the term. The sentence is now true of one producer and false of the other, and the glossary row silently picks a side.

**Probe.** When a change touches prose that uses a glossary term, grep the glossary row *and* every producer of that term. Two producers over different spans is itself a finding — for `/domain-model`, not for the docstring.

---

## Using this list

- In `/audit-quality`, Check 11 is the six probes that cover most of the volume; this file is for when a finding does not fit them, or when the scope is a large prose-carrying change (a split, a move, a migration, a rename).
- Every finding is still `path:line` + the sentence + **the one grep or input that falsifies it**. A sentence that merely feels stale is not a finding — `finding-verifier` will bounce it, and rightly.
- The inverse rule matters as much: a *behaviour* finding whose only evidence is a comment is a classic false positive. A finding about the **comment's own truth** is valid. The two are easy to confuse and `agents/finding-verifier.md` draws the line.
