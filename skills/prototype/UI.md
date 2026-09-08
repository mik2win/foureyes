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

## Check each variation before you show it

A defect you ship becomes the variable the user reacts to, so run these before Phase 3.

- **The hierarchy has to be true.** Compare what the eye groups — whitespace, background blocks,
  rule lines, column position — against what the markup nests: the markup alone always passes, and
  a heading that only looks like it spans a sibling block is a defect, not a preference.
- **Nothing lives only on hover.** Reveal-on-hover actions, tooltip-only explanations and
  colour-on-point are absent on touch, not degraded — build without them, and if a variation still
  needs one, name it under *Constraints discovered*. Same for state (selected, disabled, error):
  carry it on two dimensions, never colour alone.
- **Two absolutes**, both readable off the CSS: never small *and* low-contrast type, and no label
  inside its own field unless every escape condition holds at once (trivial form; returns when the
  field empties; never mistakable for, or submitted as, a value; still accessible) — else a label.

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
