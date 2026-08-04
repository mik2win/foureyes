---
paths:
  - "**/*.rb"
---

# Ruby Style and Modern Features

Based on Eloquent Ruby (Russ Olsen), The Well-Grounded Rubyist (David A. Black), Ruby 3.2-3.4 changelogs.

> Worked examples live in the `ruby-conventions-reference` skill (`references/style.md`).

---

## 1. Self-Documenting Code

- Write code that reads like well-composed prose. If a method needs a comment to explain *what* it does, rename it or split it.
- **Short methods: 7-10 lines max.** One thing, done well. If you're scrolling to read a method, it's too long.

## 2. Naming Conventions

- **snake_case** for file names, method names, variables.
- **CamelCase** for class and module names.
- **SCREAMING_SNAKE_CASE** for constants.
- Predicate methods end with `?` (`active?`, `valid?`); dangerous/mutating methods end with `!` (`save!`, `normalize!`).
- Prefix unused block params with `_`: `items.each { |_key, value| ... }`.

### Symbol vs String

- **Symbols** for identifiers, hash keys, enum-like values.
- **Strings** for display text, user content, external data.

## 3. String Handling

- **Single quotes** by default — switch to double only for interpolation.
- **Heredocs** for multiline strings — use `<<~` for stripped indentation.
- **`frozen_string_literal: true`** in every file — in Ruby 3.4 literals in un-commented files are "chilled" and mutation emits a deprecation warning when deprecation warnings are enabled (`-W:deprecated`); the comment is the reliable way to opt in (full enforcement deferred).
- Need a mutable string? Use `+''` or `String.new`.

## 4. Control Flow — Idiomatic Ruby

- **Guard clauses** — return early to reduce nesting; main logic stays at the top indentation level.
- **`unless` / `until`** instead of `if !` / `while !`. **Never** combine `unless` with `else` — use `if/else`.
- **Modifier `if`/`unless`** for single-line statements.
- **`each`, not `for`** — `for` leaks the loop variable into the outer scope.
- **Ternary only** for simple value assignment; never nest ternaries. Use `if/elsif` for complex branching.

## 5. Method Arguments

- **Keyword arguments for 2+ parameters** — self-documenting call sites. Positional is fine for 0-1 required args.
- **Never use an options hash** (`attrs = {}`) — use keyword args instead.

## 6. Method Visibility

- **`private`** — internal implementation; default for helper methods.
- **`protected`** — rare; only for methods called by instances of the same class (e.g. `<=>` comparison).
- List `private`/`protected` once, after all public methods (not before each method).
- Use `private attr_reader` for internal-only accessors.

## 7. Modern Ruby Features (3.2-3.4)

- **`Data.define`** — frozen, immutable value objects with keyword args, `with()` copies, and pattern matching. Replaces `Struct` for frozen data.
- **Pattern matching** (`case/in`) — destructure complex data; cleaner than nested `if`/`dig` chains. Pin operator `^var` matches against an existing variable.
- **Endless methods** (`def x = ...`) — for single-expression methods only; if the expression wraps, use a regular method.
- **`it` block parameter** (Ruby 3.4) — implicit single-arg block param; cleaner than `_1`.
- **`filter_map`** — `select` + `map` in one pass, dropping nils.
- Other: `Set` is built-in (no `require`); `Integer#ceildiv`; `Hash.new(capacity:)` to pre-allocate.

## 8. Data.define vs Struct vs Plain Class

| Need | Use | Why |
|------|-----|-----|
| Immutable data, no identity | `Data.define` | Frozen by default, `with()` for copies, pattern matching |
| Mutable lightweight data, internal use | `Struct` | Quick to define, setters available, good for display/scope objects |
| Behavior-rich objects, identity matters | Plain class | Full control, mutable state, complex initialization |

## 9. Object Equality

Ruby has four equality methods. Override the right ones.

| Method | Purpose | Override? |
|--------|---------|-----------|
| `==` | Value equality ("are these logically equal?") | Yes, for value objects |
| `eql?` | Hash key equality (same as `==` by default) | Yes, if used as Hash key |
| `equal?` | Identity ("same object in memory?") | **Never** |
| `<=>` | Ordering (for sort, Comparable) | Yes, if sortable |

**Rule:** If you override `==`, also override `hash` and `eql?` — otherwise Hash lookups break.
