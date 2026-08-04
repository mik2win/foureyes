---
description: Stack-agnostic external-API integration discipline — official docs first, exact schemas, no guessed field names, probe when docs are unclear. Loaded on file read (code work).
paths:
  - "**/*"
---

# External API integration (generic)

When integrating an external system (payment provider, exchange, messaging platform,
third-party service), verify the implementation against official documentation — never guess.

## Docs first

- Fetch the provider's official docs before writing integration code; record the doc URL and
  verification date next to the integration (`PROJECT.md` → Integrations, or a comment at the
  client boundary).
- Extract the exact message/response schema: field names, types, nesting. APIs often
  abbreviate keys (`s` = symbol, `T` = timestamp) — copy them from the docs, don't invent.
- Verify enum/semantic conventions per provider (side/direction/status vocabularies differ
  between services); document the mapping explicitly at the boundary.
- Check the provider's error codes and rate limits; map them into your retry policy
  (transient vs permanent — see `rules/_generic/exception-patterns.md`).

## Never

- Guess a field name (`data["price"]` when the docs say `p`) or assume a flat structure —
  payloads nest.
- Copy an integration from old code without re-verifying — APIs change.

## When docs are unclear

1. Write a minimal probe script and observe real responses (sandbox if the provider has one).
2. Log raw responses at debug level at the boundary.
3. Compare observed vs documented format; document any discrepancy you find.

## Why

A guessed schema fails silently: the code runs, the lookup misses, and you get empty results
instead of errors. Verifying up front is cheaper than that debugging session.

## Checklist (include in the plan)

- [ ] Official docs fetched and read; URL recorded
- [ ] Field names/types verified against the official schema
- [ ] Enum/direction semantics mapped and documented
- [ ] Error codes and rate limits understood
- [ ] Sandbox tested (if available)
