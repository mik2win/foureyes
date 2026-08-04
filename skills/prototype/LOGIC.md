# Prototype — Logic mode

Use this mode when the open question is about **how the thing should behave**: the state model, the
business rules, the data shape, an algorithm, or the branches of a flow. You answer it by building
a small **runnable** program the user can drive and watch.

## The goal

Make the behaviour *real* and *interactive*. A description of a state machine invites hand-waving; a
runnable one the user steps through exposes the cases nobody thought about. The prototype's job is
to surface those — wrong transitions, missing states, an awkward data shape — while they're cheap.

## How to build it

- **Smallest runnable thing.** A single script or a terminal app in the project's language. No UI,
  no persistence beyond in-memory, no framework ceremony.
- **Real inputs, fake everything else.** Use the project's real key libraries where they shape the
  answer; hardcode or stub data, services, auth, and I/O that don't.
- **Make it interactive.** Let the user drive it — a REPL-ish loop, a few preset scenarios to run,
  or command-line args that flip the interesting variables. The user *operating* it is where the
  learning comes from.
- **Use the domain vocabulary** from `CONTEXT.md` for states, entities, and commands, so the
  prototype and the eventual real model speak the same language.

## What to probe

- **State & transitions** — every state, who/what triggers each move, the guards. Try the
  transition that *shouldn't* be allowed and see what happens.
- **Edge cases** — empty, boundary, concurrent, partial-failure. These are exactly what a
  paper design glosses over.
- **Data shape** — does the chosen structure make the common operations easy and the rare ones
  possible? Feel the awkwardness by writing the operations against it.

## Output of this mode

The **decision**: the state/data model that survived contact with real scenarios, the rules that
turned out to matter, and the cases the user hadn't considered. Hand new terms/decisions to
`/domain-model`. Then discard the code — the real model is built fresh in the pipeline.
