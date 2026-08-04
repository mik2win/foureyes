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
- Report progress via injected logger/callback, not by printing to the delivery channel.

```
# DON'T — service reaches for the delivery framework
def run_report(cfg):
    import <web-framework>          # service must not know the transport
    printer.print("starting...")   # presentation inside logic = untestable
```

## Share setup, don't duplicate it

- When several entry points need the same construction (config, dependency wiring, resolving a
  registry), extract one shared helper and reuse it — don't copy the setup block into each.

## Command/Query separation

- A **command** changes state and returns little; a **query** reads state and causes no
  side effects. Keep them separate methods/functions — don't return data from a mutator or mutate
  inside a reader (atomic get-and-set is the deliberate exception).
- Split read and write paths at the service layer so each can be reasoned about and tested alone.
