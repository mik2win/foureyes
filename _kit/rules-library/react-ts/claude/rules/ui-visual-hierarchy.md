---
paths:
  - "**/*.tsx"
  - "**/*.css"
---

# UI Visual Hierarchy and Accessibility

Checks you can run against markup and class names, without rendering. See `react-conventions.md`
(component shape), `fsd.md` (layers).

## Scales, not one-off values

- Declare spacing/sizing, type, weight, text-colour levels, shades, elevation and radius once as custom properties — on Tailwind v4 that is the `@theme` block. v4 accepts any spacing multiple, so the scale is held by this rule, not by the toolchain.
- Reach for the token the **second** time you hand-tune a value of that kind. A second arbitrary value (`mt-[14px]` beside an existing `mt-4`) is the trigger — a countable one, not a matter of taste.

## Hierarchy

- **`Label: value` flattens hierarchy.** Where format or context already identifies the value, drop the label (`12 left in stock`), fold it into the sentence, or demote it to a lighter weight or colour level. Emphasise the label itself only when the user scans for it.
- **Spacing marks the group.** Wherever grouping is carried by spacing alone, the gap around a group must exceed the gap inside it — equal margins above and below a field label put users in the wrong input.
- **Percentage width only for what must scale with its container.** Prefer a container query (`@container` with `@md:` variants) for components and a fixed width for the rest; fluid fractions produce the absurd case of a component wider on a medium screen than on a large one.
- **One column per sortable field.** Merge the rest into a single cell with its own internal hierarchy; right-align numerics.

## Accessibility

- Every image carries `alt` (`alt=""` when purely decorative); every input has a `<label>` or an `aria-label`; an icon-only button carries an accessible name.
- Heading levels descend without skipping — one `h1` per page, no jump from `h2` to `h4`.
- Anything actionable is a real `<button>` / `<a>`, not a `div` with `onClick`, and keeps a visible focus style. Keyboard reach is not optional.
- Text contrast ≥ 4.5:1 (≥ 3:1 only at 24px, or ~18.7px bold). Buy it by flipping polarity or rotating hue 20–30°, never by darkening a non-focal panel and never with an opacity modifier on white (`text-white/60`).
- Link and control text leads with the word that distinguishes it — `Export CSV`, not `Click here to export`.
