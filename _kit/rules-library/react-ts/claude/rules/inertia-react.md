---
paths:
  - "**/pages/**/*.tsx"
  - "app/frontend/pages/**/*.tsx"
---

# Inertia.js (React side)

Conventions for Inertia page components (**Inertia v2/v3**). See `react-conventions.md` (typing, DI),
`fsd.md` (where pages sit), `react-testing.md`.

## Page metadata

- Set title / breadcrumbs / page actions through the **page-meta hook** (`usePageMeta`), never a
  raw `<Head>`. The hook drives the shared layout store, so layout stays consistent across pages.

```typescript
usePageMeta({
  title: 'Items',
  breadcrumbs: useBreadcrumbs([{ label: 'Items', href: itemsPath() }, { label: 'Settings' }]),
  actions: <Button asChild><Link href={newItemPath()}>Create</Link></Button>,
  secondarySidebar: <ItemSidebar />,   // optional; resolves its own context via hooks
})
```

## Props envelope: `{ data, meta, errors }`

- Every page receives the same three-key shape:
  - **`data`** — screen content (server presenter output).
  - **`meta`** — page/list machinery: `pagy`, `filters`, `current_tab`. Keep navigation state out of `data`.
  - **`errors`** — framework-owned validation messages; always present. **Never declare `errors`
    in your own props type** — read it via the form-errors hook.
- Type the payload with a co-located `*.props.ts` whose keys mirror the server payload exactly,
  and read it through the typed `usePageProps<T>()` overload (renames then surface as TS errors, not runtime `undefined`).
- Page props are **readonly** — never mutate.

```typescript
// index.props.ts
export interface ItemsIndexProps { data: { items: ItemRow[] }; meta: { pagy: PagyMeta } }
// index.tsx
const { data, meta } = usePageProps<ItemsIndexProps>()
```

## Validation errors

- Errors come from the redirect, not props. Read with `useFormErrors()`, merge with the Form
  slot's `errors` (redirect errors win), and render through `getFieldError` — never a raw error object.

```typescript
const formErrors = useFormErrors()
<Form action={url} method="post">
  {({ errors: slot, processing }) => {
    const errors = formErrors ?? slot
    return getFieldError(errors, 'name') ? <p className="...">{getFieldError(errors, 'name')}</p> : null
  }}
</Form>
```

## Permissions — never page-level props

- Do **not** pass `can*` / permission props from a page. Components inject access via
  `usePermissions()` / `useUser()` themselves (see `react-conventions.md` DI). Per-row flags from the server are read off the row.

## Partial & grouped reloads

- Use `only` to refetch a subset (pagination, filters) instead of the whole page.
- Props that belong to one UI section share a server-side `group:` so a single reload fetches them together.

```typescript
<Pagination pagy={meta.pagy} only={['data', 'meta']} />
```

## Deferred props

- Server may send expensive props as **deferred** (fetched after first paint). Never assume a
  deferred prop is present on first render.
- Prefer the **`<Deferred>`** component with a `fallback` over hand-rolled loading flags; group
  related deferred props so they load in one request. (v3: `fallback` shows only on first load,
  not during partial reloads.)

```tsx
<Deferred data="stats" fallback={<Skeleton />}>
  <Stats stats={data.stats} />
</Deferred>
```

## Inertia v2+ features

Reach for these where they replace manual machinery — don't add them preemptively:

- **Prefetching:** `<Link prefetch>` (hover/mount/click) and `router` prefetch for instant
  navigation; cache with `cacheFor`. Use on high-traffic links, not everything.
- **Polling:** `usePoll(interval, options)` for live data instead of a hand-written `setInterval`;
  in background tabs it's throttled ~90% by default (`keepAlive: true` disables that).
- **Lazy-on-scroll:** **`<WhenVisible>`** to fetch a section only when it scrolls into view.
- **Merge / infinite scroll:** server-side `merge`/`deepMerge` props append instead of replacing —
  the basis for "load more" / infinite lists; reset on filter change.
- **History encryption:** enable `encryptHistory` / `clearHistory` for pages with sensitive data so
  back-button navigation doesn't leak it from history state.
- **Forms:** `useForm` (and the `<Form>` component) own submission/processing/errors state — don't
  duplicate it in local `useState`.

## URL-driven tabs

- For tabbed show-pages driven by the URL, use the tab-page wrapper + a `useTab`-style hook:
  triggers render as `<Link>`, the active tab comes from `meta.current_tab`, and each panel
  registers via `useTab` and returns `null` when not active. Mount all panels (`forceMount`) so registration runs. Don't hand-roll Radix `Tabs` with local state for URL tabs.
