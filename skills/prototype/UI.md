# Prototype — UI mode

> **Needs a UI surface.** UI mode assumes the project has something servable/renderable (per
> `PROJECT.md` → Stack/Architecture). If it's headless — a CLI, a library, a backend with no
> UI — point the variations at whatever output layer it *does* have (its console / report /
> message rendering), or treat the question as **Logic** ([LOGIC.md](LOGIC.md)) — don't invent
> a route the project can't serve.

Use this mode when the open question is about **how it should look or feel**: layout, interaction,
visual direction, or which of several designs to pursue. You answer it by building **several
genuinely different variations** the user can flip between from one place.

## The goal

Comparison, not a single mock. One mock invites "yeah, looks fine" and locks in the first idea. Two
to four *radically different* variations — different layouts, different interaction models, not
recolours of the same thing — force a real choice and surface preferences the user couldn't state
in the abstract.

## How to build it

- **One throwaway route, many variations.** Add a single clearly-named throwaway route/page the
  project can serve (per `PROJECT.md` → Architecture routing), with a toggle (tabs, a query param,
  a switcher) to flip between variations A/B/C/D. The user compares them in seconds.
- **Use the real UI stack.** Build with the project's actual UI framework/components (`PROJECT.md`
  → Stack) so the look is honest and the chosen direction transfers. Fake the data behind it.
- **Make them genuinely different.** Vary the structure: e.g. a dense table vs a card grid vs a
  guided wizard; sidebar vs top-nav; one-page vs stepped. If two variations differ only by colour,
  collapse them — that's one variation, not two.
- **Static/hardcoded data.** Wire fake data so the variations render; no real backend, no
  persistence, no auth. The question is the *interface*, not the plumbing.
- **Use domain vocabulary** from `CONTEXT.md` for labels and entities, so the screens read true.

## What to probe (with `/grill`)

- Which **layout** lets the user do the main task fastest?
- Which **interaction model** feels right — and where does each one get awkward?
- What's **missing** from the favourite that another variation got right? (The best answer is often
  a graft: variation B's layout with variation C's flow.)

## Output of this mode

The **decision**: which variation (or hybrid) wins and *why*, in the user's own reactions, plus the
interaction constraints discovered. Capture any naming/term decisions via `/domain-model`. Then
**delete the throwaway route file and its registration** (the router entry / nav link / menu item)
plus the variation components, so nothing dangles — the real screens are built fresh through the
pipeline.
