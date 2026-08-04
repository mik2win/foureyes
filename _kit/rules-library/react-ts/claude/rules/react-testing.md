---
paths:
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "**/*.spec.ts"
  - "**/*.spec.tsx"
  - "e2e/**"
---

# Frontend Testing (Vitest + Playwright)

Conventions only. Unit = Vitest + Testing Library. E2E = Playwright against the real app.
See `fsd.md` for slice layout, `inertia-react.md` for page/props.

## Unit (Vitest)

- **Test behavior, not implementation.** Assert what the user/consumer observes, not internal calls or state.
- **AAA**: arrange / act / assert. One logical assertion per test where practical.
- Descriptions in English, one behavior each ("returns true when the key matches exactly").
- **Mock only at boundaries** — Inertia (`usePage`, `router`), network, heavy deps. Don't mock the unit under test or its pure collaborators.
- Tests are isolated: no shared global state between tests; reset mocks per test.
- Use the same path aliases as the app; mirror FSD structure for unit-test files.
- Query by role/text/testid (`getByRole` first), not by DOM structure or class names.

```typescript
// boundary mock — Inertia, not the hook under test
vi.mock('@inertiajs/react', () => ({ usePage: () => ({ props: { auth: { permissions: ['x'] } } }) }))
```

## E2E (Playwright)

- **Auth via fixtures**, done once per run (login → save `storageState`). Don't sign in inside
  ordinary tests. For session/password/signout/permission-denied flows use a user **created in
  that test** via a fixture — never shared session state.
- **Stable selectors, not text.** Use `data-testid` for structure/actions; constants in one
  locators file. Don't tie navigation/action locators to button or link text (i18n changes break them).
- **Assert on i18n keys / data, not hardcoded UI strings.** Match text only for genuinely
  text-based assertions (validation messages, toasts) via shared pattern helpers — keep keys, not literals, as the source of truth.
- **Web-first assertions only**: `await expect(locator).toBeVisible()`. Never
  `expect(await locator.isVisible()).toBe(true)`, and never branch test flow on `isVisible()`/`count()`.
- **Never raise timeouts.** A timeout means "element not found" — fix the locator, the assertion,
  or add the missing `data-testid`. No per-test/per-action timeout overrides.
- Use `test.step()` for multi-step flows so traces stay readable. Assert by **permission**, not role name.

```typescript
test('shows details', async ({ authenticatedAdminPage: page }) => {
  await page.getByTestId(E2E.FIRST_ROW).click()
  await expect(page.getByTestId(E2E.MAIN)).toBeVisible()   // testid, web-first
})
```

## Structure

- Unit files mirror the source slice path (`shared/lib/foo.ts` → `tests/.../shared/lib/foo.test.ts`).
- E2E specs mirror routes: one file per page/flow; inside, ordered `describe` blocks —
  **smoke → validation → crud → permissions → actions**.
