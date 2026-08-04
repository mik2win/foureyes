---
paths:
  - "src/**/*.ts"
  - "src/**/*.tsx"
  - "app/frontend/**/*.ts"
  - "app/frontend/**/*.tsx"
---

# Feature-Sliced Design (FSD)

The architecture's whole value is the **layer order + import direction**. Internalize the table.
See `react-conventions.md` (component rules), `inertia-react.md` (pages).

## Layers

```
app → pages → widgets → features → entities → shared
```

| Layer        | Responsibility (one line)                                              |
|--------------|-----------------------------------------------------------------------|
| `app`        | App wiring: providers, router, global config. Configures everything.   |
| `pages`      | Route screens. Composes widgets/features/entities for one URL.         |
| `widgets`    | Multi-feature compositions only (layout, sidebar, landing).            |
| `features`   | One user action / interaction on one resource (a form, a filter, an action menu). |
| `entities`   | A domain noun: its types, formatters, and presentational UI. **Leaf.** |
| `shared`     | Framework-agnostic foundation: ui primitives, lib, hooks, config. **Leaf.** |

## Import direction — strict, downward-only

- A layer imports **only from layers below it**. Never upward, never sideways within the same layer.
- `shared` imports nothing from other layers. `entities` import only `shared`.
- **Entities are leaf**: they must not import features/widgets. When an entity's UI needs a
  feature, **inject it as a prop** (component / callback / `ReactNode`), supplied by the page.

```typescript
// entities/user/ui/user-view.tsx
interface UserViewProps {
  user: User
  onResetPassword?: () => void   // feature behavior injected from above
  resetDialog?: ReactNode        // feature component injected from above
}
// ❌ import { ResetPasswordDialog } from '@features/...'  // upward import, banned
```

## Placement rules (the common mistakes)

| Thing                                   | Goes in                          | Not in        |
|-----------------------------------------|----------------------------------|---------------|
| Global state (layout, page-props store) | `shared/lib`                     | `widgets`     |
| Reusable UI primitive                   | `shared/ui`                      | `widgets`     |
| Entity-specific formatter               | `entities/<name>/lib`            | `shared/lib`  |
| Single-resource filter                  | `features/`                      | `widgets/`    |
| Types                                   | `<slice>/model/types.ts`         | `ui/`         |
| Hooks                                   | `<slice>/model/use-*.ts`         | a `hooks/` dir |

## Public API

- Every slice exposes a public API via `index.ts`. **Import from the slice root, never a deep path.**
- Within-slice deep imports are fine (`entities/user/ui` → `entities/user/model`).

```typescript
// ✅ import { User } from '@entities/user'
// ❌ import { User } from '@entities/user/model/types'
```

## Naming & structure

- All files **kebab-case**; `index.ts` is the only exception.

```
<slice>/
├── index.ts     # public API
├── ui/          # components
├── model/       # types.ts, store, use-*.ts hooks
├── lib/         # slice-local utilities
└── config/      # constants
```
