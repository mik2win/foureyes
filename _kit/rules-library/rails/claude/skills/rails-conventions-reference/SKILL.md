---
name: rails-conventions-reference
description: >-
  Worked GOOD/BAD examples for this project's Ruby/Rails conventions plus the optional
  architectural patterns — value objects, query objects, form objects, custom validators,
  and focused concerns.
  CONSULT when you need an idiomatic Rails example (model structure order, service
  patterns, thin controllers, routing, jobs, migrations) or when introducing a
  value/query/form object, a custom validator, or a concern. This is reference loaded on
  demand — the always-apply rules themselves live in the `ruby-rails-conventions` rule.
allowed-tools:
  - Read
  - Grep
  - Glob
---

# Ruby / Rails conventions — worked examples

Companion to the `ruby-rails-conventions` rule. The rule states the conventions as imperative
bullets; this skill holds the GOOD/BAD examples and the optional patterns. Read the reference
file (in this skill's folder) for the topic you need:

- **Naming & OOP** — naming, safe navigation, SRP, DI, Tell-Don't-Ask, Law of Demeter, duck
  typing, Open/Closed, name-by-noun → `references/naming-oop.md`
- **Model structure** — 11-step order, enums with explicit integers → `references/model-structure.md`
- **ActiveRecord** — N+1/includes, exists?, pluck, find_each, transactions, load_async,
  callbacks → `references/activerecord.md`
- **Services** — noun naming, single `#call` vs facade, dependency rule → `references/services.md`
- **Controllers & routing** — thin controllers, RESTful resources, shallow nesting →
  `references/controllers-routing.md`
- **Jobs & migrations** — idempotent jobs, reversible migrations, indexes, foreign keys →
  `references/jobs-migrations.md`
- **Optional: value / query / form objects** — when the simple approach is no longer enough →
  `references/value-query-form-objects.md`
- **Optional: custom validators & concerns** — reusable validation, focused traits →
  `references/concerns.md`
