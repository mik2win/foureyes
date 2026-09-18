---
description: Stack-agnostic service layer — thin framework-free entry-point shells that delegate to service functions (load→compute→persist), command/query separation. Loaded on file read (code work).
paths:
  - "**/*"
---

# Service layer (generic)

Separate *orchestration* (wiring, I/O sequencing) from *computation* (business logic), and keep
the delivery framework out of both. The stack pack names the concrete entry-point type (CLI
command, HTTP handler, job, message consumer).

## Entry point = thin shell

- Each entry point is a **use case shell**: build config from inputs → delegate to a service
  function → format/return the result. No business logic in the shell.
- The shell is the only layer that knows the delivery framework (web framework, CLI library,
  queue client). What it delegates to must not.

```
# DO — thin entry point delegates          # DON'T — god handler
def handle(req):                            def handle(req):
    cfg = build_config(req)                     # 200 lines: parse + load +
    result = run_report(cfg)                     #   compute + format + persist
    return present(result)                       #   all inline, framework-coupled
```

## Service functions are framework-free

- Service functions accept domain types and return domain types. **No** framework imports inside
  (no request/response objects, no CLI printer, no template/rich output) — that makes them
  untestable and unreusable.
- A service function orchestrates: `load → compute → persist`. It sequences steps and calls the
  pure domain layer; it holds no business rules of its own (those live in the pure core — see
  `rules/_generic/code-quality.md` §Pure core, thin shells).
- **One use case, one consistency boundary, one transaction.** Writing two boundaries
  atomically means one is drawn wrong — but a module is not a boundary by itself: a composer
  layer the project declares may write several modules in one transaction on one store. Across
  stores nothing is atomic: sequence the writes and compensate the earlier one, or join two
  handlers by an event (`rules/_generic/domain-events.md`); state the eventual consistency.
- Two-way object references across such a boundary are the same defect in the object graph:
  replace one direction with an identifier the other side resolves when it needs it.
- Report progress via injected logger/callback, not by printing to the delivery channel.

## Share setup, don't duplicate it

- When several entry points need the same construction (config, dependency wiring, resolving a
  registry), extract one shared helper and reuse it — don't copy the setup block into each.

## Command/Query separation

- A **command** changes state; a **query** has no *observable* side effect — caching and
  lazy init pass that test, a write a later read sees does not. Keep them separate: no
  data from a mutator, no mutation in a reader. Excepted: get-and-set, and a command that
  returns its own outcome or the id it wrote — that is a receipt, not a query.
- Split read and write paths at the service layer so each can be reasoned about and tested alone.
