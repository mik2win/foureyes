---
paths:
  - "app/views/**/*"
  - "app/components/**/*.rb"
  - "app/helpers/**/*.rb"
  - "app/javascript/**/*.js"
---

# UI/UX Conventions

Examples use **Slim** syntax.

> Worked examples live in the `ui-ux-reference` skill (`references/ui-ux.md`).

## Partial vs ViewComponent vs Helper — Decision Guide

| Use | When |
|-----|------|
| **Helper** | Simple value formatting, one-liner conditional logic (e.g. `format_amount`, `status_badge_class`). No HTML. |
| **Partial** | Reusable template with minimal or no logic. Used in one or a few contexts. Simple HTML structure. |
| **ViewComponent** | Complex, reusable UI with logic, variants, slots, or an attached Stimulus controller. |

**Default to partials.** Use ViewComponent when a partial becomes too smart or is reused in many contexts.

## Partials

- **Naming:** underscore prefix, snake_case. Place in controller directory or `shared/` for cross-context use.
- **Paths:** `app/views/shared/_flash_messages.html.slim`, `app/views/records/_row.html.slim`
- Keep logic out of partials. If you need conditionals beyond simple `if/unless`, move logic to a helper or ViewComponent.
- If the same structure appears in 2+ places — extract it into a partial.

## ViewComponent

Use when the UI has:
- Complex conditional rendering
- Multiple variants or sizes
- Slots (header, body, footer)
- An attached Stimulus controller
- Need to be reused across very different contexts

## Helpers

- Use for formatting and CSS class generation. Keep helpers focused; no business logic or DB queries.
- Never put business logic in helpers. If you need to query the database or orchestrate objects — that belongs in a model or service.

## Hotwire — Turbo

- Use Turbo for dynamic updates; avoid full-page reloads for small changes.
- **Turbo Frames** — scope partial updates.
- **Turbo Streams** — targeted DOM updates from the controller.
- **Prefer native HTML** where possible (e.g. `dialog` for confirmations, `details`/`summary` for accordions).

## Stimulus

Use Stimulus for behavior that **really needs JS** and cannot be done with native HTML + Turbo.

- **Declarative:** HTML declares the behavior via `data-controller`, `data-*-target`, `data-action`; Stimulus reacts.
- Keep controllers small: one responsibility, limited targets (~7 max).
- No domain logic or DB in Stimulus; pass data from Rails via `data-*-value`.

## TailwindCSS

- Use utility classes consistently; avoid inline `style` attributes.
- For repeated class combinations, extract to a helper method or ViewComponent.

## Flash Messages

Render flash in the layout via a shared partial; use a helper for CSS by type.

## Accessibility

- Form inputs must have associated `label` elements
- Use `aria-label` where a visible label is not possible
- Buttons must have descriptive text or `aria-label`
- Tables: use `th scope="col"` for headers
- Prefer semantic HTML: `main`, `nav`, `section`, `article`, `header`, `footer`

## Server-Side Formatting

Format numbers, dates, and currency on the server. Pass formatted strings to Stimulus only when needed for display; avoid raw values and formatting in JS.
