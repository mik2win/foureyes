# Ruby Project — Claude Instructions

## Behaviour Rules

### Think, Then Propose
Before implementing, briefly describe what you're going to do and why. One short paragraph is enough. Start coding only after.

### Simplicity First
Small team (1-3 developers). Always choose the simpler approach. Readable code beats clever code. YAGNI — don't build for hypothetical futures.

### Tests
**Do NOT write tests unless explicitly asked.** Never include specs in feature plans or generated code. Never suggest writing tests unsolicited.

---

## Architecture — Layer Responsibilities

| Layer | Responsibility |
|---|---|
| **Model** | Data logic: validations, associations, scopes, calculations belonging to the entity. Not a god object. |
| **Concern** | Reusable single-model behavior shared by 2+ models. Cohesive trait, <50 lines. |
| **Service** | Complex/cross-model logic, orchestration, external calls. Named as nouns (`OrderFulfiller`). |
| **Controller** | **Thin:** auth, params, call models/services, respond. No business logic — only coordination. |
| **Job** | Async work. Delegates to services. Must be idempotent. |
| **Helper** | View formatting only. No HTML, no DB queries. |
| **View** | Display only. |

---

## Critical Conventions

- **Naming:** `snake_case` methods/variables, `CamelCase` classes, `SCREAMING_SNAKE_CASE` constants
- **Strings:** Single quotes unless interpolation. `frozen_string_literal: true` in every file.
- **Time:** `Time.current` / `Date.current` (not `Time.now` / `Date.today`)
- **Models:** 11-step structure order, enums with explicit integers, `normalizes` over `before_validation`
- **OOP:** SRP, Dependency Injection, Tell Don't Ask, Law of Demeter, Composition over Inheritance
- **Modern Ruby:** `Data.define` for value objects, pattern matching, `filter_map`, `it` block parameter
- **Services:** Named as nouns, single `#call` or multi-method facade
- **Rails 8 Solid Stack:** Solid Queue (jobs), Solid Cache (caching), Solid Cable (WebSockets)

---

## Rules (auto-loaded by file path)

Rules are loaded automatically when you work with matching files — no need to read them manually.

| When you edit... | Rules loaded |
|---|---|
| Any `.rb` file | ruby-style, ruby-oop |
| `app/models/` | rails-models, rails-activerecord-queries |
| `app/controllers/` | rails-controllers-routing, rails-security |
| `app/controllers/` (if using Inertia, not Hotwire) | rails-inertia |
| `app/models/`, `app/controllers/`, `app/services/` (multi-tenant apps) | rails-multitenancy |
| `app/services/`, `app/forms/`, `app/policies/` | rails-business-logic |
| `app/jobs/`, `app/mailers/` | rails-background-jobs |
| `app/views/`, `app/components/` | rails-caching-storage |
| `db/migrate/` | rails-database |
| `spec/` | rspec-testing |
| Any `.rb` file (Rails app / logging service) | ruby-observability |
| `*agent*`, `*llm*`, `config/prompts/` | llm-agent-practices |

For project context, read `.claude/rules/project-overview.md` first.

---

## Available Skills

| Skill | Description |
|---|---|
| `/code-review` | Structured code review against project checklist |
| `/write-tests` | Generate RSpec tests for a class |
| `/create-service` | Scaffold service/form/policy/query object |
| `/create-migration` | Migration with zero-downtime patterns |
| `/security-audit` | OWASP Top 10 audit for Rails |
| `/performance-audit` | N+1, missing indexes, caching opportunities |
| `/pg-checklist` | PostgreSQL production checklist |
| `/ruby-idioms` | On-demand stdlib/idiom reference (Enumerable, blocks, Set, ranges, freeze) |
| `/ruby-conventions-reference` | On-demand worked examples for ruby-style + ruby-oop |
| `/rails-reference` | On-demand worked examples for the rails-* layer rules (models, queries, db, controllers, services, jobs, caching, security) |
| `/rspec-reference` | On-demand worked RSpec examples |
| `/llm-agent-reference` | On-demand worked examples for LLM/agent code |

> Each `rails-*`, `ruby-style`, `ruby-oop`, `rspec-testing`, `llm-agent-practices` rule is the
> lean always-apply version; its GOOD/BAD code examples live in the matching `*-reference`
> skill above (loaded on demand).

---

## Prohibited Actions

- Do NOT run tests or linters automatically — the developer runs them manually
- Do NOT commit to git unless explicitly requested
- Do NOT modify project rules without asking first
- Do NOT create documentation files unless explicitly asked
