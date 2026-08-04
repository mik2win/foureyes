# Ruby on Rails Project — Claude Instructions

## Behaviour Rules

### Think, Then Propose
Before implementing, briefly describe what you're going to do and why. One short paragraph is enough. Start coding only after.

### Simplicity First
Small team (1-3 developers). Always choose the simpler approach. Readable code beats clever code. YAGNI — don't build for hypothetical futures. Minimize dependencies — push Rails to its limits before adding gems.

### Tests
**Do NOT write tests unless explicitly asked.** Never include specs in feature plans. Never suggest writing tests unsolicited.

---

## Architecture

| Layer | Responsibility |
|---|---|
| **Model** | Data logic: validations, associations, scopes, domain calculations for a single entity |
| **Service** (`app/services/`) | Multi-model logic, complex operations. Named as nouns (`OrderFulfiller`). Two patterns: single `#call` or multi-method facade |
| **Controller** | Thin: params, auth, coordinate calls to models/services, respond. No business logic |
| **Helper** | View formatting only: `format_amount`, `status_badge_class`. No HTML, no DB queries |
| **View** | Display only — no data processing, no business logic |
| **Job** | Async work. Must be idempotent. Delegates logic to services |

---

## Critical Conventions

- **OOP:** SRP, DI, Tell Don't Ask, Law of Demeter, Composition over Inheritance, YAGNI
- **Time:** `Time.current` / `Date.current`
- **Models:** 11-step structure order, enums with explicit integers
- **ActiveRecord:** `includes`/`preload` for N+1, `exists?` for presence, `find_each` for batches
- **Security:** Strong params, no `html_safe`, scoped queries, encrypted credentials
- **I18n:** Model layer only (`activerecord.attributes.*`, `activerecord.errors.*`). Plain text in views.
- **Auth:** Use auth helper (`current_user`), protect with before_action, roles via model methods

---

## Rules (auto-loaded by file path)

Rules are loaded automatically when you work with matching files.

| When you edit... | Rules loaded |
|---|---|
| Any `.rb` file | ruby-rails-conventions |
| Any `.rb` file (Rails app emitting logs) | observability |
| `spec/` | rspec-testing |
| `app/views/`, `app/components/`, `app/helpers/` | ui-ux |

For project context, read `.claude/rules/project-overview.md` first.

---

## Available Skills

| Skill | Description |
|---|---|
| `/code-review` | Structured code review against project checklist |
| `/write-tests` | Generate RSpec tests for a class |
| `/rails-conventions-reference` | On-demand worked examples for the conventions + optional patterns (value/query/form objects, validators, concerns) |
| `/rspec-reference` | On-demand worked RSpec examples |
| `/ui-ux-reference` | On-demand worked view-layer examples |

> The `ruby-rails-conventions`, `rspec-testing`, and `ui-ux` rules are the lean always-apply
> versions; their worked examples live in the matching `*-reference` skills (loaded on
> demand). The Rails code-review checklist now lives in the `code-review` skill.

---

## Prohibited Actions

- Do NOT run `rails server`, `touch tmp/restart.txt`, `rails credentials`
- Do NOT auto-run migrations — show the file, let the developer run it
- Do NOT write tests or documentation unless explicitly asked
- Do NOT modify project rules without asking first
- Do NOT run RuboCop or RSpec automatically — the developer runs them manually
- Do NOT commit to git unless explicitly requested
