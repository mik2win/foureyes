
# Project Overview

> **Fill in this template** when adding rules to a new project. Replace placeholders with actual project details.

## What Is This Project

<!-- Describe the project in 2-3 sentences: what it does, who uses it, what problem it solves -->
[PROJECT_NAME] — ...

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Ruby on Rails [VERSION] |
| Database | PostgreSQL [VERSION] |
| Authentication | [Devise / has_secure_password / etc.] |
| Frontend | Hotwire (Turbo + Stimulus) |
| Styles | TailwindCSS |
| Views | [Slim / ERB] |
| Background jobs | [Solid Queue (Rails 8 default) / Sidekiq + Redis / GoodJob] |
| Testing | RSpec, FactoryBot, Shoulda Matchers |
| Components | ViewComponent |
| Linting | [rubocop-rails-omakase / Standard] |
| Other | [list additional gems] |

## Domain Entities

<!-- List the core models and their relationships.
     For each entity, describe:
     - What it represents
     - Key attributes and their meaning
     - Enums with values: enum role: { user: 0, admin: 1 }
     - Important associations (belongs_to, has_many)
     - Business rules specific to this entity
     - Data filters (e.g. "only records with status IN ('active', 'pending') are shown") -->

### User
<!-- Example:
     Authenticated account. Has role: user or admin.
     - Admin: can manage records, users, settings
     - User: can view reports, interact with own records -->

### [EntityName]
...

### [EntityName]
...

## Key Business Rules

<!-- Describe the critical business logic. The AI needs this to make correct architectural and code decisions.
     Examples:
     - Calculation formulas and algorithms
     - Access control / authorization matrix
     - Data validation rules beyond simple presence/format
     - Workflow states and transitions
     - Integration points with external systems -->

1. ...
2. ...

## Key Algorithms

<!-- If the project has non-trivial calculations or data processing, describe the algorithm here.
     Include:
     - Input data and sources
     - Step-by-step calculation logic
     - Output format
     - Edge cases and special handling -->

## Architecture Notes

<!-- Non-obvious architectural decisions:
     - Custom directory structure (e.g. app/services/ module organization)
     - Strategy/policy objects and their purpose
     - External service integrations
     - Caching strategy
     - Background job orchestration
     - Data flow for critical features -->

## API / Integrations

<!-- If applicable:
     - External APIs consumed (with endpoints and auth method)
     - APIs exposed (with versioning strategy)
     - Webhook handlers
     - File import/export formats -->

## UI / Report Structure

<!-- If applicable:
     - Key pages and their purpose
     - Report fields with labels (useful for the AI to understand domain vocabulary)
     - Dashboard structure -->

## Team Context

- Number of developers: [1-3 / 3-10 / 10+]
- Project maturity: [MVP / growing / mature / legacy]
- Key constraints: [deadline, compliance, performance, etc.]
