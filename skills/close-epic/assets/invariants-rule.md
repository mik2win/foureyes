---
description: <Silent class> invariants — <the four or five rules in one line, so the loader knows what it is buying>. Loaded on file read in the paths below.
paths:
  - '<narrowest globs that actually own the class — the models, services, presenters and client modules that touch it, never `**/*`>'
---

# <Silent class> path

> **Template.** `/close-epic` proposes this file when **≥2 findings of one silent class** (money, time, access) land in a single epic. Copy it to the project's rules directory, fill it from the findings themselves, delete this blockquote. Every numbered line below must be a violation that **actually happened and was fixed** — an invariant nobody has broken is a guess, and a rule of guesses is context the project pays for and no one trusts.

**Why this class is silent.** <One paragraph: what wrongness on this path looks like from the outside. A wrong total renders and persists with no stack trace; a naive timestamp compares fine until the DST boundary; a missing scope returns the other tenant's rows with a 200. Name the reason the test suite does not catch it — usually that the specs assert only the cases they already name.>

## 1. <The invariant, as an imperative>

- <The rule, then the symbol that owns it in backticks: `Pricing::DiscountAllocator`, `Orders::Internal::LineState#charge`. The symbol is the point — a reader who disagrees with the rule has somewhere to go and read.>
- <The one sanctioned exception, with its path glob. A rule with no stated exception gets a hand-rolled one within a month.>

## 2. <Next invariant>

- <…>

## Smells — what to flag on sight

| Smell | Severity |
|---|---|
| <the shape the finding took, spelled as a grep-able tell> | CRITICAL |
| <a copy of a formula changed alone, one of N> | STRUCTURAL |

**CRITICAL** = wrong value ships silently · **STRUCTURAL** = copies drift apart.

---

**Keep it honest as it ages.** Each invariant carries the symbol that enforces it, so a reader can check the rule against the code rather than trusting the sentence — the whole failure mode of a rule file is prose outliving its enforcer (`/audit-quality` Check 11). When the enforcer moves, the line moves with it or comes out.
