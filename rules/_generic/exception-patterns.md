---
description: Stack-agnostic error-handling discipline — narrow scope, specific errors, no swallowing, cancellation safety. Loaded on file read (code work).
paths:
  - "**/*"
---

# Exception / error handling (generic)

## Scope

- Wrap the smallest block that can fail, not a whole function body.
- Catch the most specific error type available; never a bare/catch-all that hides
  programmer errors.
- A new error type is earned by a caller that handles it differently; otherwise reuse the
  nearest existing one.

## Never swallow

- No empty catch blocks. If you catch, you handle: recover, translate, or log + rethrow.
- Preserve the cause when wrapping — use the language's error-chaining mechanism, never
  lose the original stack.
- Error messages state what failed, the relevant inputs, and what would have been valid
  (`unknown kind 'x', expected one of [...]`) — debuggable without a stack trace.
- Capture diagnostic context at the failure site (the values that explain it) before
  raising — the catcher won't have them. The owning boundary still logs the failure once.

## Not for flow control

- An expected outcome is not exceptional: a lookup that can legitimately find nothing
  returns an empty/optional value, it doesn't raise. Reserve errors for contract
  violations and failures.
- That optional is safe only when the caller must read it: a method called for its
  side effect discards it, so the failure goes silent — raise instead. "Nothing
  found" is safe only when no legitimate result is falsey (0, "", [] are).
- Inside a framework callback that cannot propagate exceptions, honor the framework's
  error contract (its sentinel / error return) instead of raising through it.

## Cancellation & async (where the language has it)

- Cancellation signals must propagate, never be caught-and-ignored: a catch-all that
  swallows the runtime's cancellation error makes the task un-cancellable. Re-raise it;
  respect abort/cancellation tokens.
- Don't catch-all around `await` points and continue as if nothing happened.
- Give every asynchronous failure a destination: retryable → a retry queue; rejected by
  policy → persisted as an error at once; past the attempt cap → a dead-letter queue a
  human reads. A detached task or a message with no owner drops its failure silently.

## Warnings & deprecations

- Investigate before suppressing: a warning signals deprecation, future removal, or a
  real issue. Test whether the feature actually works; if broken, replace it; if an
  alternative exists, evaluate it; suppress only what works and has no alternative —
  with a comment saying why.
- Never blanket-ignore all warnings, and never suppress a warning on a feature that is
  actually broken. Scope any suppression to the narrowest block the language allows.

## Boundaries vs core

- Translate external/library errors into domain errors at the boundary; the core
  should not leak third-party exception types upward.
- Fail-open vs fail-closed is a deliberate decision — document which and why at the
  boundary (a security check fails closed; an optional enrichment may fail open).
