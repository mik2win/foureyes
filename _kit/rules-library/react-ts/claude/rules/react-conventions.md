---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

# React + TypeScript Conventions

Conventions only — assumes fluency with React, TS, and hooks. See `fsd.md` (layers),
`inertia-react.md` (page/props), `react-testing.md` (tests).

## Typing

- Strict mode. **No `any`** (no implicit, no explicit). Reach for `unknown` + narrowing, generics, or a precise type.
- Props: explicit `interface Props` (or named `XxxProps`). Don't infer from usage.
- Model mutually-exclusive states as **discriminated unions**, not optional-flag soups.
- No non-null `!` assertions to silence the compiler — narrow with an early return instead.

```typescript
// Discriminated union over a bag of optionals
type Async<T> =
  | { status: 'loading' }
  | { status: 'error'; error: string }
  | { status: 'ready'; data: T }

// ❌ { loading?: boolean; error?: string; data?: T } — illegal states representable
```

## Components

- File naming: **kebab-case** (`status-badge.tsx`, `use-mobile.ts`). Only `index.ts` is exempt.
- One public component per file; each slice re-exports through its `index.ts` (see `fsd.md`).
- Page components: **default export**. Reusable components: **named export**.
- Order inside a component: **all hooks unconditionally → early returns → derived state → JSX.**
  Never call a hook after a conditional `return`.

```typescript
export function SettingsView() {
  const tenant = useTenant()          // 1. hooks first, unconditional
  const { can } = usePermissions()

  if (!tenant) return null            // 2. early returns

  const editable = can('settings:edit') // 3. derive
  return /* ... */
}
```

## Data injection: hooks, not prop-drilling

- Cross-cutting context (current user, account, role, permissions, locale) is read **inside the
  component via a `useX()` hook** — never threaded through intermediate props.
- Don't pass `can*` / permission booleans down from a page. Components resolve their own access.
- When a row from the server already carries per-row flags (`row.canEdit`), read them off the entity; don't recompute or re-pass.

```typescript
// ✅ component owns its context
function Toolbar() {
  const { can } = usePermissions()
  return can('items:create') ? <CreateButton /> : null
}
// ❌ <Toolbar canCreate={can('items:create')} />
```

## State

- Keep global/shared state in a **shared lib** (e.g. `shared/lib`), not in widgets or features.
- Reusable UI primitives live in **shared ui** — check it before adding any new component or library.
- Local UI state stays local. Don't lift state higher than the lowest common owner.

## Forms

- Prefer **native / declarative forms** (uncontrolled fields, `defaultValue`, FormData on submit).
  Reach for manually-controlled `useState` per field only when you need programmatic control or a custom transform.
- Show server validation through a helper — **never** render a raw error object.

```typescript
{getFieldError(errors, 'name') && (
  <p className="text-sm text-destructive">{getFieldError(errors, 'name')}</p>
)}
```

See `inertia-react.md` for where `errors` comes from and the form envelope.

## Misc

- **No `console.log`** in committed code (lint-enforced). Use a logger util if you need diagnostics.
- Import order, blank-line-separated, alphabetical within group:
  external → feature aliases → entity aliases → shared aliases → relative.
- Format/derive display strings via entity-layer formatters; don't scatter ad-hoc formatting in components.
