---
description: Stack-agnostic domain events — immutable past-tense facts, self-contained payloads, subscriber isolation, emit-after-persist, idempotent handlers, versioning. Loaded on file read (code work).
paths:
  - "**/*"
---

# Domain events (generic)

For code where modules communicate by publishing facts rather than calling each other directly.
The stack pack names the concrete transport (in-process callback, bus, queue). If there's one
known caller, skip events and call it directly — see `rules/_generic/code-quality.md` §Pattern
choice.

## Events are immutable past-tense facts

- Name events for what **already happened**, past tense: `OrderPlaced`, `PaymentCaptured`,
  `UserRegistered` — not `PlaceOrder` (that's a command) or `OrderPlacement`.
- Events are **immutable** once created (frozen/readonly value objects). A subscriber must never
  be able to mutate an event and corrupt what the next subscriber sees.
- No side-effecting methods on an event — it's a pure data carrier.

## Self-contained payload

- Carry the facts the event asserts, plus identifiers; reference large or mutable data by id.
  A field added for one consumer's convenience inverts the dependency — the event's shape now
  changes when that consumer's needs do — so name the consumer and accept versioning for them.
- Pick state vs a bare notification by the consumer's consistency need: carry state when it can
  live with stale data; carry ids and let it query back when it must read the producer's last
  write, or when the data is sensitive.

```
# DO — the facts it asserts + ids           # DON'T — a field for one consumer
OrderPlaced(order_id, customer_id,           OrderPlaced(order_id, ..., invoice_pdf_url)
            total, currency, placed_at)      # billing asked; now every change touches it
```

## Emit after persist

- Publish an event **after** the state it describes is durably saved. Emitting first risks
  notifying subscribers about a change a crash then loses.
- `save(x)` then `publish(E)` is a **dual write**: a crash between them loses E with no trace.
  In-process subscribers are fine; once the event leaves the process (broker, queue, webhook),
  write it to an outbox row **inside** the transaction and let a relay deliver it. The outbox
  must share the state's store; when the queue lives in another store, enqueue after commit and
  name the window in which a crash loses the event.

## Subscriber isolation

- One subscriber failing must not crash the emitter or the other subscribers. Wrap each
  subscriber, log its failure, continue. Compose multiple subscribers at the composition root,
  not by chaining one inside another (that couples unrelated concerns).
- Emitting a fact must not depend on any subscriber succeeding — decouple the two.

## Idempotent handlers

- Delivery may repeat (retries, at-least-once transports). Handlers must be **idempotent**:
  processing the same event twice = same end state. Track a processed-id / dedup key, or make the
  effect naturally repeatable (upsert, not blind increment). See `rules/_generic/resilience.md`.

## Versioning

- Event shapes evolve. Add fields as **optional** with sane defaults; don't repurpose or remove a
  field's meaning. For a breaking change, introduce a new version/type rather than silently
  altering the old one — old and in-flight events must still deserialize.
