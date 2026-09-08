# React + TypeScript Project — Claude Instructions

## Behaviour Rules

### Think, Then Propose
Before implementing, briefly describe what you're going to do and why. One short paragraph. Start coding only after.

### Simplicity First
Small team. Choose the simpler approach. Readable beats clever. YAGNI.

### Tests
**Do NOT write tests unless explicitly asked.** Never include tests in feature plans or generated code unsolicited.

---

## Architecture — Feature-Sliced Design

Layers, top to bottom; imports go **downward only**:

| Layer | Responsibility |
|---|---|
| **app** | Entry, providers, routing, global config. |
| **pages** | Route targets; compose widgets/features. |
| **widgets** | Composite UI blocks (layouts, panels). |
| **features** | User interactions (forms, actions, local state). |
| **entities** | Domain types, formatters, hooks. Leaf — inject features via props. |
| **shared** | Reusable ui/, lib/, hooks/, api/. Leaf. |

No upward imports. Public API only via each slice's `index.ts`. See `fsd.md`.

---

## Critical Conventions

- **Types:** strict; no `any`; explicit props types / discriminated unions.
- **Files:** kebab-case; one public API per slice via `index.ts`.
- **Data:** inject via hooks (`useX`), not deep prop-drilling.
- **State:** global state in `shared/lib`; reusable UI in `shared/ui`.
- **Forms:** prefer native/declarative forms; manual state only when programmatic control is needed.
- **Validation:** server-side; display via a field-error helper (`getFieldError`).
- **No** `console.log` in committed code.
- **Inertia** (if used): page-meta hook over raw `<Head>`; never page-level permission props — inject via hooks.

---

## Rules (auto-loaded by file path)

| When you edit... | Rules loaded |
|---|---|
| Any `.ts` / `.tsx` | react-conventions |
| `src/**`, `app/frontend/**` | fsd |
| `pages/**` | inertia-react (if using Inertia) |
| `*.test.*`, `*.spec.*`, `e2e/**` | react-testing |
| Any `.tsx` / `.css` | ui-visual-hierarchy |

For project context, read `.claude/rules/project-overview.md` first (if present).

---

## Prohibited Actions

- Do NOT run tests, linters, or the dev server automatically — the developer runs them.
- Do NOT commit to git unless explicitly requested.
- Do NOT modify project rules without asking first.
- Do NOT create documentation files unless explicitly asked.
