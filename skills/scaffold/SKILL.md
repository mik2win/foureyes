---
name: scaffold
disable-model-invocation: true
description: >-
  Add a new module, component, command or adapter modelled on an existing one: read the canonical
  exemplar first, place it per the profile's Architecture, wire it into every registration point,
  and prove each wiring with a command rather than by reading the code. Built around the failure
  this task actually has — a registration that never took raises nothing, and the new thing is
  simply absent from the listing.
  TRIGGER when: the user asks to add a new module / component / command / adapter / provider
  "like the existing one", or to create a new <X> modelled on <Y>, in a project that has an
  extension point (a registry, a composition root, a plugin directory).
  DO NOT TRIGGER when: the work is a whole feature that needs a plan first — that is /prepare;
  it is one known edit inside files that already exist — /implement; the contract or the seam
  itself is what needs designing — /api-design or /codebase-design; the new thing is throwaway
  exploration — /prototype.
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, AskUserQuestion
effort: high
---

# Scaffold: $ARGUMENTS

Create a new artifact of a kind this repo already has, and leave it **provably wired**. The
checklist below says *what* must exist; the exemplar says *how it looks here*. Where another
skill already owns a step, this one links to it instead of restating it.

## Phase 0 — Read the exemplar FIRST

- [ ] `PROJECT.md` → Architecture → **Canonical exemplars** names the nearest existing thing of
      the same kind. Read it end to end, plus the file where it is registered.
- [ ] Mirror that shape — **do not invent structure from this checklist alone**.
- [ ] The exemplar is a candidate, not an authority (`rules/_generic/code-quality.md`): if it
      carries a known wart, say so and deviate on purpose, not by accident.
- [ ] No exemplar exists → this is not scaffolding. Route to `/prepare` (a new kind of thing) or
      `/api-design` (a new contract) and stop.

## Phase 1 — Placement

`PROJECT.md` → Architecture decides the layer, the directory, and where this logic must **not**
go. Do not re-derive it from the file tree when the profile answers it.

## Phase 2 — Registration points

This is the phase the skill exists for. A new artifact usually fails here, and nothing complains.

- [ ] List **every** registration point from `PROJECT.md` → Architecture → **Wiring /
      registration points**. For each one: the file, the edit, and the command that proves it took.
- [ ] **Load-bearing side-effect import.** An import whose only job is to run a decorator or a
      registration call looks removable and is not. Skip it and there is no error — the artifact
      is just missing from `--help`, the list, the menu. Tests pass, review passes, the thing is
      not there.
- [ ] **Proof is a command, not a reading.** `<cli> --help`, a list subcommand, a route dump, the
      registry length printed in one line. Reading the import proves you wrote it, not that it ran.
- [ ] Coordinated edits land in **one session**: an enum member, a dictionary entry and an import
      that must agree are one edit, not three — partial application drifts silently.
- [ ] A shared registry file is a **serialization point**
      (`rules/_generic/parallel-wave-execution.md`): in a parallel wave exactly one session touches
      it, and the others declare it as a dependency.

Sort the touchpoints before editing — the third column is what stops collateral edits:

| Kind | Meaning |
|------|---------|
| **Always** | the registry / composition root / manifest entry, without which the artifact does not exist |
| **Conditional** | only under a named condition (a template file, a config slot, a new event channel) — name the condition, then check whether it holds |
| **Zero-edit — do NOT touch** | consumers that resolve the artifact dynamically by name; editing them is the classic scaffolding regression |

## Phase 3 — Smoke run, then parity

- [ ] Run it. `PROJECT.md` → Commands; the bar is `/implement` §Behavior Check — exercise it, do
      not just compile it.
- [ ] **Parity with the exemplar**: run the same command against the exemplar and against the new
      artifact and compare the outputs shape for shape. State the one difference you expect, and
      confirm nothing else differs. "It imports" is not the bar; "it does what its neighbour
      does" is.

## Output

Keep it short: what was created; each registration point with its proving command **and the line
of output that proves it**; the parity comparison; then a commit block as text — explicit paths,
never run (`rules/_generic/core.md`).

## Hard rules

- **Exemplar before structure.** A structure invented from this checklist is a finding against
  this skill.
- **An unproven registration counts as not done.** No command, no claim.
- **Never self-enable on a live or production path.** Scaffold it disabled and ask.
- **No plan is written here.** If the work turns out to need one, stop and route to `/prepare`.
