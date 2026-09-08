**Gate:** `/test` Phase 1 loads this when the target has no tests AND nothing outside the code — no
spec, ticket, docstring or sibling test — states what it should do. Anything that does: normal flow.

# Legacy mode — pin the behaviour, then design

## Characterize before you design

- Trigger: filling the `Expected` cell of the Phase 3 table would mean simulating the code in your
  head → you are not writing an expectation. Put the unit in a harness, assert a value you know is
  wrong, let the failure report what the code returns, and pin it — the row records `Observed`.
- Moving an assertion toward the code is legitimate **only here**, where nothing outside the code
  states the expectation; where a spec, ticket or stated expectation exists it stays CRITICAL.
- Behaviour you believe is wrong still goes in — pinned, marked suspicious, reported, never
  silently corrected. Already deployed: assume someone depends on it and ask before changing it.

## Where the test goes

- **One change point** → trace the effect forward and write at the nearest place it is observable;
  every extra hop is one more inference you must get right. Forced to write far from it: break the
  code at the change point on purpose and confirm the test goes red before trusting it.
- **Several collaborating units AND none with usable coverage** → do not break dependencies in each.
  Find the narrowing all the effects funnel through and write temporary higher-level tests there;
  they cover arbitrary restructuring underneath. Both triggers, or the move is unavailable, and it
  is a first step toward unit tests, never a substitute. Mark each as scaffolding with its removal
  condition, list it under `Remaining Gaps`, delete only once the replacing unit tests are green;
  no narrowing exists → the change is scoped too wide, split it.
