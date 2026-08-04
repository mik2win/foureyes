---
paths:
  - "**/*.rb"
---

# Ruby OOP Principles and Class Design

Based on POODR (Sandi Metz), 99 Bottles of OOP, Clean Architecture (Robert Martin), Eloquent Ruby (Russ Olsen). These are the principles the team actively follows — apply them when writing or reviewing code.

> Worked examples live in the `ruby-conventions-reference` skill (`references/oop.md`).

---

## 1. Single Responsibility (SRP)

- Every class and method has one reason to change. When a class starts doing two things, split it.
- Keep entity logic on the entity; move notification, PDF generation, etc. into their own classes.

## 2. Dependency Injection

- Pass collaborators in; don't instantiate them inside. Hardcoded dependencies create invisible coupling you can't test, swap, or configure.
- Inject the real implementation in production, a double/stub in tests.

## 3. Tell, Don't Ask

- Tell objects to do things; don't interrogate state to decide for them. The object that owns the data owns the behavior.
- Asking for state and acting externally duplicates knowledge — every caller must update when the state changes.
- Let an object present itself (`defect.full_category`) instead of formatting its parts externally.

## 4. Law of Demeter (POODR)

- Limit method chaining — talk only to immediate neighbors; avoid "train wrecks" that reach through distant objects.
- Delegate or encapsulate the chain behind one method on the owning model.
- One dot per statement is a guideline, not a rule. Chaining on the same type (e.g. `array.select.map`) is fine; the goal is to avoid coupling to distant internal structure.

## 5. Duck Typing (POODR)

- Depend on what objects **do**, not what they **are**. If multiple objects respond to the same message, trust the interface.
- Avoid `is_a?` dispatch — it creates rigid coupling and violates Open/Closed (a new type means editing every check).
- Optionally define the contract explicitly with a module raising `NotImplementedError`.

## 6. Managing Dependency Direction (POODR)

- Depend on things that change **less often** than you do:
  - Abstractions are more stable than concretions
  - Widely-used classes are more stable than rarely-used ones
  - Framework classes are more stable than your application classes
- When choosing which class depends on which, point the dependency toward the more stable one (volatile → stable).

## 7. Tolerate Duplication / Shameless Green (99 Bottles)

- Don't extract an abstraction at the first sign of repetition. Start with the simplest passing solution (Shameless Green), even if naive or duplicated.
- **Two** similar things, abstraction unclear → leave duplicated. **Three** with an obvious shared concept → extract.
- Wrong abstraction is far more costly than duplication — it bends every new case to fit.

## 8. Open/Closed Principle (99 Bottles, SOLID)

- Design classes to be **extended** without **modifying** existing code (e.g. inject a strategy).
- Add new behavior (new formatter, new strategy) without touching the class that uses it.

## 9. Name Things by What They ARE

- Name classes/modules/services by what the object **IS** (noun: `ReportGenerator`), not what it does (verb: `GenerateReport`). Avoid vague names like `reporter`.

## 10. Composition over Inheritance

- Use modules/mixins for shared behavior. Avoid deep inheritance chains.
- Inheritance only when "is-a" is truly present and types share identical structure (1-2 levels max), e.g. custom error classes under `StandardError`.

## 11. SOLID + DRY + YAGNI

- **YAGNI wins over premature abstraction** — don't build for hypothetical future requirements.
- **DRY applies to knowledge**, not just syntax — the same business decision should live in one place.
- **SOLID** guides class design, but apply pragmatically — don't over-engineer for a small team.
- Don't force unrelated things into a shared abstraction (`case type when ...`); prefer separate classes even with some duplication.

## 12. Modules — Namespaces AND Mixins

- **Namespaces:** group related classes under a module to avoid collisions and communicate structure (instead of verbose flat names).
- **Mixins:** `include` for instance methods, `extend` for class methods, `module_function` for utility functions callable both ways.
- **`self.included` hook:** use it to `base.extend(ClassMethods)` and add class methods when a module is included.

## 13. Service Objects

- Name by what the object **IS** (noun), not what it does (verb). Place in a dedicated directory.
- **Pattern 1 — single `#call`** for focused, single-operation services.
- **Pattern 2 — multiple public methods** when a service is a facade over related operations. Use it when:
  - Multiple callers need different slices of the same computation
  - Methods share significant setup or internal state
  - The class reads naturally as an interface/facade
- Avoid Pattern 2 when methods are unrelated — that's a sign the service should be split.

## 14. Error Handling

- **Custom hierarchies:** root domain errors in a module-level `Error < StandardError`. Rescue the base class for broad handling, specific classes for targeted handling.
- **Rescue specific exceptions**, never bare `rescue` — bare `rescue` catches `StandardError` and hides real bugs (`NoMethodError`, `NameError`).
- **Exceptions for exceptional cases**, not control flow — don't use `rescue` as a fancy `if`.
- **Re-raise with context** when wrapping errors from external systems.
- **Recoverable errors:** return an error value, let the caller decide — for per-item failures in batch processing.
- **Unrecoverable errors:** raise and halt — for startup/config failures that make the whole run pointless.
