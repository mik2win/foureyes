---
name: prototype
disable-model-invocation: true
description: >-
  Build a THROWAWAY prototype to flesh out a design before committing to it — either a runnable
  terminal/script app to explore state & business-logic questions, or several radically different
  UI variations toggleable from one route to compare looks and flows. The product is a learning,
  not shippable code. Distinct from /spike (validates ONE binary hypothesis) — prototype EXPLORES
  a design space with multiple options.
  TRIGGER when: the user wants to explore how a feature should look or behave, compare UI options,
  feel out a flow, or "mock something up to react to" before designing for real.
  DO NOT TRIGGER when: the user wants to validate one risky assumption yes/no (use /spike), build
  the real feature (use /implement), or work out requirements in words (use /analyst).
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion, Agent
effort: medium
---

# Prototype: $ARGUMENTS

Build a **throwaway** prototype to make a fuzzy design concrete enough to react to. You learn
fastest by seeing options side by side and poking at them — not by arguing about them in the
abstract. The only product is a **decision**; the code is disposable.

`$ARGUMENTS` is the design question to explore. If empty, ask what to prototype, then stop.

This skill carries only invariant workflow logic. Run commands, where source lives, the UI stack,
and routing come from `.claude/PROJECT.md`. Prototype code lives in a **clearly throwaway
location** and is **never** promoted into production — the real version is built fresh through the
pipeline.

---

## Phase 0 — Load profile

1. Read `.claude/PROJECT.md` — **Commands** (`run`), **Stack** (UI framework, language), and
   **Architecture** (where the app's routes/entry points live, so the prototype can attach without
   polluting real source). If missing or `TEMPLATE`, fall back to the root `CLAUDE.md` (always in
   context) when it carries those facts — proceed on it, noting you're running without a kit
   profile. Only if *neither* has them, **STOP** → `/bootstrap` first.
2. If `CONTEXT.md` exists, read it so the prototype uses the project's real domain vocabulary.

---

## Phase 1 — Frame & choose a mode

Pin down the question, then pick the mode that answers it:

| Mode | Use when the open question is about… | Build |
|------|--------------------------------------|-------|
| **Logic** | state, business rules, data shape, an algorithm, a flow's branches | a runnable terminal app / script — see [LOGIC.md](LOGIC.md) |
| **UI** | how it should look or feel, layout, interaction, which of several designs | several radically different variations toggleable from one route — see [UI.md](UI.md) |

If the question is genuinely both, do **Logic first** (settle the model), then **UI** on top of it.
If it's really a single yes/no feasibility check, this is the wrong skill — route to `/spike`.

---

## Phase 2 — Build the throwaway

- Put it in a **clearly disposable location**: a scratch dir (`prototype/`, `.prototype/`) at the
  repo root, or — for UI mode — a single throwaway route the project can serve, clearly named so
  no one mistakes it for production.
- **Cut every corner that isn't the question.** Hardcode data, stub services, skip auth, skip
  tests, skip error handling. The prototype exists to answer one design question, nothing else.
- **Logic mode:** make it *runnable* and interactive so the user drives it and sees real behaviour,
  not a description (LOGIC.md).
- **UI mode:** build **2–4 genuinely different** variations (not tweaks of one), all switchable
  from one route so the user flips between them and compares (UI.md). Use the project's real UI
  stack so the look is honest.

For a multi-file build, fan out with the **Agent** tool, then assemble — but keep it small; a
prototype that's growing into a feature should stop and route to `/prepare`.

---

## Phase 3 — Run & react

1. Run it via `PROJECT.md` → Commands (`run`) or a direct one-off invocation.
2. Put it in front of the user. **`/grill`** them on what they're seeing: which variation, which
   behaviours feel right, what's missing, where the model breaks. This is the payoff — concrete
   reactions, not abstract opinions.
3. Iterate cheaply: tweak and re-run. Cheap iteration is the whole point.

---

## Phase 4 — Capture the decision & discard

1. **Record the learning** — the chosen direction (which variation / which logic model), *why*, and
   the constraints discovered. If domain terms or a design decision crystallized, hand them to
   `/domain-model` for `CONTEXT.md` / an ADR. This learning is what survives.
2. **Discard the code.** Delete the prototype, or move it to the scratch dir clearly marked
   throwaway/gitignored. **Never** integrate it — the real feature is built fresh via
   `analyst → prepare → implement`.

---

## Output

```
## Prototype — <design question>

**Mode**: Logic | UI
**Built**: <what + where (throwaway location)>
**Variations explored**: <UI: A/B/C summary | Logic: the model(s) tried>
**Decision**: <chosen direction> — <why, from the user's reactions>
**Constraints discovered**: <what the prototype revealed>
**Next**: /analyst (spec the chosen design) | /prepare (plan it) | /implement (if trivial)
**Disposition**: deleted | moved to scratch and marked throwaway
```

---

## Hard rules

- **Throwaway only.** Prototype code is never promoted; the real version is built through the
  pipeline. Its product is a decision, not code.
- **Explore options.** UI mode shows *several* genuinely different variations — that's how it
  differs from a single mock.
- **Outside production source.** Scratch dir or a clearly-marked throwaway route — never woven into
  the Architecture source paths.
- **Stop if it's becoming a feature.** Outgrowing "quick exploration" → route to `/prepare`.
- **Facts from PROJECT.md.** Run command, UI stack, and routing come from the profile.

## Cross-reference

- **`/spike`** — validate ONE risky hypothesis (binary, time-boxed). Prototype EXPLORES a design
  space with multiple options; spike ANSWERS a single can-it-work question.
- **After:** `/analyst` (spec the chosen design) or `/prepare` (plan it).
- **`/domain-model`** — capture terms/decisions the prototype surfaced.
